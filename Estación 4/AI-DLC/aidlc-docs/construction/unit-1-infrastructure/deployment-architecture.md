# Deployment Architecture — Unit 1: Infraestructura

**Propósito**: Traducir ADRs y NFRs en diagrama detallado de cómo los servicios se despliegan, comunican y escalan en AWS. Incluye topología de red, security group rules, data flow, y failover paths.

---

## 1. TOPOLOGÍA DE RED (Network Topology)

### Estructura de VPC

```
AWS Region: us-south-1 (São Paulo)
├── VPC: 10.0.0.0/16 (ticketdesk-vpc)
│
├── AVAILABILITY ZONE: us-south-1a
│   ├── Public Subnet: 10.0.1.0/24
│   │   ├── NAT Gateway (Elastic IP: xxx)
│   │   └── ALB (Target: ECS tasks in private subnets)
│   │
│   ├── Private Subnet: 10.0.10.0/24
│   │   ├── ECS tasks (backend:8000, frontend:3000)
│   │   ├── RDS primary (port 5432)
│   │   └── ElastiCache (port 6379)
│   │
│   └── Database Subnet: 10.0.20.0/24
│       └── RDS primary instance
│
├── AVAILABILITY ZONE: us-south-1b
│   ├── Public Subnet: 10.0.2.0/24
│   │   ├── NAT Gateway (Elastic IP: yyy)
│   │   └── ALB (redundant listener)
│   │
│   ├── Private Subnet: 10.0.11.0/24
│   │   ├── ECS tasks (backend:8000, frontend:3000)
│   │   ├── RDS replica (read-only)
│   │   └── ElastiCache replica (read-only)
│   │
│   └── Database Subnet: 10.0.21.0/24
│       └── RDS replica instance (standby)
│
├── Internet Gateway (igw-xxxxx)
│   ├── Inbound: HTTP (80) → ALB
│   └── Inbound: HTTPS (443) → ALB
│
├── NAT Gateways (2x, one per AZ)
│   ├── us-south-1a NAT: Outbound traffic from private subnet 10.0.10.0/24
│   └── us-south-1b NAT: Outbound traffic from private subnet 10.0.11.0/24
│
└── Route Tables
    ├── Public (10.0.1.0/24, 10.0.2.0/24)
    │   └── Default route (0.0.0.0/0) → Internet Gateway
    │
    └── Private (10.0.10.0/24, 10.0.11.0/24)
        └── Default route (0.0.0.0/0) → NAT Gateway (same AZ)
```

### Rutas de Tráfico

```
Entrada (Internet → Application):
  Internet → ALB (port 443, TLS) → Security Group ALB-SG
           → Route 10.0.1.0/24 (public subnet)
           → Health check: /health (ECS tasks)
           → Load balance → ECS-SG
           → Route 10.0.10.0/24, 10.0.11.0/24 (private subnets)
           → FastAPI (port 8000) / Next.js (port 3000)

Salida (Application → External):
  ECS tasks → Claude API (HTTPS)
           → Security Group ECS-SG allows ephemeral ports to 0.0.0.0/0
           → NAT Gateway (port 443 outbound)
           → Internet (NatGateway translates source IP)

Base de Datos (Application → Database):
  ECS tasks → RDS endpoint (ticketdesk-prod.xxxxx.us-south-1.rds.amazonaws.com:5432)
           → Security Group ECS-SG
           → Security Group RDS-SG (allows 5432 only from ECS-SG)
           → Primary RDS (sync replication to replica)

Cache (Application → Redis):
  ECS tasks → ElastiCache endpoint (ticketdesk-redis.xxxxx.cache.us-south-1.rds.amazonaws.com:6379)
           → Security Group ECS-SG
           → Security Group Redis-SG (allows 6379 only from ECS-SG)
           → Primary Redis (no replication in v1.0)
```

---

## 2. SECURITY GROUPS & FIREWALL RULES

### Diagrama de SG Rules

```
┌─────────────────────────────────────────────────────────┐
│                     INTERNET (0.0.0.0/0)                │
└────────────────────────────┬────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   ALB-SG        │
                    │ (sg-alb-xxxxx)  │
                    │ Inbound:        │
                    │ - 80 (HTTP)     │
                    │ - 443 (HTTPS)   │
                    │ Outbound:       │
                    │ - all to ECS-SG │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   ECS-SG        │
                    │ (sg-ecs-xxxxx)  │
                    │ Inbound:        │
                    │ - 8000 ALB-SG   │
                    │ - 3000 ALB-SG   │
                    │ Outbound:       │
                    │ - all to RDS-SG │
                    │ - all to Redis  │
                    │ - 443 to 0.0.0.0│
                    │ - 53 to 0.0.0.0 │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼───┐          ┌──────▼──────┐      ┌────▼────┐
    │RDS-SG │          │ Redis-SG    │      │ S3      │
    │(sg-db)│          │ (sg-cache)  │      │(bucket) │
    │Inbound│          │ Inbound:    │      │ Private │
    │5432   │          │ - 6379      │      │ access  │
    │from   │          │   from ECS  │      │ only    │
    │ECS-SG │          │ Outbound:   │      └─────────┘
    │       │          │ - none      │
    └───────┘          └─────────────┘
```

### Security Group Rules (Tabular)

| SG | Direction | Port/Protocol | Source/Dest | Purpose |
|-----|-----------|---|---|---|
| ALB-SG | Inbound | 80/TCP | 0.0.0.0/0 | HTTP redirect |
| ALB-SG | Inbound | 443/TCP | 0.0.0.0/0 | HTTPS (TLS) |
| ALB-SG | Outbound | 8000/TCP | ECS-SG | Backend |
| ALB-SG | Outbound | 3000/TCP | ECS-SG | Frontend |
| ECS-SG | Inbound | 8000/TCP | ALB-SG | Backend API |
| ECS-SG | Inbound | 3000/TCP | ALB-SG | Frontend |
| ECS-SG | Outbound | 5432/TCP | RDS-SG | PostgreSQL |
| ECS-SG | Outbound | 6379/TCP | Redis-SG | Cache |
| ECS-SG | Outbound | 443/TCP | 0.0.0.0/0 | HTTPS (Claude, Docker Hub) |
| ECS-SG | Outbound | 53/UDP | 0.0.0.0/0 | DNS |
| RDS-SG | Inbound | 5432/TCP | ECS-SG | PostgreSQL |
| RDS-SG | Outbound | - | - | None (no egress) |
| Redis-SG | Inbound | 6379/TCP | ECS-SG | Cache |
| Redis-SG | Outbound | - | - | None (no egress) |

---

## 3. ARQUITECTURA DE COMPUTE (ECS Deployment)

### ECS Cluster Topology

```
┌─────────────────────────────────────────────────────┐
│              ECS Cluster: ticketdesk-prod           │
│           (Capacity Providers: AUTOSCALING)         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  ECS Service: backend (FastAPI)              │  │
│  │  ├─ Desired count: 2 (min), 10 (max)         │  │
│  │  ├─ Auto-scaling: CPU > 70% → +1 task       │  │
│  │  ├─ Task definition: backend:latest          │  │
│  │  └─ Port mapping: 8000 → ALB                 │  │
│  │                                              │  │
│  │  Task 1 (us-south-1a)       Task 2 (us-south-1b) │
│  │  ├─ Image: backend:v1.0     ├─ Image: backend:v1.0 │
│  │  ├─ CPU: 512 (units)        ├─ CPU: 512         │
│  │  ├─ Memory: 1024 MB         ├─ Memory: 1024 MB  │
│  │  ├─ Port: 8000              ├─ Port: 8000       │
│  │  └─ Env: RDS_URL, REDIS_URL └─ Env: RDS_URL, ... │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  ECS Service: frontend (Next.js)             │  │
│  │  ├─ Desired count: 2 (min), 10 (max)         │  │
│  │  ├─ Auto-scaling: CPU > 70% → +1 task       │  │
│  │  ├─ Task definition: frontend:latest         │  │
│  │  └─ Port mapping: 3000 → ALB                 │  │
│  │                                              │  │
│  │  Task 1 (us-south-1a)       Task 2 (us-south-1b) │
│  │  ├─ Image: frontend:v1.0    ├─ Image: frontend:v1.0 │
│  │  ├─ CPU: 256 (units)        ├─ CPU: 256         │
│  │  ├─ Memory: 512 MB          ├─ Memory: 512 MB   │
│  │  ├─ Port: 3000              ├─ Port: 3000       │
│  │  └─ Env: NEXT_PUBLIC_API_URL └─ Env: NEXT_... │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### ECS Task Definition (JSON structure)

```json
{
  "family": "ticketdesk-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["EC2"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "XXX.dkr.ecr.us-south-1.amazonaws.com/ticketdesk-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@ticketdesk-prod.xxxxx.us-south-1.rds.amazonaws.com:5432/ticketdesk"
        },
        {
          "name": "REDIS_URL",
          "value": "rediss://user:pass@ticketdesk-redis.xxxxx.cache.us-south-1.amazonaws.com:6379"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/aws/ecs/ticketdesk/backend",
          "awslogs-region": "us-south-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ],
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole"
}
```

---

## 4. ARQUITECTURA DE DATOS (Data Storage & Replication)

### Replicación de Datos

```
PRIMARY (us-south-1a)          REPLICA (us-south-1b)
┌──────────────────────┐      ┌──────────────────────┐
│ RDS PostgreSQL       │      │ RDS PostgreSQL       │
│ - Primary instance   │      │ - Standby replica    │
│ - Accepts writes     │  ←→  │ - Read-only          │
│ - 9 tables, 100 GB   │      │ - Sync replicated    │
│ - Backups daily      │      │ - For failover       │
└──────────────────────┘      └──────────────────────┘
         │                              │
         └─────────────────────────────┘
                  ↓
        S3: Automated snapshots
        - 30-day retention
        - Cross-region backup (monthly)

PRIMARY (us-south-1a)          STANDBY (us-south-1b)
┌──────────────────────┐      ┌──────────────────────┐
│ ElastiCache Redis    │      │ ElastiCache Redis    │
│ - Primary node       │  ←→  │ - Replica (v1.1)     │
│ - Cluster mode OFF   │      │ - Current: single    │
│ - Session cache      │      │ - Future: sentinel   │
│ - Rubric cache       │      │ - Automatic failover │
└──────────────────────┘      └──────────────────────┘

S3 Buckets (auto geo-replicated by AWS)
┌──────────────────────────────────────────────────────┐
│ ticketdesk-transcriptions (versioning enabled)      │
│ ticketdesk-audit-logs (7-year retention)            │
│ ticketdesk-knowledge-base (backup & archive)        │
└──────────────────────────────────────────────────────┘
```

### Failover Flow

```
NORMAL STATE:
  ECS Tasks → RDS Primary (us-south-1a) ✓
           → Redis Primary (us-south-1a) ✓

PRIMARY FAILS (us-south-1a goes down):
  [t=0s] Connection timeout to RDS primary
  [t=0-30s] ECS circuit breaker detects failures
  [t=30-60s] AWS detects RDS primary unhealthy (health checks fail)
  [t=60-120s] Automatic RDS failover:
              - Replica in us-south-1b promoted to primary
              - DNS endpoint updated (same endpoint, new IP)
  [t=120s+] ECS connection pool retries
           → RDS Primary (new, was replica) ✓
           → Redis Primary (still us-south-1a replica in v1.0)

POST-RECOVERY:
  [t=0-30min] AWS provisions new replica in us-south-1a
  [t=30min+] Sync replication restored
             Multi-AZ status: healthy ✓
```

---

## 5. CI/CD PIPELINE (Deployment Flow)

### GitHub Actions Workflow

```
Developer:
  git push origin feature/xxx

         ↓ (webhook trigger)

GitHub Actions:
  ┌─────────────────────────────────────────┐
  │ Job 1: Test Backend                    │
  │ ├─ run: pytest (>80% coverage)         │
  │ ├─ run: black --check                  │
  │ ├─ run: pylint                         │
  │ └─ run: mypy                           │
  │ Status: ✓ PASS / ✗ FAIL                │
  └─────────────────────────────────────────┘
                ↓
  ┌─────────────────────────────────────────┐
  │ Job 2: Test Frontend                    │
  │ ├─ run: npm test (>80% coverage)       │
  │ ├─ run: eslint                         │
  │ ├─ run: prettier --check               │
  │ └─ run: tsc --noEmit                   │
  │ Status: ✓ PASS / ✗ FAIL                │
  └─────────────────────────────────────────┘
                ↓
  ┌─────────────────────────────────────────┐
  │ Job 3: Build Docker Images              │
  │ ├─ docker build -t backend:${SHA}      │
  │ ├─ docker push ECR/backend:${SHA}      │
  │ ├─ docker build -t frontend:${SHA}     │
  │ ├─ docker push ECR/frontend:${SHA}     │
  │ ├─ Image scan (security check)         │
  │ └─ Status: ✓ PUSH / ✗ FAIL             │
  └─────────────────────────────────────────┘
                ↓
  ┌─────────────────────────────────────────┐
  │ Job 4: Deploy to Staging (automatic)   │
  │ ├─ Update ECS task definition          │
  │ ├─ Deploy to staging cluster           │
  │ ├─ Run smoke tests (health checks)     │
  │ └─ Status: ✓ DEPLOYED / ✗ FAIL        │
  └─────────────────────────────────────────┘
                ↓
  ┌─────────────────────────────────────────┐
  │ Job 5: Manual Approval Required         │
  │ ├─ Approver reviews staging env        │
  │ ├─ Runs integration tests              │
  │ ├─ Approves or rejects deployment      │
  │ └─ Status: ⏳ PENDING APPROVAL         │
  └─────────────────────────────────────────┘
                ↓
  ┌─────────────────────────────────────────┐
  │ Job 6: Deploy to Production (manual)   │
  │ ├─ Blue-green deployment:              │
  │ │  - "Blue" tasks (old version)        │
  │ │  - "Green" tasks (new version)       │
  │ ├─ Health checks for green tasks       │
  │ ├─ Monitor health for 5 minutes        │
  │ ├─ If healthy: shift traffic to green │
  │ ├─ If fails: revert to blue            │
  │ └─ Status: ✓ LIVE / ✗ ROLLBACK       │
  └─────────────────────────────────────────┘

GitHub Merge:
  ✓ Merge to main (branch protection: all checks pass)
  ✓ Tag: v1.0.123 (semantic versioning)
  ✓ Close feature branch
```

---

## 6. OBSERVABILIDAD & MONITORING

### CloudWatch Dashboards

```
┌───────────────────────────────────────────────────┐
│       TicketDesk-Infrastructure Dashboard         │
├───────────────────────────────────────────────────┤
│                                                   │
│ ┌─────────────────────┬───────────────────────┐  │
│ │ ECS Service Status  │ ALB Target Health     │  │
│ │ • Desired: 2        │ • Healthy: 2/2        │  │
│ │ • Running: 2        │ • Unhealthy: 0        │  │
│ │ • Pending: 0        │ • Pending: 0          │  │
│ └─────────────────────┴───────────────────────┘  │
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ CPU Utilization (5 min avg)                 │ │
│ │ 80% ┤                          ┌──────────┐ │ │
│ │ 60% ┤   ┌─────────────────────┘          └─┤ │
│ │ 40% ┤───┘                                   │ │
│ │      └──────────────────────────────────────┤ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ RDS Database Connections                    │ │
│ │ 20 │       ┌──────────────────┐             │ │
│ │ 15 │       │ Current: 12 conn │             │ │
│ │ 10 ├───────┘                  └───┬─────────┤ │
│ │  5 │                              │         │ │
│ │    └──────────────────────────────┴─────────┤ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ ALB Response Time (p99)                     │ │
│ │ 2.0s ┤                                       │ │
│ │ 1.5s ┤                    ┌──────────────┐  │ │
│ │ 1.0s ┤    ┌───────────────┘              └──┤ │
│ │ 0.5s ├────┘                                 │ │
│ │ 0.0s └──────────────────────────────────────┤ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
│ ┌─────────────────────┬───────────────────────┐  │
│ │ Redis Cache Stats   │ Error Rate (5min)     │  │
│ │ • Hits: 15,234      │ • 4xx: 12 reqs        │  │
│ │ • Misses: 2,456     │ • 5xx: 0 reqs         │  │
│ │ • Hit rate: 86%     │ • Rate: 0.02%         │  │
│ └─────────────────────┴───────────────────────┘  │
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ RDS Multi-AZ Status                         │ │
│ │ • Primary: us-south-1a ✓                    │ │
│ │ • Replica: us-south-1b ✓                    │ │
│ │ • Replication lag: 0 ms ✓                   │ │
│ │ • Last failover: 2026-05-20                 │ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
└───────────────────────────────────────────────────┘
```

### Alarms (SNS Notifications)

| Alarm | Metric | Threshold | Action |
|-------|--------|-----------|--------|
| RDS CPU High | CPU % | > 80% | Email + Slack |
| ECS Tasks Down | DesiredCount | < 2 | Page on-call |
| ALB Latency | Response time p99 | > 2s | Email |
| Cache Hit Rate | Hit % | < 85% | Email |
| Error Rate Spike | 5xx errors | > 1% | Email |
| Cost Alert | Monthly spend | > $220 | Email |

---

## 7. DISASTER RECOVERY (DR Strategy)

### Recovery Point Objective (RPO)

```
Data Loss Scenario:
┌────────────────────────────────────────────┐
│ RDS Primary Fails (data corruption)        │
│ RPO: < 1 minute (sync replication)         │
│                                            │
│ Current state: Replica in sync             │
│ → Promote replica (new primary)            │
│ → Zero data loss ✓                         │
│ → Max lag: 0 ms (sync)                    │
└────────────────────────────────────────────┘

S3 Data Loss Scenario:
┌────────────────────────────────────────────┐
│ S3 Accidental Delete                       │
│ RPO: 30 days (backup retention)            │
│ → Versioning enabled                       │
│ → Restore from previous version ✓          │
└────────────────────────────────────────────┘

Audit Log Data Loss Scenario:
┌────────────────────────────────────────────┐
│ RDS Audit Logs Deleted                     │
│ RPO: 7 years (S3 archive)                  │
│ → Cross-region S3 backup                   │
│ → Restore from S3 Glacier ✓                │
└────────────────────────────────────────────┘
```

### Recovery Time Objective (RTO)

```
RDS Primary Failure:
  [t=0] Failure detected (health check fails)
  [t=30-60s] AWS RDS detects unhealthy
  [t=60-120s] Automatic failover
  [t=120s] Replica promoted, DNS updated
  [t=120-180s] ECS reconnects
  → RTO: 2-3 minutes ✓

ECS Task Failure:
  [t=0] Task health check fails (3 consecutive)
  [t=30s] ALB marks target unhealthy
  [t=30-60s] ECS launches replacement task
  [t=60-90s] New task passes health checks
  → RTO: 90 seconds ✓

ALB Failure:
  [t=0] ALB becomes unavailable (rare)
  [t=5min] AWS automatically restarts
  → RTO: 5 minutes
  Mitigated by Route53 health checks + failover

Full Region Failure (us-south-1):
  [t=0] Region down
  → Manual intervention: restore from backup to different region
  → RTO: 30+ minutes
  Mitigated by: S3 versioning, RDS snapshots, multi-region roadmap (v2.0)
```

---

**Artefacto para**: Unit 1 - Infraestructura  
**Fecha**: 2026-05-27  
**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction - Estación 5, Actividad 3

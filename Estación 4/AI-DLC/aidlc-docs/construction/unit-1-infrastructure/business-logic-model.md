# Business Logic Model — Unit 1: Infraestructura

## Flujo: Provisioning Inicial de AWS (Day 0)

### Descripción
Desde cero, provisionamiento completo de stack AWS usando Terraform/CloudFormation. Crea VPC, subnets, RDS, Redis, ECS cluster, ALB, S3, ECR, CI/CD pipeline, monitoreo. Al final, health checks pasan en todos los servicios.

**Duración**: 1-2 semanas (depende de aprobaciones AWS)  
**Actores**: DevOps Engineer, Cloud Architect (review)  
**Entrada**: Terraform/CloudFormation templates (versionados)  
**Salida**: AWS stack production-ready, CICD pipeline activo, health checks green

### Pasos

1. **Crear VPC con subnets multi-AZ**
   - Terraform: `aws_vpc` (CIDR 10.0.0.0/16)
   - Crear 2 subnets públicas (10.0.1.0/24 us-south-1a, 10.0.2.0/24 us-south-1b)
   - Crear 2 subnets privadas (10.0.10.0/24, 10.0.11.0/24)
   - Aplicar: `terraform apply`
   - Validar: `terraform state` muestra 1 VPC + 4 subnets ✓

2. **Configurar Internet Gateway + NAT Gateway**
   - Internet Gateway: attach a VPC (ingress desde internet)
   - NAT Gateway: create en subnet pública (egress desde privadas hacia internet)
   - Route tables:
     - Público: 0.0.0.0/0 → Internet Gateway
     - Privado: 0.0.0.0/0 → NAT Gateway
   - Validar: `curl internet-gateway` → 200 OK ✓

3. **Crear Security Groups (4 grupos)**
   - ALB SG: Allows 80 (HTTP), 443 (HTTPS) from 0.0.0.0/0
   - ECS SG: Allows 8000 (backend), 3000 (frontend) from ALB SG only
   - RDS SG: Allows 5432 from ECS SG only (no 0.0.0.0/0!)
   - Redis SG: Allows 6379 from ECS SG only
   - Audit: `aws ec2 describe-security-groups` confirms rules ✓

4. **Provisionar RDS PostgreSQL Multi-AZ**
   - Instance class: db.t3.small
   - Allocated storage: 100 GB
   - Multi-AZ: true (replica en us-south-1b)
   - Encryption: KMS key
   - Backup retention: 30 days
   - Subnet group: privadas (no internet access)
   - Validar:
     - `psql -h rds-endpoint -U postgres -c "SELECT 1"` → success ✓
     - RDS console: Multi-AZ status = "Yes" ✓

5. **Provisionar ElastiCache Redis**
   - Node type: cache.t3.micro
   - Encryption: at rest (KMS) + in transit (TLS)
   - maxmemory_policy: allkeys-lru
   - Subnet group: privadas
   - Auth token: generated, stored in Secrets Manager
   - Validar:
     - `redis-cli -h redis-endpoint ping` → PONG ✓
     - `redis-cli info memory` → used_memory, max_memory ✓

6. **Crear S3 buckets (3 buckets)**
   - ticketdesk-transcriptions: versioning, KMS encryption, lifecycle (90d → Glacier)
   - ticketdesk-audit-logs: versioning, KMS, lifecycle (7y retention)
   - ticketdesk-knowledge-base: versioning, KMS
   - Public access: BlockPublicAcls, BlockPublicPolicy ✓
   - Validar: `aws s3 ls` → 3 buckets ✓

7. **Crear ECR repositories (2 repos)**
   - ticketdesk-backend: FastAPI image
   - ticketdesk-frontend: Next.js image
   - Scan on push: enabled
   - Lifecycle: keep last 10 images
   - Validar: `aws ecr describe-repositories` → 2 repos ✓

8. **Provisionar ECS Cluster + ALB**
   - ECS cluster: "ticketdesk-prod"
   - Capacity providers: AUTOSCALING (EC2) + FARGATE
   - ALB: listeners en 80 (HTTP → HTTPS redirect), 443 (HTTPS)
   - Target groups: backend (port 8000), frontend (port 3000)
   - TLS certificate: ACM (auto-renewed)
   - Health checks: /health every 30s
   - Validar:
     - ALB DNS resolvable ✓
     - HTTPS certificate valid ✓
     - Health check endpoint responds 200 ✓

9. **Crear CloudWatch Log Groups + Alarms**
   - Log groups: /aws/ecs/ticketdesk/{backend,frontend}, /aws/rds, /aws/lambda
   - Retention: 30 days
   - Metric filters: ErrorCount, LatencyP99, CPUUtilization
   - Alarms:
     - RDS CPU > 80% → SNS
     - ECS tasks < 2 → SNS
     - ALB latency p99 > 2s → SNS
   - SNS topic: critical-alerts → email suscriptions
   - Validar: `aws logs describe-log-groups` → all groups exist ✓

10. **Configurar GitHub Actions CI/CD Pipeline**
    - Secrets: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, GITHUB_TOKEN, ECR_REGISTRY
    - Workflow triggers: on push to main, PR to main
    - Jobs:
      - test-backend: pytest (>80% coverage)
      - test-frontend: jest (>80% coverage)
      - build-docker: docker build, push to ECR
      - deploy-staging: ECS deploy (green task) → health check → confirm
      - deploy-production: manual approval + ECS deploy (blue-green)
    - Rollback: if health check fails, revert to previous task definition
    - Validar: GitHub Actions logs show all jobs passing ✓

### Reglas Aplicadas
- RULE-INFRA-01: VPC multi-AZ ✓
- RULE-INFRA-02: Encryption at rest (KMS) ✓
- RULE-INFRA-03: TLS 1.3 en ALB ✓
- RULE-INFRA-04: Secrets en AWS Secrets Manager ✓
- RULE-INFRA-05: Security groups least privilege ✓
- RULE-INFRA-06: NAT Gateway para egreso ✓
- RULE-DB-01: RDS Multi-AZ failover ✓
- RULE-DB-02: Connection pooling ✓
- RULE-DB-03: Password rotation 90d ✓
- RULE-DB-04: Backups 30d retention ✓
- RULE-CACHE-01: Redis LRU eviction ✓
- RULE-ECS-01: Auto-scaling 2-10 tasks ✓
- RULE-ECS-02: Health checks 30s ✓
- RULE-ECS-03: Blue-green deployment ✓
- RULE-ECS-04: CloudWatch logs ✓
- RULE-S3-01: Public access block ✓
- RULE-S3-02: Versioning ✓
- RULE-S3-03: Lifecycle 90d/7y ✓
- RULE-MONITOR-01: Alarms → SNS ✓

### Estados Posibles (State Machine)

```
Initial (terraform code)
  ↓ (terraform apply)
VPC_CREATED
  ↓ (IGW + NAT created)
NETWORKING_CONFIGURED
  ↓ (SGs created)
SECURITY_GROUPS_CONFIGURED
  ↓ (RDS provisioning)
RDS_PROVISIONING
  ↓ (RDS available + backup enabled)
RDS_READY
  ↓ (Redis provisioning)
REDIS_PROVISIONING
  ↓ (Redis cluster available)
REDIS_READY
  ↓ (ECS cluster + ALB)
ECS_ALB_PROVISIONING
  ↓ (ALB health checks passing)
ECS_ALB_READY
  ↓ (CICD pipeline deployed)
CICD_READY
  ↓ (All health checks green)
PRODUCTION_READY ✅
```

### Decisiones Clave
- **Región**: us-south-1 (São Paulo) para LGPD compliance
- **Database engine**: PostgreSQL 14+ (open source, reliable)
- **Cache engine**: Redis 7+ (fast, supports pub/sub)
- **Orchestration**: ECS (simpler than k8s for monolith)
- **IaC**: Terraform (version controlled, reproducible)

---

## Flujo: Crear Local Development Environment (Day 0.5)

### Descripción
Mientras AWS se provisiona (1-2 semanas), desarrolladores necesitan stack local. Docker Compose con PostgreSQL, Redis, localstack (simular S3/SQS), mock AWS services.

**Duración**: 2-4 horas setup  
**Actores**: Backend/Frontend developers  
**Entrada**: docker-compose.yml  
**Salida**: `docker-compose up -d` trae stack completo, developers pueden empezar Unit 2

### Pasos

1. **Clone repositorio + Docker Compose**
   ```bash
   git clone https://github.com/ticketdesk/enterprise
   cd ticketdesk
   docker-compose up -d
   ```
   Espera 30-60 segundos por servicios.

2. **Verificar servicios locales**
   ```bash
   curl http://localhost:8000/health  # FastAPI backend
   curl http://localhost:3000/api/health  # Next.js frontend
   psql -h localhost -U postgres -d ticketdesk -c "SELECT 1"  # PostgreSQL
   redis-cli -h localhost ping  # Redis
   ```

3. **Ejecutar migrations (alembic)**
   ```bash
   cd backend
   alembic upgrade head  # Create 9 tables
   ```

4. **Seed initial data**
   ```bash
   python scripts/seed.py  # Create test campaign, test users, test rubric
   ```

5. **Verificar frontend**
   ```bash
   cd ../frontend
   npm install
   npm run dev  # Should start on port 3000
   ```

### Estados
- DOCKER_COMPOSE_RUNNING → SERVICES_HEALTHY → DB_MIGRATED → READY_FOR_DEVELOPMENT

---

## Flujo: Monitoreo en Producción (Ongoing)

### Descripción
Después de deployment a production, sistema monitorea salud continuamente. Alertas se disparan si algo anormal.

### Pasos

1. **Health checks cada 30s**
   - ALB: GET /health → 200 OK
   - Si falla 3 veces → task replacement

2. **Métricas en CloudWatch cada minuto**
   - CPU utilization, memory, disk I/O
   - RDS connections, replication lag
   - Redis memory, eviction rate
   - ALB target response time, HTTP errors

3. **Si CPU > 70%**
   - Scale up: +1 task (max 10)

4. **Si CPU < 30% para 10 minutos**
   - Scale down: -1 task (min 2)

5. **Si latency p99 > 2s**
   - Alert to Slack (dev team)
   - Auto-investigation: check DB queries, cache hit rate, external APIs

6. **Diario: automated backup verification**
   - RDS: verify latest backup exists
   - If missing → alert to DBA team

### Estados
- NORMAL (all green) ↔ DEGRADED (some alerts) ↔ CRITICAL (multiple failures) ↔ RECOVERY

---

## Flujo: Disaster Recovery - RDS Failover (Edge Case)

### Descripción
Si primaria RDS falla, multi-AZ replica automáticamente promueve.

### Pasos

1. **RDS primary becomes unavailable**
   - Application gets connection timeout
   - Retry logic backs off (exponential)

2. **Failover automático inicia (AWS)**
   - Replica en us-south-1b promueve a primaria (1-2 minutos)
   - DNS endpoint sigue siendo válido (AWS re-points)

3. **Application reconnects**
   - Connection pool reintentos
   - Traffic restaurado
   - CloudWatch logs "RDS failover completed"

4. **Post-recovery**
   - AWS crea nuevo replica en us-south-1a
   - Monitoreo confirma "Multi-AZ healthy"
   - Email a DBA: "RDS failover occurred at 14:32 UTC"

### Estados
- PRIMARY_ACTIVE → PRIMARY_FAILURE → FAILOVER_IN_PROGRESS → REPLICA_PROMOTED → RECOVERY_IN_PROGRESS → PRIMARY_ACTIVE (new)

---

## Matriz de Estados de Infraestructura

| Estado | VPC | RDS | Redis | ECS | ALB | Implicación |
|--------|-----|-----|-------|-----|-----|-------------|
| INITIALIZING | ✅ | ⏳ | ⏳ | ❌ | ❌ | Provisioning in progress |
| DEGRADED | ✅ | ✅ | ⏳ | ✅ | ✅ | Redis down, cache unavailable |
| CRITICAL | ✅ | ❌ | ✅ | ⚠️ | ✅ | RDS down, DB access failed |
| HEALTHY | ✅ | ✅ | ✅ | ✅ | ✅ | Production ready, SLA met |

---

**Artefacto para**: Unit 1 - Infraestructura  
**Fecha**: 2026-05-27  
**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction - Estación 5, Actividad 1

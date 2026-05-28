# Diseño de Infraestructura — TicketDesk Enterprise v1.0

**Configuración AWS, Terraform, CI/CD Pipeline, Networking**  
**Fecha**: 2026-05-27  
**Fase**: Inception - Infrastructure Design  
**Estado**: En Desarrollo

---

## 1. ARQUITECTURA AWS

### 1.1 Región y Disponibilidad

```yaml
Región Seleccionada: us-south-1 (São Paulo, Brasil)
  ├─ Compliance: LGPD (Lei Geral de Proteção de Dados)
  ├─ Data residency: Todos datos hosted en Brasil
  ├─ Latency: <10ms para usuarios en São Paulo
  └─ Cost: Moderado (regional pricing)

Availability Zones:
  ├─ us-south-1a (Primary)
  │  ├─ Public subnet A: 10.0.1.0/24
  │  ├─ Private subnet A: 10.0.11.0/24
  │  └─ Resources: ALB, ECS tasks, RDS Primary
  │
  └─ us-south-1b (Secondary)
     ├─ Public subnet B: 10.0.2.0/24
     ├─ Private subnet B: 10.0.12.0/24
     └─ Resources: ECS tasks, RDS Standby (Multi-AZ)
```

### 1.2 VPC & Networking

```yaml
VPC Configuration:
  ├─ CIDR: 10.0.0.0/16
  ├─ DNS: enabled
  ├─ DNS hostnames: enabled
  └─ Flow logs: enabled (CloudWatch Logs) for debugging

Subnets:

  Public Subnets (DMZ):
    ├─ Public subnet A: 10.0.1.0/24 (us-south-1a)
    │  ├─ Route table: IGW (Internet Gateway)
    │  ├─ NAT Gateway: Allocated
    │  └─ Resources: ALB
    │
    └─ Public subnet B: 10.0.2.0/24 (us-south-1b)
       ├─ Route table: IGW
       ├─ NAT Gateway: Allocated (HA)
       └─ Resources: ALB (secondary)

  Private Subnets (Application):
    ├─ Private subnet A: 10.0.11.0/24 (us-south-1a)
    │  ├─ Route table: NAT Gateway A (for outbound internet)
    │  └─ Resources: ECS tasks, RDS
    │
    └─ Private subnet B: 10.0.12.0/24 (us-south-1b)
       ├─ Route table: NAT Gateway B (for HA)
       └─ Resources: ECS tasks, RDS Standby

Route Tables:

  Public Route Table (attached to public subnets):
    ├─ Destination: 0.0.0.0/0 → Target: IGW (Internet Gateway)
    └─ LOCAL: 10.0.0.0/16 → Local VPC

  Private Route Table A (attached to private subnet A):
    ├─ Destination: 0.0.0.0/0 → Target: NAT Gateway A
    └─ LOCAL: 10.0.0.0/16 → Local VPC

  Private Route Table B (attached to private subnet B):
    ├─ Destination: 0.0.0.0/0 → Target: NAT Gateway B
    └─ LOCAL: 10.0.0.0/16 → Local VPC

Internet Gateway (IGW):
  ├─ Attached to VPC
  ├─ Provides route from public subnets to internet
  └─ Enables inbound traffic (ALB)

NAT Gateways:
  ├─ NAT Gateway A (in public subnet A)
  │  ├─ Elastic IP: Allocated
  │  └─ Used by private subnet A for outbound traffic
  │
  └─ NAT Gateway B (in public subnet B)
     ├─ Elastic IP: Allocated
     └─ Used by private subnet B for outbound traffic (HA)
```

### 1.3 Security Groups

```yaml
ALB-SG (Application Load Balancer Security Group):
  ├─ Inbound:
  │  ├─ Port 80 (HTTP): 0.0.0.0/0 (all) [redirect to 443]
  │  ├─ Port 443 (HTTPS): 0.0.0.0/0 (all)
  │  └─ Port 3000 (Next.js health): 0.0.0.0/0
  │
  ├─ Outbound:
  │  └─ All traffic to ECS-SG (port 8000, 3000)
  │
  └─ Tags: {Name: "ticketdesk-alb-sg"}

ECS-SG (ECS Tasks Security Group):
  ├─ Inbound:
  │  ├─ Port 8000 (FastAPI): From ALB-SG only
  │  ├─ Port 3000 (Next.js): From ALB-SG only
  │  └─ Port 22 (SSH): From ops-jumpbox-sg only (bastion host)
  │
  ├─ Outbound:
  │  ├─ Port 443: To 0.0.0.0/0 (HTTPS for external APIs)
  │  ├─ Port 5432: To RDS-SG (PostgreSQL)
  │  ├─ Port 6379: To Redis-SG (Redis)
  │  └─ Port 25/587: To 0.0.0.0/0 (AWS SES email)
  │
  └─ Tags: {Name: "ticketdesk-ecs-sg"}

RDS-SG (PostgreSQL Security Group):
  ├─ Inbound:
  │  ├─ Port 5432 (PostgreSQL): From ECS-SG only
  │  └─ Port 5432: From ops-jumpbox-sg (for manual admin access)
  │
  ├─ Outbound:
  │  └─ None (database doesn't initiate outbound)
  │
  └─ Tags: {Name: "ticketdesk-rds-sg"}

Redis-SG (ElastiCache Security Group):
  ├─ Inbound:
  │  ├─ Port 6379 (Redis): From ECS-SG only
  │  └─ Port 6379: From ops-jumpbox-sg (redis-cli access)
  │
  ├─ Outbound:
  │  └─ None (Redis doesn't initiate outbound)
  │
  └─ Tags: {Name: "ticketdesk-redis-sg"}

Ops-Jumpbox-SG (Bastion Host):
  ├─ Inbound:
  │  ├─ Port 22 (SSH): From 0.0.0.0/0 (or restricted IPs)
  │  └─ Ideally: whitelist office IPs only
  │
  ├─ Outbound:
  │  ├─ Port 22: To ECS-SG (SSH to ECS instance)
  │  ├─ Port 5432: To RDS-SG (psql)
  │  ├─ Port 6379: To Redis-SG (redis-cli)
  │  └─ Port 443: To 0.0.0.0/0 (for AWS CLI, etc.)
  │
  └─ Tags: {Name: "ticketdesk-jumpbox-sg"}
```

---

## 2. COMPUTE

### 2.1 Application Load Balancer (ALB)

```yaml
Load Balancer Configuration:
  ├─ Type: Application Load Balancer (Layer 7)
  ├─ Name: ticketdesk-alb
  ├─ Scheme: internet-facing (public)
  ├─ IP Address Type: IPv4
  ├─ Subnets: us-south-1a (public), us-south-1b (public)
  ├─ Security groups: ALB-SG
  └─ Tags: {Name: "ticketdesk-alb"}

Listeners:

  HTTP Listener (Port 80):
    ├─ Protocol: HTTP
    ├─ Port: 80
    ├─ Action: Redirect to HTTPS
    │  ├─ Protocol: HTTPS
    │  ├─ Port: 443
    │  ├─ Status code: 301 (Permanent Redirect)
    │  └─ Preserve path: true
    └─ No target groups

  HTTPS Listener (Port 443):
    ├─ Protocol: HTTPS
    ├─ Port: 443
    ├─ SSL Certificate: ACM (arn:aws:acm:...)
    │  ├─ Domain: *.ticketdesk.com (wildcard)
    │  ├─ Renewal: Auto-renewed by AWS
    │  └─ Validation: DNS CNAME in Route53
    │
    └─ Rules:
       ├─ Rule 1 (Backend):
       │  ├─ Host header: api.ticketdesk.com
       │  └─ Forward to: backend-target-group
       │
       └─ Rule 2 (Frontend):
          ├─ Host header: app.ticketdesk.com (or no condition = default)
          └─ Forward to: frontend-target-group

Target Groups:

  backend-target-group:
    ├─ Name: ticketdesk-backend-tg
    ├─ Protocol: HTTP
    ├─ Port: 8000 (FastAPI internal port)
    ├─ VPC: ticketdesk-vpc
    ├─ Health check:
    │  ├─ Protocol: HTTP
    │  ├─ Path: /health
    │  ├─ Port: 8000
    │  ├─ Interval: 30s
    │  ├─ Timeout: 5s
    │  ├─ Healthy threshold: 2 (2 consecutive successes)
    │  ├─ Unhealthy threshold: 3 (3 consecutive failures)
    │  └─ Matcher: 200 (expects HTTP 200)
    │
    ├─ Stickiness: disabled (stateless API)
    └─ Targets: Registered by ECS service (auto-registered)

  frontend-target-group:
    ├─ Name: ticketdesk-frontend-tg
    ├─ Protocol: HTTP
    ├─ Port: 3000 (Next.js internal port)
    ├─ VPC: ticketdesk-vpc
    ├─ Health check:
    │  ├─ Protocol: HTTP
    │  ├─ Path: /api/health (Next.js health endpoint)
    │  ├─ Interval: 30s
    │  └─ Matcher: 200
    │
    └─ Targets: Registered by ECS service
```

### 2.2 ECS (Elastic Container Service)

```yaml
ECS Cluster:
  ├─ Name: ticketdesk-prod
  ├─ Launch type: EC2 (NOT Fargate, for cost optimization)
  ├─ Container Insights: Enabled (CloudWatch monitoring)
  └─ Default capacity provider: EC2

EC2 Auto Scaling Group (for cluster capacity):
  ├─ Name: ticketdesk-ecs-asg
  ├─ Launch template:
  │  ├─ AMI: ECS-optimized (Amazon Linux 2)
  │  ├─ Instance type: t3.medium (2 vCPU, 4 GB RAM)
  │  ├─ Key pair: ticketdesk-kp (for SSH access)
  │  ├─ IAM role: ecsInstanceRole (allows EC2 to pull images from ECR, etc.)
  │  ├─ Security group: ECS-SG
  │  └─ Monitoring: Detailed CloudWatch metrics
  │
  ├─ Desired capacity: 2 (start)
  ├─ Min capacity: 2 (always running)
  ├─ Max capacity: 6 (scaling up during peak)
  ├─ Availability zones: us-south-1a, us-south-1b (spread across AZs)
  ├─ VPC subnets: Private subnet A, Private subnet B
  └─ Health check:
     ├─ Type: ELB
     ├─ Grace period: 300s (5 min for instance to boot)
     └─ Unhealthy: Replace instance

Task Definition (Backend):
  ├─ Name: ticketdesk-backend
  ├─ Revision: 1
  ├─ Network mode: awsvpc (ENI-based networking)
  ├─ CPU: 512
  ├─ Memory: 1024 (MB)
  ├─ Logging: awslogs (CloudWatch)
  │  ├─ Log group: /ecs/ticketdesk-backend
  │  ├─ Log stream: ticketdesk-backend-{task_id}
  │  └─ Region: us-south-1
  │
  ├─ Container definitions:
  │  └─ fastapi-container:
  │     ├─ Image: {ECR_URI}/ticketdesk-backend:latest
  │     ├─ Port mappings:
  │     │  ├─ Container port: 8000
  │     │  ├─ Host port: 0 (dynamic port allocation)
  │     │  └─ Protocol: tcp
  │     │
  │     ├─ Environment variables:
  │     │  ├─ ENVIRONMENT: production
  │     │  ├─ LOG_LEVEL: info
  │     │  ├─ WORKERS: 4
  │     │  ├─ DATABASE_URL: postgresql://app_user:password@rds-endpoint:5432/ticketdesk_prod
  │     │  ├─ REDIS_URL: redis://redis-endpoint:6379
  │     │  ├─ AWS_REGION: us-south-1
  │     │  └─ CLAUDE_API_KEY: (from AWS Secrets Manager, injected at runtime)
  │     │
  │     ├─ Secrets (from AWS Secrets Manager):
  │     │  ├─ DATABASE_PASSWORD
  │     │  ├─ REDIS_PASSWORD
  │     │  ├─ JWT_SECRET
  │     │  └─ CLAUDE_API_KEY
  │     │
  │     ├─ Log configuration:
  │     │  ├─ Log driver: awslogs
  │     │  ├─ Options:
  │     │  │  ├─ awslogs-group: /ecs/ticketdesk-backend
  │     │  │  ├─ awslogs-region: us-south-1
  │     │  │  └─ awslogs-stream-prefix: ecs
  │     │
  │     ├─ Health check:
  │     │  ├─ Command: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  │     │  ├─ Interval: 30s
  │     │  ├─ Timeout: 5s
  │     │  ├─ Retries: 3
  │     │  └─ Start period: 60s
  │     │
  │     └─ Resource limits:
  │        ├─ CPU: 512 (relative units)
  │        └─ Memory: 900 (MB, leave 124 for OS)

Task Definition (Frontend):
  ├─ Name: ticketdesk-frontend
  ├─ CPU: 256
  ├─ Memory: 512
  ├─ Container: next-js-container
  │  ├─ Image: {ECR_URI}/ticketdesk-frontend:latest
  │  ├─ Port: 3000
  │  ├─ Environment:
  │  │  ├─ NEXT_PUBLIC_API_URL: https://api.ticketdesk.com
  │  │  └─ NODE_ENV: production
  │  │
  │  └─ Health check:
  │     └─ Command: ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"]

ECS Services:

  backend-service:
    ├─ Name: ticketdesk-backend-service
    ├─ Cluster: ticketdesk-prod
    ├─ Task definition: ticketdesk-backend:1
    ├─ Launch type: EC2
    ├─ Desired count: 2 (running tasks)
    ├─ Deployment configuration:
    │  ├─ Min healthy percent: 100 (maintain 2 tasks)
    │  ├─ Max percent: 200 (allow 4 tasks during update)
    │  └─ Deployment type: Rolling (no downtime)
    │
    ├─ Load balancing:
    │  ├─ Target group: backend-target-group
    │  ├─ Container name: fastapi-container
    │  ├─ Container port: 8000
    │  └─ Health check grace period: 60s
    │
    ├─ Auto Scaling:
    │  ├─ Min tasks: 2
    │  ├─ Max tasks: 8
    │  ├─ Scale up policy: IF CPU > 70% → +1 task
    │  ├─ Scale down policy: IF CPU < 30% → -1 task
    │  └─ Cooldown: 60s
    │
    └─ Networking:
       ├─ Subnets: Private subnet A, Private subnet B
       ├─ Security groups: ECS-SG
       └─ Assign public IP: false (internal only)

  frontend-service:
    ├─ Name: ticketdesk-frontend-service
    ├─ Similar configuration to backend-service
    ├─ Task definition: ticketdesk-frontend:1
    ├─ Desired count: 2
    └─ Auto Scaling: Min 2, Max 6 tasks
```

---

## 3. DATABASE & CACHE

### 3.1 PostgreSQL RDS

```yaml
RDS Database:
  ├─ DB Engine: PostgreSQL 15.3
  ├─ DB Instance Identifier: ticketdesk-prod
  ├─ Instance class: db.t3.small (2 vCPU, 2 GB RAM)
  ├─ Storage:
  │  ├─ Storage type: gp3 (General Purpose)
  │  ├─ Allocated storage: 100 GB (start)
  │  ├─ Max allocated storage: 200 GB (auto-scale)
  │  ├─ Encryption: enabled (KMS customer-managed key)
  │  └─ Backup storage: encrypted
  │
  ├─ Availability:
  │  ├─ Multi-AZ: enabled
  │  ├─ Primary: us-south-1a
  │  ├─ Standby: us-south-1b (synchronous replication)
  │  └─ Failover: automatic (takes ~2 min)
  │
  ├─ Backup:
  │  ├─ Backup retention: 30 días
  │  ├─ Backup window: 02:00-03:00 UTC (low traffic)
  │  ├─ Copy backups to another region: false (v2.0 feature)
  │  └─ Backup encryption: enabled
  │
  ├─ Database:
  │  ├─ Database name: ticketdesk_prod
  │  ├─ Port: 5432
  │  └─ Character set: UTF8
  │
  ├─ Database Users:
  │  ├─ Master user: postgres (admin, never use in app)
  │  │  └─ Password: 32-char random (stored in AWS Secrets Manager)
  │  │
  │  ├─ app_user (application READ/WRITE):
  │  │  ├─ Password: 32-char random
  │  │  └─ Permissions: SELECT, INSERT, UPDATE, DELETE on app tables
  │  │
  │  ├─ readonly_user (analytics, reporting):
  │  │  ├─ Password: 32-char random
  │  │  └─ Permissions: SELECT only
  │  │
  │  └─ backup_user (for snapshots):
  │     └─ Permissions: SELECT on all tables
  │
  ├─ Parameter Group: custom-ticketdesk-pg15
  │  ├─ max_connections: 200 (scaled for app + read replicas)
  │  ├─ shared_buffers: 524288 (2GB for t3.small)
  │  ├─ work_mem: 5242880 (5MB per operation)
  │  ├─ maintenance_work_mem: 52428800 (50MB)
  │  ├─ effective_cache_size: 1572864 (6GB, 3x RAM estimate)
  │  ├─ random_page_cost: 1.1 (SSD storage)
  │  ├─ log_statement: 'all' (for query audit)
  │  └─ log_duration: on (log query time)
  │
  ├─ Option Group: default.postgres15
  └─ Enhanced Monitoring:
     ├─ Enabled: yes
     ├─ Granularity: 60 seconds
     └─ IAM role: rds-monitoring-role

Connectivity:
  ├─ VPC: ticketdesk-vpc
  ├─ DB subnet group: ticketdesk-db-subnet-group (private subnets A+B)
  ├─ Security group: RDS-SG (port 5432 from ECS-SG)
  ├─ Publicly accessible: false (private DB)
  └─ DNS endpoint: ticketdesk-prod.xxxxx.us-south-1.rds.amazonaws.com

Read Replicas (Future v1.1):
  ├─ Replica 1: us-south-1b (same region, different AZ)
  │  └─ Use case: Distribute read queries
  │
  └─ Replica 2: us-east-1 (different region, optional)
     └─ Use case: Geographic redundancy + read scaling
```

### 3.2 ElastiCache Redis

```yaml
Redis Cluster:
  ├─ Engine: Redis 7.0
  ├─ Cache node type: cache.t3.micro (0.5 GB, MVP)
  ├─ Number of cache nodes: 1 (single node)
  ├─ Automatic failover: disabled (single node)
  ├─ Engine version: 7.0 (latest compatible)
  └─ Tags: {Name: "ticketdesk-redis"}

Parameter Group: custom-ticketdesk-redis
  ├─ maxmemory-policy: allkeys-lru (evict LRU keys when memory full)
  ├─ timeout: 300 (close idle connections after 5 min)
  ├─ tcp-keepalive: 300 (keep connections alive)
  ├─ requirepass: required (set password)
  └─ masterauth: (password for replication, future)

Subnet Group: ticketdesk-redis-subnet-group
  ├─ VPC: ticketdesk-vpc
  └─ Subnets: Private subnet A, Private subnet B (even though single node)

Security:
  ├─ Security group: Redis-SG (port 6379 from ECS-SG)
  ├─ Publicly accessible: false
  ├─ Authorization token: 32-char random (Redis password)
  │  └─ Stored in AWS Secrets Manager
  │
  ├─ Encryption in transit:
  │  ├─ Protocol: TLS (optional, add overhead)
  │  └─ Currently: plaintext (acceptable within VPC, no public access)
  │
  └─ Encryption at rest: enabled (AWS managed)

Monitoring:
  ├─ CloudWatch metrics: enabled
  ├─ Metrics:
  │  ├─ CPU utilization
  │  ├─ Memory usage
  │  ├─ Evictions (# keys evicted due to memory pressure)
  │  ├─ Connection count
  │  └─ Network bytes in/out
  │
  └─ Alarms:
     ├─ CPU > 80%
     ├─ Memory evictions > 1000/min
     └─ Connection count > 400

Persistence (Optional):
  ├─ RDB Snapshots: Via Celery task (not ElastiCache RDB, manual approach)
  │  ├─ Frequency: Every 5 min
  │  ├─ Script: BGSAVE + copy to S3
  │  └─ Recovery: Load RDB on Redis restart
  │
  └─ AOF (Append-only file): disabled (performance cost)
```

---

## 4. ALMACENAMIENTO

### 4.1 S3 Buckets

```yaml
Bucket 1: ticketdesk-transcriptions
  ├─ Purpose: Store candidate screening transcriptions
  ├─ Versioning: enabled
  ├─ Server-side encryption: SSE-S3 (AES-256)
  ├─ Bucket policy:
  │  ├─ Allow ECS tasks to PutObject, GetObject
  │  ├─ Deny public access (Block Public Access: ON)
  │  └─ Deny unencrypted uploads
  │
  ├─ Lifecycle policy:
  │  ├─ Transition to GLACIER after 90 días
  │  ├─ Delete old versions after 30 días
  │  └─ Delete incomplete multipart uploads after 7 días
  │
  ├─ Object structure:
  │  └─ s3://ticketdesk-transcriptions/{campaign_id}/{session_id}/transcript.json
  │
  └─ Estimated size: ~10 KB per transcription × 100K/year = 1 GB/year

Bucket 2: ticketdesk-knowledge-base
  ├─ Purpose: Store knowledge base documents for RAG
  ├─ Versioning: enabled
  ├─ Encryption: SSE-S3
  ├─ Bucket policy:
  │  ├─ Allow ECS to PutObject, GetObject
  │  └─ Allow presigned URLs for recruiter download
  │
  ├─ Lifecycle policy:
  │  └─ Keep all versions (no expiration, useful for KB versioning)
  │
  ├─ Object structure:
  │  └─ s3://ticketdesk-knowledge-base/{campaign_id}/{doc_id}/content.txt
  │
  └─ Estimated size: ~50 KB × 500 docs = 25 MB (small, grows with campaigns)

Bucket 3: ticketdesk-compliance-reports
  ├─ Purpose: Store generated compliance PDF reports
  ├─ Versioning: enabled
  ├─ Encryption: SSE-KMS (customer-managed key for compliance)
  ├─ Bucket policy:
  │  ├─ Allow ECS to PutObject
  │  ├─ Allow only HTTPS uploads
  │  └─ Require server-side encryption
  │
  ├─ Lifecycle policy:
  │  ├─ Keep all versions indefinitely (compliance retention: 7 años)
  │  └─ Transition to Glacier (or Glacier Deep Archive) after 2 años (cost optimization)
  │
  ├─ Object structure:
  │  └─ s3://ticketdesk-compliance-reports/{campaign_id}/{date}/report.pdf
  │
  └─ Estimated size: ~100 KB per report × 365/year = 36 MB/year

Bucket 4: ticketdesk-redis-backups (optional)
  ├─ Purpose: Store Redis RDB snapshots for recovery
  ├─ Versioning: enabled
  ├─ Encryption: SSE-S3
  ├─ Lifecycle policy:
  │  ├─ Keep last 7 días (rolling window)
  │  └─ Delete older snapshots automatically
  │
  ├─ Object structure:
  │  └─ s3://ticketdesk-redis-backups/redis-{timestamp}.rdb
  │
  └─ Estimated size: ~50 MB × 288 snapshots/day = 14.4 GB (manageable)
```

---

## 5. CI/CD PIPELINE

### 5.1 GitHub Actions Workflow (Backend)

```yaml
Name: Backend CI/CD
File: .github/workflows/backend.yml

Trigger:
  - push to any branch
  - pull_request to main/develop

Jobs:

  Test:
    runs-on: ubuntu-latest
    steps:
      1. Checkout code
      2. Setup Python 3.11
      3. Cache pip dependencies
      4. Install dependencies: pip install -r requirements.txt
      5. Run linting: pylint src/ tests/ --fail-under=8.0
      6. Run type checking: mypy src/ --strict
      7. Run tests: pytest tests/ --cov=src --cov-fail-under=80
      8. Upload coverage to CodeCov (optional)
      9. On failure: Comment PR with error details

  Build:
    runs-on: ubuntu-latest
    needs: Test
    if: Test.result == 'success'
    steps:
      1. Checkout code
      2. Login to AWS ECR:
         - aws ecr get-login-password --region ${{ env.AWS_REGION }}
         - docker login -u AWS -p {password} {ECR_URL}
      3. Build Docker image:
         - docker build -t {ECR_URL}/ticketdesk-backend:latest .
         - docker tag {ECR_URL}/ticketdesk-backend:latest {ECR_URL}/ticketdesk-backend:{COMMIT_SHA}
      4. Push to ECR:
         - docker push {ECR_URL}/ticketdesk-backend:latest
         - docker push {ECR_URL}/ticketdesk-backend:{COMMIT_SHA}
      5. Output image URI to next job

  Deploy-Staging:
    runs-on: ubuntu-latest
    needs: Build
    if: github.ref == 'refs/heads/develop'
    steps:
      1. Configure AWS credentials
      2. Update ECS task definition:
         - Fetch current task definition
         - Update image URI to new version
         - Register new task definition revision
      3. Update ECS service (staging):
         - aws ecs update-service --cluster ticketdesk-staging --service backend --task-definition new-revision
      4. Wait for deployment to complete:
         - aws ecs wait services-stable
      5. Run smoke tests (staging):
         - curl https://api-staging.ticketdesk.com/health
         - curl https://api-staging.ticketdesk.com/api/screening (should 401 without token)
      6. Slack notification: Deploy successful/failed

  Deploy-Production:
    runs-on: ubuntu-latest
    needs: Build
    if: github.ref == 'refs/heads/main' && github.event == 'push'
    steps:
      1. Manual approval required (optional, implemented via branch protection)
      2. Configure AWS credentials
      3. Update ECS task definition
      4. Update ECS service (production):
         - aws ecs update-service --cluster ticketdesk-prod --service backend
      5. Monitor deployment (CloudWatch):
         - Check task health (wait for new tasks to pass health checks)
         - Monitor error rate in CloudWatch (should not exceed 5%)
         - Timeout: 10 min
      6. Automatic rollback on failure:
         - IF deployment fails: Revert to previous task definition
         - Notification: PagerDuty alert
      7. Slack notification with deployment details
```

### 5.2 GitHub Actions Workflow (Frontend)

```yaml
Name: Frontend CI/CD
File: .github/workflows/frontend.yml

Trigger: push/PR (same as backend)

Jobs:

  Test:
    runs-on: ubuntu-latest
    steps:
      1. Checkout code
      2. Setup Node.js 18
      3. Cache node_modules
      4. Install: npm ci (clean install)
      5. Linting: npm run lint (ESLint)
      6. Type checking: npm run type-check (TypeScript)
      7. Unit tests: npm test (Jest, excluding integration tests)
      8. Coverage requirement: >80%
      9. Build: npm run build (next build)
      10. Test build succeeds (verify no build errors)

  Build:
    runs-on: ubuntu-latest
    needs: Test
    steps:
      1. Checkout code
      2. Setup Node.js
      3. Install dependencies
      4. Build Next.js app: npm run build && npm run export
      5. Build Docker image (multi-stage):
         - Stage 1: Build (node:18-alpine)
           - npm ci
           - npm run build
         - Stage 2: Runtime (node:18-alpine)
           - Copy from builder (.next/, public/, package.json)
           - CMD: next start (or custom server.js)
      6. Push to ECR: docker push {ECR_URL}/ticketdesk-frontend:latest

  Deploy-Staging & Deploy-Production:
    (Similar to backend, update ECS service for frontend)
```

### 5.3 Deployment Safety

```yaml
Branch Protection Rules (main):
  ├─ Require PR review: 1 approval
  ├─ Require CI/CD status: all checks pass
  ├─ Require up-to-date branches: before merge
  ├─ Dismiss reviews on push: enabled (re-review on changes)
  └─ Allow force pushes: disabled (prevent accidental overwrites)

Staging Environment:
  ├─ Auto-deployed on every push to develop branch
  ├─ Acts as pre-production test environment
  ├─ Smoke tests run automatically after deployment
  ├─ Stability target: 99% uptime (acceptable for staging)
  └─ Data: Sanitized copy of production (anonymized)

Production Environment:
  ├─ Manual trigger required (OR auto on merge to main)
  ├─ Deployment strategy: Rolling update (no downtime)
  │  ├─ Min healthy: 100%
  │  ├─ Max: 200% (allow 4 tasks while deploying 2)
  │  └─ Gradually replace old tasks with new
  │
  ├─ Automatic rollback:
  │  ├─ If new tasks fail health checks: automatic rollback
  │  ├─ If error rate > 10%: manual intervention (ops must approve rollback)
  │  └─ Rollback action: Restore previous task definition
  │
  └─ Notifications:
     ├─ Deployment start: Slack + PagerDuty
     ├─ Deployment complete: Slack
     └─ Deployment failure: PagerDuty critical alert
```

---

## 6. MONITOREO Y LOGGING

### 6.1 CloudWatch

```yaml
Log Groups:
  ├─ /ecs/ticketdesk-backend
  │  └─ Log streams: backend-{container_id}
  │     ├─ Application logs (DEBUG, INFO, WARNING, ERROR)
  │     ├─ Request logs (method, path, status, latency)
  │     └─ Retention: 30 días
  │
  ├─ /ecs/ticketdesk-frontend
  │  └─ Log streams: frontend-{container_id}
  │     └─ Retention: 14 días (less verbose)
  │
  ├─ /aws/rds/instance/ticketdesk-prod/error
  │  └─ PostgreSQL errors: 7 días retention
  │
  ├─ /aws/rds/instance/ticketdesk-prod/slowquery
  │  └─ Queries > 1000ms: 3 días retention
  │
  └─ /aws/lambda/ticketdesk-* (if using Lambda for tasks)

CloudWatch Metrics:
  ├─ ECS Cluster:
  │  ├─ CPU utilization (% of cluster)
  │  ├─ Memory utilization (%)
  │  ├─ Running tasks count
  │  ├─ Pending tasks count (if high = capacity issue)
  │  └─ Service deployment status
  │
  ├─ ALB:
  │  ├─ Request count (requests/min)
  │  ├─ Target response time (p50, p99)
  │  ├─ HTTP 4xx count
  │  ├─ HTTP 5xx count
  │  └─ Unhealthy host count
  │
  ├─ RDS:
  │  ├─ CPU utilization
  │  ├─ Database connections
  │  ├─ Storage space available
  │  ├─ Read/Write latency
  │  ├─ Read/Write IOPS
  │  └─ Replica lag (if read replicas)
  │
  ├─ Redis:
  │  ├─ CPU utilization
  │  ├─ Memory usage (bytes)
  │  ├─ Evictions (# keys evicted/min)
  │  ├─ Connection count
  │  └─ Network bandwidth
  │
  └─ Application (custom):
     ├─ Request latency (p50, p95, p99)
     ├─ Request error rate (5xx, 4xx)
     ├─ Queue depth (pending jobs)
     ├─ Cache hit ratio (%)
     └─ Claude API latency + errors

CloudWatch Alarms:

  Critical (PagerDuty page):
    ├─ RDS CPU > 90% for 5 min
    ├─ RDS storage < 10% available
    ├─ RDS unavailable (failover)
    ├─ ALB unhealthy targets > 0 for 2 min
    ├─ API error rate (5xx) > 5%
    ├─ Claude API error rate > 10%
    └─ Redis memory evictions > 1000/min

  Warning (Slack notification):
    ├─ ECS CPU > 75%
    ├─ API latency p99 > 3s
    ├─ Queue depth > 1000
    ├─ Cache hit ratio < 80%
    └─ Celery dead-letter queue > 0
```

---

## 7. SECRETS MANAGEMENT

### 7.1 AWS Secrets Manager

```yaml
Secrets Stored:
  ├─ ticketdesk/database/password
  │  └─ Value: PostgreSQL app_user password (32-char random)
  │
  ├─ ticketdesk/redis/password
  │  └─ Value: Redis auth token (32-char random)
  │
  ├─ ticketdesk/jwt/secret
  │  └─ Value: JWT signing secret (64-char random)
  │
  ├─ ticketdesk/claude/api-key
  │  └─ Value: Claude API key from Anthropic
  │
  ├─ ticketdesk/aws/s3-kms-key
  │  └─ Value: KMS key ID for S3 encryption (ARN)
  │
  └─ ticketdesk/smtp/credentials
     ├─ Username: AWS SES SMTP user
     └─ Password: AWS SES SMTP password

Rotation Policy:
  ├─ Database password: Quarterly (manual in MVP)
  ├─ Redis password: Quarterly
  ├─ JWT secret: Annually (keep old for grace period)
  ├─ API keys (Claude): On demand (if key compromised)
  └─ Monitoring: Alert if secret not rotated > 180 días

Access Control (IAM):
  ├─ ECS task role can read: database/password, redis/password, jwt/secret, claude/api-key
  ├─ CI/CD role can read: All secrets (for injection)
  ├─ Admin role can rotate: All secrets
  └─ Audit trail: CloudTrail logs all secret access
```

---

**Estado**: 🔄 Infrastructure Design En Progreso  
**Siguiente**: Final consolidation + handoff to Construction phase


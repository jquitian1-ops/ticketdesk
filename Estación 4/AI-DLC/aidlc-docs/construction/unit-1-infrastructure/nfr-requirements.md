# NFR Requirements — Unit 1: Infraestructura

**Propósito**: Especificar cómo se miden y validan los requerimientos no funcionales de infraestructura. Estos son "hechos observables" que deben cumplirse en producción.

---

## 1. DISPONIBILIDAD (Availability)

### Requerimiento
**SLA**: 99.5% uptime anual (máximo 3.7 horas downtime/año)  
**RTO** (Recovery Time Objective): < 2 minutos  
**RPO** (Recovery Point Objective): < 1 minuto (sync replication)

### Cómo se mide

#### 1.1 Uptime Monitoring
- **Métrica**: (Total time - Downtime) / Total time
- **Tool**: CloudWatch synthetic monitoring + third-party uptime service (Pingdom/UptimeRobot)
- **Measurement**:
  - Health check endpoint: `GET /health` every 30 seconds
  - If 3 consecutive checks fail → incident
  - Calculate: uptime% = (seconds up / total seconds) × 100
  
#### 1.2 Downtime Events
- **Critical downtime**: Any of these components down:
  - RDS primary (no failover to replica)
  - ALB completely unavailable
  - ECS cluster < 2 healthy tasks
  - VPC/networking issues
- **Partial degradation**: Single AZ down, but traffic fails over to other AZ (acceptable)

#### 1.3 Alert on SLA Breach
- **Monthly SLA tracking**: CloudWatch dashboard
- **If monthly uptime < 99.5%**: Automatic alert to DevOps team by day 25 of month
- **Root cause analysis**: Post-incident review within 24 hours

#### 1.4 Acceptance Criteria
```
Dado que sistema está en producción
Cuando se monitorea por 30 días consecutivos
Entonces:
  ✓ Uptime ≥ 99.5% (≤ 10.8 minutos downtime)
  ✓ RDS failover occurs < 2 min
  ✓ No requests dropped during failover
  ✓ ALB target count never < 2 simultaneously
```

### Validation
- Daily: Check CloudWatch dashboard for uptime% (target >99.5%)
- Weekly: Automated failover test (simulated RDS failure) → verify auto-recovery
- Monthly: SLA report generated automatically
- Annually: Disaster recovery drill (full stack restore from backups)

---

## 2. SEGURIDAD (Security)

### Requerimiento
**Encryption at rest**: All data encrypted with KMS  
**Encryption in transit**: All traffic TLS 1.3  
**Authentication**: JWT (HS256)  
**LGPD Compliance**: Data retention, audit logs, consent  
**No public DB access**: Security groups prevent 0.0.0.0/0 to RDS/Redis

### Cómo se mide

#### 2.1 Encryption Verification
- **At rest**: 
  - RDS: `aws rds describe-db-instances | grep StorageEncrypted` = true
  - Redis: `aws elasticache describe-replication-groups | grep AtRestEncryptionEnabled` = true
  - S3: `aws s3api get-bucket-encryption` returns KMS key ID
  - EBS: All volumes have `Encrypted: true`
  
- **In transit**:
  - ALB listeners: `Protocol: HTTPS` (port 443 only)
  - TLS version: `aws elbv2 describe-ssl-policies` → minimum TLS 1.3
  - Certificate: Valid ACM certificate, auto-renewed

#### 2.2 Security Group Audit
- **Script**: `aws ec2 describe-security-groups --query SecurityGroups[*].IpPermissions`
- **Validation**:
  - RDS SG: No rule with `CidrIp: 0.0.0.0/0` or `Ipv6CidrIp: ::/0`
  - Redis SG: No rule with `CidrIp: 0.0.0.0/0`
  - ALB SG: Only allows 80 (HTTP→HTTPS) and 443 (HTTPS)
  - ECS SG: Allows traffic only from ALB SG

#### 2.3 Secrets Manager Audit
- **Database password**: Stored in Secrets Manager, not in code
- **JWT secret**: Stored in Secrets Manager
- **API keys** (Claude, GitHub): In Secrets Manager
- **Script**: 
  ```bash
  grep -r "aws_secret_access_key\|password\|api_key" app/ 2>/dev/null | grep -v "\.pyc"
  # Should return 0 matches (no secrets in code)
  ```

#### 2.4 LGPD Compliance Checks
- **Consent logging**: 
  - Every screening start logged with explicit consent
  - `consent_records` table populated for every candidate
  
- **Audit logs immutability**:
  - `audit_logs` table has constraint: INSERT only, no UPDATE/DELETE
  - Test: Attempt DELETE → fails with constraint error
  
- **Data retention**:
  - Personal data deleted after 90 days (soft-delete)
  - Hard-delete job runs nightly
  - Audit logs retained 7 years
  
- **Right to erasure**:
  - `/api/candidate/{id}/erase` endpoint responds
  - POST request cascades deletes personal data
  - Audit log created for erasure request

#### 2.5 Acceptance Criteria
```
Dado que sistema está en producción
Cuando auditor ejecuta security checklist
Entonces:
  ✓ 100% datos encriptados con KMS
  ✓ TLS 1.3 en todas las conexiones
  ✓ 0 secrets en código
  ✓ 0 public access a RDS/Redis
  ✓ Consent logged para todo candidate
  ✓ Audit logs immutable (INSERT-only)
  ✓ Data retention policies funcionan (90d soft, 7y audit)
```

### Validation
- Weekly: `aws ec2 describe-security-groups` audit
- Weekly: `grep secrets` in codebase
- Monthly: LGPD compliance report (consent %, data retention %, audit logs size)
- Quarterly: Penetration testing (external security firm)

---

## 3. PERFORMANCE (Latency & Throughput)

### Requerimiento
**Endpoint latency**: p99 < 2 seconds  
**Chat response time**: < 1 second (BotEngine response)  
**API throughput**: 100 requests/second (load test baseline)  
**Cache hit rate**: > 85%  
**Frontend bundle**: < 100 KB gzipped

### Cómo se mide

#### 3.1 Endpoint Latency
- **Metric**: ALB target response time (CloudWatch)
- **Baseline**:
  - GET /health: p99 < 100ms
  - POST /screening/start: p99 < 500ms (BD + Redis setup)
  - POST /screening/{id}/response: p99 < 1s (Claude API call or queue)
  - GET /recruiter/queue: p99 < 800ms (DB query + cache)
  
- **Measurement**:
  ```
  CloudWatch metric: TargetResponseTime
  Statistic: p99
  Period: 5 minutes
  Alert if: p99 > 2000ms (for any endpoint)
  ```

#### 3.2 Chat Response Time
- **Metric**: Time from POST /screening/{id}/response to response.status = 200
- **Target**: p99 < 1 second
- **Components**:
  - Request parsing: < 100ms
  - Jailbreak detection: < 200ms
  - Database insert: < 100ms
  - Event emit: < 100ms (async, not blocking)
- **Measurement**: 
  - Log request.start_time, response.end_time
  - Calculate: latency = end_time - start_time
  - Group by percentile (p50, p95, p99)

#### 3.3 Throughput
- **Load test baseline**:
  ```
  ab -n 10000 -c 100 https://api.ticketdesk.com/health
  Requests per second: 500+ (baseline)
  ```
  
- **Production monitoring**:
  - ALB RequestCount metric
  - Normal: 50-100 req/s (2 ECS tasks, each handles 25-50 req/s)
  - Peak: 100-150 req/s (auto-scale triggers)

#### 3.4 Cache Hit Rate
- **Metric**: Redis cache hits vs misses
- **Target**: > 85%
- **Components**:
  - Session cache (24h TTL): should have >95% hit rate
  - Rubric cache (7d TTL): should have >80% hit rate
  - Overall: > 85%
  
- **Measurement**:
  ```bash
  redis-cli INFO stats | grep keyspace_hits, keyspace_misses
  hit_rate = hits / (hits + misses)
  alert if hit_rate < 0.85
  ```

#### 3.5 Frontend Bundle
- **Metric**: Next.js bundle size (gzipped)
- **Target**: < 100 KB
- **Measurement**:
  ```bash
  npm run build
  gzip dist/pages/_app.js
  du -h _app.js.gz  # Should be < 100KB
  ```
- **Alert**: If bundle > 120KB (10% margin)

#### 3.6 Acceptance Criteria
```
Dado que sistema está en producción
Cuando se ejecutan load tests durante 1 hora
Entonces:
  ✓ p99 latency < 2s (para endpoints principales)
  ✓ Chat response < 1s (p99)
  ✓ Throughput > 100 req/s sustained
  ✓ Cache hit rate > 85%
  ✓ Frontend bundle < 100KB gzipped
  ✓ p95 latency < 1.5s
  ✓ p50 latency < 500ms
```

### Validation
- Continuous: CloudWatch latency graphs (5-minute periods)
- Daily: Cache hit rate report (target >85%)
- Weekly: Load test (1000 concurrent users, 1 hour)
- Monthly: Frontend bundle size audit
- Before every deployment: Performance baseline test

---

## 4. ESCALABILIDAD (Scalability)

### Requerimiento
**Auto-scaling**: 2-10 ECS tasks based on CPU  
**Multi-AZ**: Minimum 2 AZs, failover < 2 min  
**Horizontal scaling**: Can add more ECS instances without code changes  
**Database read replicas**: v1.1 roadmap (for now: single primary)

### Cómo se mide

#### 4.1 Auto-Scaling Verification
- **Metric**: ECS DesiredCount and RunningCount
- **Target scaling**:
  - CPU > 70% → +1 task (up to 10 total)
  - CPU < 30% (for 10 min) → -1 task (down to 2 minimum)
  
- **Measurement**:
  ```
  CloudWatch metric: ECS Service DesiredCount
  Alert if DesiredCount < 2 (health issue)
  Alert if DesiredCount > 10 (cost control)
  ```

#### 4.2 Load Test Scaling
- **Test scenario**:
  ```
  Start: 2 tasks (baseline)
  Load: Ramp to 500 req/s
  Expected: Auto-scale to 5-8 tasks
  Verify: p99 latency stays < 2s
  Verify: No requests dropped
  ```

#### 4.3 Multi-AZ Failover
- **Test scenario**:
  ```
  Simulate: ALB target in us-south-1a becomes unhealthy
  Expected: Traffic reroutes to us-south-1b within 30s
  Verify: 0 requests dropped
  Verify: Health check fails < 3 times before reroute
  ```

#### 4.4 Acceptance Criteria
```
Dado que sistema está bajo carga
Cuando CPU sube a 75%
Entonces:
  ✓ New task inicia < 60s
  ✓ Task pasa health check
  ✓ Traffic redirigida sin drop
  ✓ p99 latency stays < 2s

Dado que CPU baja a 25%
Cuando pasan 15 minutos
Entonces:
  ✓ Task se termina
  ✓ Remaining tasks soportan carga
  ✓ No latency spike
  ✓ Min 2 tasks siempre corriendo
```

### Validation
- Weekly: Load test (ramp from 50 to 500 req/s)
- Monthly: Failover test (simulate AZ outage)
- Continuous: Monitor DesiredCount metric (alert <2 or >10)

---

## 5. CONFIABILIDAD (Reliability)

### Requerimiento
**MTTR** (Mean Time To Recover): < 2 minutes  
**MTTF** (Mean Time To Failure): > 720 hours (1 month between incidents)  
**Backup retention**: 30 days (RDS), 7 years (audit logs)  
**No data loss**: RPO = 0 (sync replication)

### Cómo se mide

#### 5.1 RDS Failover Test
- **Procedure**:
  ```bash
  # Simulate RDS primary failure
  aws rds reboot-db-instance --db-instance-identifier ticketdesk-prod --force-failover
  
  # Measure time to recovery
  measure: time until /health responds 200 OK
  target: < 2 minutes
  ```

#### 5.2 Backup Verification
- **Daily**: Check latest RDS backup exists
  ```bash
  aws rds describe-db-snapshots | grep LatestRestorableTime
  # Should be within last 24 hours
  ```

- **Weekly**: Restore backup to test environment
  - Create temporary RDS from snapshot
  - Verify data integrity (row counts match)
  - Delete temporary instance
  - Document: "Backup restore successful"

#### 5.3 Backup Retention Audit
- **RDS backups**: 30 days retention
  ```bash
  aws rds describe-db-instances | grep BackupRetentionPeriod
  # Should be 30
  ```

- **S3 audit logs**: 7 years retention
  ```bash
  aws s3api get-bucket-lifecycle | grep NoncurrentVersionExpiration
  # Should be 2557 days (7 years)
  ```

#### 5.4 Acceptance Criteria
```
Dado que RDS primary falla
Cuando failover se inicia
Entonces:
  ✓ Replica promueve < 120s
  ✓ DNS endpoint sigue siendo válido
  ✓ 0 conexiones perdidas (connection pool retries)
  ✓ RPO = 0 (no data lost)

Dado que snapshot antiguo (30+ días) existe
Cuando scheduled cleanup ejecuta
Entonces:
  ✓ Snapshot se elimina
  ✓ Backup retention stays at 30 days
  ✓ Audit logs > 30 days conservados
```

### Validation
- Weekly: RDS failover test
- Weekly: Backup restoration test
- Monthly: Backup retention audit
- Quarterly: Full disaster recovery drill

---

## 6. COSTO (Cost Efficiency)

### Requerimiento
**Budget**: $200/month AWS (estimated)  
**Components**:
  - RDS: $30/month (db.t3.small with backups)
  - ElastiCache: $15/month (cache.t3.micro)
  - ECS: $60/month (2-10 instances t3.medium)
  - S3/data transfer: $20/month
  - ALB/networking: $20/month
  - CloudWatch/other: $15/month
  - **Buffer/miscellaneous**: $40/month

### Cómo se mide

#### 6.1 AWS Cost Monitoring
- **Tool**: AWS Cost Explorer + Billing Dashboard
- **Baseline**: First month post-launch
- **Monthly tracking**:
  ```
  aws ce get-cost-and-usage --time-period StartDate=2026-06-01,EndDate=2026-06-30
  Group by: SERVICE
  Filter: Project=TicketDesk
  ```

#### 6.2 Cost Alerts
- **Alert**: If month-to-date spending > $220 (10% over budget)
- **Escalation**: If monthly total will exceed $250
- **Action**: DevOps to investigate spike (unusual traffic? runaway task?)

#### 6.3 Cost Optimization Opportunities
- **RDS**: Monitor unused storage (can downsize)
- **ECS**: Monitor max concurrent task count (max seen last month?)
- **S3**: Monitor lifecycle transitions (90d → Glacier savings)
- **Data transfer**: Monitor inter-AZ transfer (should be minimal)

#### 6.4 Acceptance Criteria
```
Dado que sistema está en producción por 30 días
Cuando se revisa AWS billing
Entonces:
  ✓ Total bill ≤ $250 (< 25% over budget)
  ✓ Per-service breakdown matches estimates
  ✓ No unexpected charges (orphaned resources)
  ✓ RDS, ElastiCache, ECS are primary costs

Dado que traffic aumenta a 500 req/s
Cuando auto-scaling escala a 8 tasks
Entonces:
  ✓ Bill increase proporcional (≈ 4x cost for 4x tasks)
  ✓ No hidden costs (data transfer, NAT Gateway)
```

### Validation
- Daily: AWS Cost Explorer dashboard
- Weekly: Cost forecast (if trend continues)
- Monthly: Detailed cost breakdown + optimization report
- Quarterly: Rightsizing analysis (could smaller instances work?)

---

## Resumen: Matriz de Aceptación

| NFR | Métrica | Target | Herramienta | Frecuencia |
|-----|---------|--------|------------|-----------|
| Disponibilidad | Uptime % | ≥ 99.5% | CloudWatch | Daily |
| Seguridad | Encryption check | 100% encrypted | aws cli | Weekly |
| Performance | p99 latency | < 2s | CloudWatch | Continuous |
| Escalabilidad | Auto-scale test | 2-10 tasks | Load test | Weekly |
| Confiabilidad | RDS failover | < 2 min | Manual test | Weekly |
| Costo | Monthly bill | ≤ $250 | AWS Billing | Monthly |

---

**Artefacto para**: Unit 1 - Infraestructura  
**Fecha**: 2026-05-27  
**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction - Estación 5, Actividad 2

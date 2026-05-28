# Business Rules — Unit 1: Infraestructura

## Reglas de Provisioning

### RULE-INFRA-01: VPC Multi-AZ obligatorio
- **Descripción**: Todo deployable debe estar en mínimo 2 Availability Zones diferentes para garantizar alta disponibilidad.
- **Condición**: Creación de cualquier recurso (RDS, Redis, ECS, ALB).
- **Consecuencia**: Si se intenta provisionar en una sola AZ, el deployment falla con error: "Multi-AZ deployment required".
- **Fuente**: HU-1.2 (Configurar VPC), HU-1.3 (RDS Multi-AZ), HU-1.4 (Redis setup), NfR Disponibilidad (99.5% SLA)
- **Implementación**:
  - VPC con subnets en us-south-1a y us-south-1b
  - RDS: Multi-AZ habilitado (auto failover <2 min)
  - ECS: mínimo 2 instances en AZs diferentes
  - ALB: listeners en ambas AZs

### RULE-INFRA-02: Encryption at rest en todos los datos
- **Descripción**: Todos los datos almacenados (RDS, Redis, S3, EBS, CloudWatch) deben estar encriptados con AWS KMS.
- **Condición**: Cualquier servicio de almacenamiento se crea.
- **Consecuencia**: Storage sin KMS es rechazado. LGPD compliance fallido.
- **Fuente**: HU-1.3, HU-1.4, HU-1.5, NFR Seguridad (LGPD Art. 5)
- **Implementación**:
  - RDS: KMS-encrypted volumes
  - Redis: at_rest_encryption_enabled = true
  - S3: server_side_encryption = aws:kms
  - EBS: encrypted = true
  - CloudWatch Logs: encrypted con KMS

### RULE-INFRA-03: TLS 1.3 obligatorio en tránsito
- **Descripción**: Todas las conexiones de red (ALB, API Gateway, Lambda) usan TLS 1.3 mínimo. No se permite TLS 1.2 o inferior.
- **Condición**: Cualquier comunicación cliente-servidor.
- **Consecuencia**: Conexión TLS <1.3 se rechaza (443 only, HTTP redirect a HTTPS).
- **Fuente**: NFR Seguridad, LGPD compliance
- **Implementación**:
  - ALB policy: TLS 1.3 + TLS 1.2 (minimum)
  - API Gateway: enforce HTTPS only
  - CloudFront: minimum TLS 1.2 (1.3 preferred)
  - Ciphers: solo ECDHE + AES-GCM

### RULE-INFRA-04: No secrets en código
- **Descripción**: Todas las credenciales (DB password, API keys, JWT secrets) deben estar en AWS Secrets Manager, nunca hardcodeadas.
- **Condición**: Cualquier configuración de credentials.
- **Consecuencia**: Pre-commit hook falla si detecta AWS_SECRET_ACCESS_KEY, DATABASE_PASSWORD, ANTHROPIC_API_KEY en archivos.
- **Fuente**: HU-1.5 (CI/CD), Security best practices
- **Implementación**:
  - .env.example: placeholders solo ("YOUR_API_KEY_HERE")
  - .env: gitignored
  - GitHub Actions: secrets rotados cada 90 días
  - ECS task role: IAM policy permite acceso solo a Secrets Manager

### RULE-INFRA-05: Security groups: least privilege
- **Descripción**: Security groups permiten tráfico mínimo necesario. Ningún 0.0.0.0/0 a BD, Redis, o servicios internos.
- **Condición**: Creación de SG rules.
- **Consecuencia**: Regla que abre 0.0.0.0/0 a puerto 5432 (DB) es rechazada. Alert a security team.
- **Fuente**: HU-1.2, Security audit
- **Implementación**:
  - ALB SG: allows 80 (HTTP) + 443 (HTTPS) from 0.0.0.0/0
  - ECS SG: allows port 8000 (backend), 3000 (frontend) from ALB SG only
  - RDS SG: allows 5432 only from ECS SG
  - Redis SG: allows 6379 only from ECS SG

### RULE-INFRA-06: NAT Gateway para egreso desde subnets privadas
- **Descripción**: ECS tasks (en subnets privadas) hacen requests outbound (Claude API, Docker hub pull) vía NAT Gateway, nunca directamente a internet.
- **Condición**: Creación de route table para subnet privada.
- **Consecuencia**: Sin NAT, requests fallan (no internet connectivity). Egreso no auditado.
- **Fuente**: HU-1.2, Network architecture
- **Implementación**:
  - 1 NAT Gateway por AZ (redundancia)
  - Subnet privada → route table → default route (0.0.0.0/0) → NAT Gateway
  - IP público de NAT puede ser whitelisted en sistemas externos (Claude API)

---

## Reglas de Bases de Datos

### RULE-DB-01: RDS Multi-AZ con failover automático
- **Descripción**: Base de datos replica sincrónitamente a AZ secundaria. Failover automático si primaria falla.
- **Condición**: RDS instance creada.
- **Consecuencia**: Downtime <2 minutos, ninguna pérdida de datos (sync replication).
- **Fuente**: HU-1.3, NfR Disponibilidad, SLA 99.5%
- **Implementación**:
  - multi_az = true
  - backup_retention_period = 30 (days)
  - Enhanced Monitoring habilitado
  - Automated backups = daily

### RULE-DB-02: Connection pooling (max 20)
- **Descripción**: Application usa connection pool con máximo 20 conexiones simultaneas.
- **Condición**: Cualquier request a BD.
- **Consecuencia**: Si pool se agota, request espera con timeout. Si timeout > 5s, request falla (circuit breaker).
- **Fuente**: HU-2.2 (SQLAlchemy models), Performance tuning
- **Implementación**:
  - FastAPI + SQLAlchemy: pool_size = 10, max_overflow = 10
  - Redis: connection pool = 5
  - Metrics: monitor pool utilization (alert >80%)

### RULE-DB-03: Database encryption password rotation
- **Descripción**: PostgreSQL password rotado cada 90 días vía Secrets Manager rotation.
- **Condición**: Cada 90 días.
- **Consecuencia**: Password antiguo invalida (aplicación auto-updates vía Secrets Manager), si no se rota → security risk.
- **Fuente**: Security policy, LGPD compliance
- **Implementación**:
  - Secrets Manager rotation: Lambda function
  - Rotation schedule: cada 90 días
  - Zero-downtime rotation (new password antes de invalidar viejo)

### RULE-DB-04: Automated backups con 30 días retención
- **Descripción**: RDS automaticamente crea backups diarios, retiene 30 días.
- **Condición**: RDS instance running.
- **Consecuencia**: Data loss < 1 día (RPO). Restore < 15 minutos (RTO).
- **Fuente**: HU-1.3, Disaster recovery, LGPD compliance
- **Implementación**:
  - backup_retention_period = 30
  - preferred_backup_window = "02:00-03:00 UTC" (low traffic)
  - Multi-region snapshots (copy to backup region monthly)

---

## Reglas de Caching

### RULE-CACHE-01: Redis maxmemory-policy: allkeys-lru
- **Descripción**: Si Redis alcanza máxima memoria, elimina keys menos recientemente usadas (LRU eviction).
- **Condición**: Redis cluster at capacity.
- **Consecuencia**: Keys antiguas se descartan (cache miss acceptable), nunca memory error.
- **Fuente**: HU-1.4, Performance optimization
- **Implementación**:
  - maxmemory = 1GB (t3.micro default)
  - maxmemory_policy = "allkeys-lru"
  - Monitoring: alert si eviction rate > 100 keys/min

### RULE-CACHE-02: Cache TTL defaults
- **Descripción**: Session cache (24h), Rubric cache (7 days), Queue (real-time no TTL).
- **Condición**: Cualquier data almacenada en Redis.
- **Consecuencia**: Keys expiran automáticamente. Datos stale descartados.
- **Fuente**: HU-3, HU-4, Performance design
- **Implementación**:
  - Session: EXPIRE session:{id} 86400 (24h)
  - Rubric: EXPIRE rubric:{id} 604800 (7d)
  - Queue: LPUSH event:screening.started (no TTL, persisted en Celery)

---

## Reglas de Container Orchestration

### RULE-ECS-01: Auto-scaling policy
- **Descripción**: ECS cluster escala automáticamente entre 2-10 tasks basado en CPU utilization.
- **Condición**: CPU > 70% → +1 task | CPU < 30% → -1 task
- **Consecuencia**: Aplicación mantiene latencia <2s bajo carga. Costo controlado (scale down cuando baja demanda).
- **Fuente**: HU-1.5, Performance SLA <2s p99
- **Implementación**:
  - Target tracking scaling: CPU 70%
  - Min capacity = 2, Max = 10
  - Scale-up cooldown = 60s, Scale-down = 300s

### RULE-ECS-02: Health checks cada 30 segundos
- **Descripción**: ALB health checks envían request a /health cada 30s. Si falla 3 veces consecutivas → task se reemplaza.
- **Condición**: Cada 30 segundos.
- **Consecuencia**: Task unhealthy se reemplaza < 2 minutos. Traffic redirigido a healthy tasks.
- **Fuente**: HU-1.5, HA requirement
- **Implementación**:
  - Health check path: /health
  - Interval: 30 segundos
  - Healthy threshold: 2 checks pasados
  - Unhealthy threshold: 3 checks fallidos
  - Timeout: 5 segundos

### RULE-ECS-03: Despliegue blue-green con rollback automático
- **Descripción**: Nueva versión de código se despliega a nuevo task definition (green). Si health checks fallan → revert a viejo (blue).
- **Condición**: Cada deploy vía GitHub Actions.
- **Consecuencia**: Zero-downtime deployment. Fallo automaticamente revertido.
- **Fuente**: HU-1.5 (CI/CD), Reliability
- **Implementación**:
  - GitHub Actions: create new task definition
  - ECS: canary deployment (2 tasks green, 1 blue)
  - Monitor health checks (5 min)
  - Si health check falla: revert to blue

### RULE-ECS-04: Logging obligatorio a CloudWatch
- **Descripción**: Todos los logs de container (stdout/stderr) envían a CloudWatch. Retención 30 días (prod), 7 años audit logs.
- **Condición**: Task running.
- **Consecuencia**: Logs centralizados, searchable, auditables. Acceso controlado por IAM.
- **Fuente**: HU-1.5, Observability, Compliance
- **Implementación**:
  - Log driver: awslogs
  - Log group: /aws/ecs/ticketdesk/{backend|frontend}
  - Retention: 30 días (produtoduction logs)
  - Audit logs: 7 años (separate log group)

---

## Reglas de Storage (S3)

### RULE-S3-01: Bucket public access block
- **Descripción**: S3 bucket tiene public access completamente BLOQUEADO. No se permite uploads no encriptados.
- **Condición**: Creación de bucket, upload de object.
- **Consecuencia**: Bucket no accessible vía internet (private only). Violación de encriptación → upload rechazado.
- **Fuente**: HU-1.5, Security
- **Implementación**:
  - BlockPublicAcls = true
  - BlockPublicPolicy = true
  - IgnorePublicAcls = true
  - RestrictPublicBuckets = true
  - Bucket policy: Deny * if not encrypted (SSE-KMS)

### RULE-S3-02: Versioning habilitado
- **Descripción**: S3 mantiene múltiples versiones de cada object. Protect contra accidental delete.
- **Condición**: Bucket created.
- **Consecuencia**: Puede recuperar version anterior de transcripción si se corrompe.
- **Fuente**: HU-3, Data recovery
- **Implementación**:
  - versioning_status = Enabled
  - MFA delete = enabled (require MFA to permanently delete)

### RULE-S3-03: Lifecycle policy (90 días personal data, 7 años audit)
- **Descripción**: Personal data (transcriptions) se archiva después 90 días (LGPD), audit logs se conservan 7 años.
- **Condición**: Objeto creado en S3.
- **Consecuencia**: 90 días → Glacier (cheaper storage). 7 años → Glacier. >7 años → deleted.
- **Fuente**: HU-6, LGPD compliance, Data retention
- **Implementación**:
  - Prefix "transcriptions/": Transition to Glacier at 90 days, Delete at 365 days
  - Prefix "audit-logs/": Transition to Glacier at 7 years, Delete at 7 years + 1 day
  - Prefix "knowledge-base/": Transition to Glacier at 2 years (indefinite)

---

## Reglas de Monitoreo y Alertas

### RULE-MONITOR-01: CloudWatch alarms críticas → SNS → Email
- **Descripción**: Alarma crítica (RDS down, ECS tasks failing, CPU >90%) triggers SNS notification.
- **Condición**: Métrica cruza threshold.
- **Consecuencia**: Email inmediato a on-call engineer. Respuesta esperada <15 min.
- **Fuente**: HU-1.5, SLA 99.5% uptime
- **Implementación**:
  - Alarm: RDSAvailability (state != "available")
  - Alarm: ECSTaskCount (< 2)
  - Alarm: ALBTargetResponseTime (p99 > 2s)
  - SNS topic: critical-alerts → email suscriptions

### RULE-MONITOR-02: Dashboards en CloudWatch
- **Descripción**: Dashboard en tiempo real muestra estado de infraestructura (RDS connections, Redis memory, ECS CPU, etc).
- **Condición**: Cada minuto.
- **Consecuencia**: Operador puede ver health en un vistazo. Alertas visibles.
- **Fuente**: HU-1.5, Observability
- **Implementación**:
  - Dashboard name: TicketDesk-Infrastructure
  - Widgets: RDS utilization, Redis memory, ECS CPU/memory, ALB latency, error rate

---

**Artefacto para**: Unit 1 - Infraestructura  
**Fecha**: 2026-05-27  
**Fase**: Construction - Estación 5, Actividad 1

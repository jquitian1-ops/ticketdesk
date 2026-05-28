# NFR Design — Unit 1: Infraestructura

**Propósito**: Documentar ADRs (Architecture Decision Records) y patrones de diseño que cumplen cada NFR. Cada decisión incluye contexto, opciones evaluadas, decisión tomada y consecuencias.

---

## ADR-UNIT1-001: Multi-AZ Architecture para Disponibilidad

### Contexto
TicketDesk Enterprise requiere 99.5% uptime SLA (máximo 3.7 horas downtime/año). Un AZ puede fallar. Necesitamos arquitectura que sobreviva fallo de AZ sin pérdida de datos.

### Opciones Evaluadas

**Opción A**: Single AZ deployment (no redundancia)
- Pros: Simplicity, costo mínimo (~$150/mes)
- Cons: Fallo de AZ = total outage, viola SLA, LGPD risk (no backup geo)
- **Decisión**: RECHAZADA

**Opción B**: Multi-AZ with async replication (eventual consistency)
- Pros: RPO = minutes (acceptable downtime)
- Cons: Data loss posible en failover (inaceptable para LGPD)
- **Decisión**: RECHAZADA

**Opción C**: Multi-AZ with sync replication (this decision)
- Pros: RPO = 0, RTO < 2 min, LGPD compliant
- Cons: Latency increase (~10ms inter-AZ), slightly higher cost
- **Decisión**: ACEPTADA ✅

### Decisión Tomada

**Implementar Multi-AZ architecture con sync replication:**

1. **VPC**: Span 2 AZs (us-south-1a, us-south-1b)
2. **RDS**: Multi-AZ enabled
   - Primary en us-south-1a
   - Synchronous replica en us-south-1b
   - Failover automático si primary down
3. **ECS cluster**: Min 2 tasks en AZs diferentes
4. **ALB**: Listeners en ambas AZs
5. **Data storage**:
   - PostgreSQL: sync replication built-in
   - Redis: Single instance (v1.1 add Redis sentinel)
   - S3: Automatically geo-replicated

### Consecuencias

✅ **Beneficios**:
- 99.5% uptime alcanzable
- RPO = 0 (no data loss)
- RTO < 2 min (automatic failover)
- LGPD compliant (no data loss)

⚠️ **Trade-offs**:
- Costo +$30/mes (extra instances, inter-AZ transfer)
- Latencia inter-AZ ~10ms (acceptable, <2s p99 target)
- Operational complexity (monitoring 2 AZs, failover testing)

### Implementación
```terraform
# RDS Multi-AZ
resource "aws_db_instance" "postgres" {
  multi_az = true
  availability_zone = "us-south-1a"
  # AWS creates replica in us-south-1b automatically
}

# ECS tasks across AZs
resource "aws_ecs_service" "backend" {
  desired_count = 2
  # AWS scheduler places tasks in different AZs
}

# ALB targets in both AZs
resource "aws_lb_target_group" "backend" {
  # Targets registered in both AZs automatically
}
```

---

## ADR-UNIT1-002: AWS KMS + TLS 1.3 para Seguridad

### Contexto
LGPD require encryption at rest + in transit. Candidato data es PII (nome, email, responses). Reclutador data é PII. Audit logs são sensibles (quem fez o quê quando).

Precisamos guarantir:
1. Data encrypted before leaving application
2. No plaintext em storage
3. Apenas HTTPS com TLS 1.3

### Opciones Evaluadas

**Opción A**: No encryption (just rely on AWS defaults)
- Pros: Simplest
- Cons: LGPD violation, data breach risk, non-compliant
- **Decisión**: REJEITADA

**Opción B**: Application-level encryption (encrypt before sending to AWS)
- Pros: Full control, LGPD compliant
- Cons: Key management overhead, performance hit, operational complexity
- **Decisión**: REJEITADA (too complex for MVP)

**Opção C**: AWS KMS + TLS (this decision)
- Pros: AWS manages keys, automatic rotation, LGPD compliant, good UX
- Cons: Vendor lock-in to AWS KMS
- **Decisión**: ACEITA ✅

### Decisão Tomada

**AWS KMS para encryption at rest + TLS 1.3 para encryption in transit:**

#### At Rest
1. **RDS**: Encrypted with KMS
   ```terraform
   storage_encrypted = true
   kms_key_id = aws_kms_key.primary.arn
   ```

2. **ElastiCache**: Encrypted with KMS
   ```terraform
   at_rest_encryption_enabled = true
   kms_key_id = aws_kms_key.primary.arn
   ```

3. **S3**: Encrypted with KMS
   ```terraform
   server_side_encryption_configuration {
     rule {
       apply_server_side_encryption_by_default {
         sse_algorithm = "aws:kms"
         kms_master_key_id = aws_kms_key.primary.arn
       }
     }
   }
   ```

4. **EBS volumes**: Encrypted
   ```terraform
   ebs_block_device {
     encrypted = true
     kms_key_id = aws_kms_key.primary.arn
   }
   ```

#### In Transit
1. **ALB**: TLS 1.3
   ```terraform
   listener {
     protocol = "HTTPS"
     ssl_policy = "ELBSecurityPolicy-TLS-1-3-2021-06"
     certificate_arn = aws_acm_certificate.main.arn
   }
   ```

2. **RDS connections**: TLS required
   ```python
   # SQLAlchemy
   engine = create_engine(
     f"postgresql+psycopg2://{user}:{password}@{host}/db?sslmode=require",
     ...
   )
   ```

3. **Redis connections**: TLS required
   ```python
   # Redis client
   redis.Redis(
     host=REDIS_HOST,
     port=6379,
     ssl=True,
     ssl_cert_reqs='required'
   )
   ```

### Consequências

✅ **Benefícios**:
- LGPD compliant (encryption requirement fulfilled)
- Data protected from insider threats (AWS KMS isolation)
- Automatic key rotation (AWS handles)
- Transparent to application (AWS APIs handle encryption)

⚠️ **Trade-offs**:
- KMS API calls add latency (~5ms per request)
- Cost: KMS $1/month base + $0.03 per 10k requests
- Vendor lock-in: Can't move to non-AWS easily

---

## ADR-UNIT1-003: Circuit Breaker + Fallback para Confiabilidade

### Contexto
Unit 1 infraestructura fornece base para Units 2-6. Unit 3 (BotEngine) chama Claude API, que pode falhar. Precisamos isolar falhas (fallo em Claude != fallo do sistema inteiro).

Pattern: Circuit Breaker (com fallback questions).

### Decisão Tomada

**Circuit Breaker pattern com 3 estados:**

1. **CLOSED** (normal operation)
   - Requests → Claude API
   - Success → continue
   - Failure → increment counter

2. **OPEN** (too many failures)
   - Threshold: 5 consecutive failures OR 50% failure rate
   - Requests → return fallback question
   - Health check: periodically retry (every 30s)

3. **HALF_OPEN** (recovery testing)
   - Limited requests → Claude API
   - If success: reset counter, go to CLOSED
   - If failure: go back to OPEN

### Implementação
```python
# app/shared/services/circuit_breaker.py
class ClaudeCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        self.failure_threshold = failure_threshold
        self.timeout = timeout
    
    async def call(self, coro, fallback_question):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                return {"response": fallback_question, "is_fallback": True}
        
        try:
            result = await coro
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            return {"response": fallback_question, "is_fallback": True}
```

### Consequências
- ✅ Claude API failures don't crash system (graceful degradation)
- ✅ Fallback questions keep candidate experience smooth
- ✅ Automatic recovery (HALF_OPEN testing)
- ⚠️ Fallback questions may be less ideal (basic questions vs tailored)

---

## ADR-UNIT1-004: Auto-scaling Policy (CPU-based)

### Contexto
TicketDesk traffic é variable. Peak hours (morning) temos 500 req/s, off-hours 10 req/s. Precisamos escalar automatically para manter latência baixa (<2s p99) sem desperdiçar dinheiro.

### Opciones Evaluadas

**Opción A**: Fixed number of tasks (static)
- Pros: Predictable cost
- Cons: Over-provisioned off-hours, under-provisioned peak (violates SLA)
- **Decisión**: REJEITADA

**Opción B**: Schedule-based scaling (time-of-day)
- Pros: Predictable traffic patterns
- Cons: Doesn't handle unexpected traffic spikes, requires maintenance
- **Decisión**: REJEITADA (no spike handling)

**Opção C**: Metric-based auto-scaling (this decision)
- Pros: Reacts to actual load, automatic, optimizes cost
- Cons: May oscillate (if thresholds not tuned well)
- **Decisión**: ACEITA ✅

### Decisão Tomada

**CPU-based Target Tracking Auto-Scaling:**

```terraform
# ECS Service Auto Scaling
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity = 10
  min_capacity = 2
  resource_id = "service/ticketdesk-prod/backend"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_policy" {
  policy_name = "cpu-targeting"
  policy_type = "TargetTrackingScaling"
  
  target_tracking_scaling_policy_configuration {
    target_value = 70.0  # Scale up at 70% CPU
    
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    
    scale_out_cooldown = 60    # 60s after scale-up
    scale_in_cooldown = 300    # 5 min after scale-down
  }
}
```

### Limites
- Min: 2 tasks (HA, 0 single point of failure)
- Max: 10 tasks (cost control, ~$100/month)

### Métricas Monitoreadas
- CPU > 70% → scale up
- CPU < 30% (for 10 min) → scale down
- Memory < 80% (no memory pressure)
- Disk I/O < 50% (no disk saturation)

### Consequências
- ✅ Automatic scaling handles spikes
- ✅ Cost optimized (scale down off-hours)
- ✅ Maintains <2s latency under load
- ⚠️ May have brief latency spikes during scale-up

---

## ADR-UNIT1-005: Terraform + AWS para Infrastructure as Code

### Contexto
Infrastructure precisará ser versionada, reproducível, auditável. Opções: Terraform, CloudFormation, CDK.

### Opciones Evaluadas

**Opción A**: Manual AWS Console clicks
- Pros: Flexible, immediate
- Cons: No version history, not reproducible, error-prone
- **Decisión**: REJEITADA

**Opción B**: AWS CloudFormation
- Pros: AWS-native, no learning curve
- Cons: YAML verbosity, limited language support
- **Decisión**: REJEITADA

**Opção C**: Terraform (this decision)
- Pros: Multi-cloud, readable HCL, strong community, IaC best practice
- Cons: Learning curve, separate state management
- **Decisión**: ACEITA ✅

### Decisão Tomada

**Terraform for 100% Infrastructure as Code:**

Structure:
```
infrastructure/
├── main.tf         # VPC, subnets, security groups
├── rds.tf          # RDS instance
├── redis.tf        # ElastiCache
├── ecs.tf          # ECS cluster + services
├── alb.tf          # Application Load Balancer
├── s3.tf           # S3 buckets
├── cloudwatch.tf   # Monitoring, alarms
├── variables.tf    # Input variables
├── outputs.tf      # Output values
├── terraform.tfvars # Environment-specific values
└── .gitignore      # Ignore tfstate files
```

Workflow:
```bash
terraform init         # Initialize backend + providers
terraform plan        # Review changes (before apply)
terraform apply       # Apply changes (with approval)
terraform destroy     # Teardown (for test envs)
```

### Consequências
- ✅ Infrastructure version-controlled in Git
- ✅ Code review before infrastructure changes
- ✅ Reproducible deployments (same code = same infra)
- ✅ Disaster recovery: `terraform apply` from repo
- ⚠️ Terraform state file needs securing (lock + encryption)
- ⚠️ Team must learn Terraform HCL

---

## ADR-UNIT1-006: CloudWatch + SNS para Observabilidade

### Contexto
Produção precisa de monitoramento. Quando algo quebra, on-call engineer deve saber em < 5 minutos.

### Opciones Evaluadas

**Opción A**: No monitoring
- Pros: Costo zero
- Cons: Blind, descobrimos problemas vía customer complaints
- **Decisión**: REJEITADA

**Opção B**: Third-party SaaS (DataDog, New Relic)
- Pros: Rich features, great UX
- Cons: Costo ~$500/mes, vendor lock-in, overkill para MVP
- **Decisión**: REJEITADA

**Opção C**: CloudWatch + SNS (this decision)
- Pros: AWS-native, cost ~$50/mes, sufficient para MVP
- Cons: Less rich UI than DataDog, basic alerting
- **Decisión**: ACEITA ✅

### Decisão Tomada

**CloudWatch para metrics + logs, SNS para alertas:**

#### Logs
```terraform
resource "aws_cloudwatch_log_group" "ecs_backend" {
  name = "/aws/ecs/ticketdesk/backend"
  retention_in_days = 30
  kms_key_id = aws_kms_key.primary.arn
}
```

#### Metrics + Alarms
```terraform
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name = "RDS CPU High"
  metric_name = "CPUUtilization"
  namespace = "AWS/RDS"
  statistic = "Average"
  threshold = 80
  comparison_operator = "GreaterThanThreshold"
  alarm_actions = [aws_sns_topic.critical_alerts.arn]
}
```

#### Dashboards
- Real-time metrics (CPU, memory, latency, error rate)
- Updated every minute
- Accessible to ops team

### Consequências
- ✅ Observability <5min latency to alert
- ✅ Cost-effective ($50/mes)
- ✅ AWS-native integration (no new tools)
- ⚠️ CloudWatch UI less polished than SaaS alternatives

---

## Resumen: ADRs Implementadas

| ADR | Padrón | Benefício | Custo |
|-----|--------|-----------|-------|
| ADR-001 | Multi-AZ | 99.5% uptime | +$30/mes |
| ADR-002 | KMS + TLS | LGPD compliance | +$10/mes |
| ADR-003 | Circuit Breaker | Graceful degradation | 0 |
| ADR-004 | Auto-scaling | Cost optimization | 0 |
| ADR-005 | Terraform | IaC reproducibility | 0 |
| ADR-006 | CloudWatch | Observability | +$50/mes |

**Total Estimado**: $200/mes

---

**Artefacto para**: Unit 1 - Infraestructura  
**Fecha**: 2026-05-27  
**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction - Estación 5, Actividad 2

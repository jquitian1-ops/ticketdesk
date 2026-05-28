# Actividad 5: Pruebas e Integración — Plan de Ejecución

**Fecha Inicio**: 2026-05-27  
**Duración Estimada**: 3-4 horas  
**Objetivo**: Validar que Terraform despliega infraestructura correctamente y todos los componentes funcionan juntos

---

## 📋 Actividades de Actividad 5

### Fase 1: Validación Terraform (30 min)

#### Paso 1.1: Validación de Sintaxis
```bash
cd terraform

# Format check
terraform fmt -check -recursive .
# Output esperado: All files properly formatted

# Syntax validation
terraform init -backend=false  # Init without S3 backend
terraform validate
# Output esperado: Success! The configuration is valid.
```

#### Paso 1.2: TFLint (Best Practices)
```bash
# Install TFLint
curl https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Run linter
tflint --init
tflint --format compact
# Output esperado: No errors (warnings acceptable)
```

#### Paso 1.3: Plan Review
```bash
# Create plan file
terraform plan \
  -var-file="environments/production/terraform.tfvars" \
  -var="database_password=$DB_PASSWORD" \
  -var="redis_auth_token=$REDIS_TOKEN" \
  -out=tfplan

# Review plan
terraform show tfplan | head -100
# Output esperado: See resource creations (no destroy)
```

**Aceptación**: ✅ Validación pasa sin errores críticos

---

### Fase 2: Provisión de Infraestructura (60-90 min)

#### Paso 2.1: Preparar Variables
```bash
# Set environment variables (or use .tfvars file)
export TF_VAR_database_password="YourSecurePassword123!@#"
export TF_VAR_redis_auth_token="YourTokenAbcdef123456789012"
export TF_VAR_backend_image="123456789012.dkr.ecr.us-south-1.amazonaws.com/ticketdesk-backend:latest"
export TF_VAR_frontend_image="123456789012.dkr.ecr.us-south-1.amazonaws.com/ticketdesk-frontend:latest"
export TF_VAR_certificate_arn="arn:aws:acm:us-south-1:123456789012:certificate/12345678-1234-1234"
export TF_VAR_domain_name="ticketdesk.staging.example.com"
export TF_VAR_alert_email="ops@ticketdesk.example.com"
```

#### Paso 2.2: Aplicar Configuración
```bash
# Apply with approval
terraform apply \
  -var-file="environments/staging/terraform.tfvars" \
  -auto-approve \
  tfplan 2>&1 | tee apply.log

# Expected duration: 15-20 minutes
# Observe module provisioning order:
# 1. KMS (encryption key)
# 2. VPC + CloudWatch (dependencies)
# 3. Security Groups
# 4. RDS (5-10 min)
# 5. Redis (2-3 min)
# 6. S3, ECR (immediate)
# 7. ECS (task definitions, services)
# 8. ALB (target groups, listeners)
# 9. Route53 (DNS)
```

#### Paso 2.3: Capturar Outputs
```bash
# Save all outputs
terraform output -json > outputs.json

# Extract key values
ALB_DNS=$(terraform output -raw alb_dns_name)
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
ECS_CLUSTER=$(terraform output -raw cluster_name)

echo "ALB: $ALB_DNS"
echo "RDS: $RDS_ENDPOINT"
echo "Redis: $REDIS_ENDPOINT"
echo "Cluster: $ECS_CLUSTER"
```

**Aceptación**: ✅ Todos los recursos creados sin errores

---

### Fase 3: Validación de Health Checks (45 min)

#### Paso 3.1: Esperar Stabilización
```bash
# Wait for ALB to become healthy (2-3 minutes)
# Wait for ECS tasks to reach RUNNING state

# Monitor ECS services
watch -n 5 'aws ecs describe-services \
  --cluster '$ECS_CLUSTER' \
  --services ticketdesk-backend-service ticketdesk-frontend-service \
  --region us-south-1 \
  --query "services[*].{Service:serviceName,Status:status,RunningCount:runningCount,DesiredCount:desiredCount}"'

# Expected output:
# Service                       Status   RunningCount  DesiredCount
# ticketdesk-backend-service    ACTIVE   2             2
# ticketdesk-frontend-service   ACTIVE   2             2
```

#### Paso 3.2: Validar Target Groups
```bash
# Check backend target group health
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw backend_target_group_arn) \
  --region us-south-1 \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Description]'

# Expected output:
# All targets should show "healthy"
# Example:
# "11.22.33.44:8000"  "healthy"  "Health checks passed"
# "11.22.33.45:8000"  "healthy"  "Health checks passed"
```

#### Paso 3.3: Validar RDS
```bash
# Check RDS instance status
aws rds describe-db-instances \
  --db-instance-identifier ticketdesk-postgres \
  --region us-south-1 \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Class:DBInstanceClass,Engine:Engine,MultiAZ:MultiAZEnabled}'

# Expected output:
# Status: available
# MultiAZEnabled: true
```

#### Paso 3.4: Validar Redis
```bash
# Check Redis cluster status
aws elasticache describe-cache-clusters \
  --cache-cluster-id ticketdesk-redis \
  --region us-south-1 \
  --query 'CacheClusters[0].{Status:CacheClusterStatus,Engine:Engine,Node:CacheNodeType}'

# Expected output:
# Status: available
# Engine: redis
```

#### Paso 3.5: Validar DNS
```bash
# Check Route53 health checks
aws route53 get-health-check-status \
  --health-check-id $(terraform output -raw app_health_check_id) \
  --query 'HealthCheckObservations[0].StatusReport'

# Expected output:
# Status: Success
# IPv4Address: (ALB IP)

# Verify DNS resolves
nslookup ticketdesk.staging.example.com
dig ticketdesk.staging.example.com
```

**Aceptación**: ✅ Todos los health checks PASSED

---

### Fase 4: Pruebas de Conectividad (30 min)

#### Paso 4.1: Probar ALB
```bash
# Direct ALB health endpoint
curl -v https://$ALB_DNS/health \
  -H "Host: ticketdesk.staging.example.com" \
  -k  # ignore self-signed cert

# Expected: 200 OK
# Body: {"status": "ok"}
```

#### Paso 4.2: Probar Frontend
```bash
# Frontend homepage
curl -s https://$ALB_DNS/ \
  -H "Host: ticketdesk.staging.example.com" \
  -k | head -50

# Expected: HTML content (Next.js page)
```

#### Paso 4.3: Probar Backend API
```bash
# Backend API health
curl -s https://$ALB_DNS/api/health \
  -H "Host: ticketdesk.staging.example.com" \
  -k | jq .

# Expected: {"status": "healthy", "version": "1.0.0"}
```

#### Paso 4.4: Probar Database (desde ECS task)
```bash
# Connect to RDS from within VPC
aws ecs execute-command \
  --cluster $ECS_CLUSTER \
  --task (obtener task ID) \
  --container ticketdesk-backend \
  --command "psql -h $RDS_ENDPOINT -U ticketdesk_admin -d ticketdesk -c 'SELECT 1;'"

# Expected: (1 row, SELECT 1)
```

#### Paso 4.5: Probar Cache (desde ECS task)
```bash
# Test Redis connection
aws ecs execute-command \
  --cluster $ECS_CLUSTER \
  --task (obtener task ID) \
  --container ticketdesk-backend \
  --command "redis-cli -h $REDIS_ENDPOINT PING"

# Expected: PONG
```

**Aceptación**: ✅ Todos los endpoints responden correctamente

---

### Fase 5: Load Testing (30 min)

#### Paso 5.1: Instalar Apache Bench
```bash
apt-get update && apt-get install -y apache2-utils
# o
brew install httpd  # macOS
```

#### Paso 5.2: Baseline Load Test
```bash
# Test 1: Simple requests (low concurrency)
ab -n 100 -c 5 \
  -H "Host: ticketdesk.staging.example.com" \
  https://$ALB_DNS/

# Expected output:
# Requests per second: 10-20 (baseline)
# Time per request: 50-100ms (p50)
# Failed requests: 0
```

#### Paso 5.3: Increased Concurrency
```bash
# Test 2: Higher concurrency
ab -n 500 -c 20 \
  -H "Host: ticketdesk.staging.example.com" \
  https://$ALB_DNS/

# Expected:
# No connection errors
# All requests complete
# p99 latency <2s (SLA requirement)
```

#### Paso 5.4: Sustained Load (5 minutes)
```bash
# Test 3: Sustained traffic
ab -t 300 -c 10 \
  -H "Host: ticketdesk.staging.example.com" \
  https://$ALB_DNS/ | tee load-test-results.txt

# Monitor during test:
watch -n 2 'aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --statistics Average \
  --start-time $(date -u -d "5 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --region us-south-1 \
  --query "Datapoints[*].[Timestamp,Average]" \
  --sort-ascending'
```

#### Paso 5.5: Analizar Resultados
```bash
# Parse load test results
grep -E "Requests per second|Time per request|Failed requests" load-test-results.txt

# Expected metrics:
# RPS: 15-30 (depends on instance size)
# p50 latency: 50-150ms
# p99 latency: <2000ms (SLA requirement)
# Failed requests: 0
```

**Aceptación**: ✅ Latencia p99 <2s, sin errores

---

### Fase 6: Verificación de Monitoring (15 min)

#### Paso 6.1: CloudWatch Dashboards
```bash
# Get dashboard URLs
terraform output infrastructure_dashboard_url
terraform output application_dashboard_url

# Open in browser and verify:
# - ECS task count trending up during load test
# - RDS CPU <50%
# - Redis memory <20%
# - ALB response time trending
# - Request count increasing
```

#### Paso 6.2: Métricas Personalizadas
```bash
# Check custom application metrics
aws cloudwatch get-metric-statistics \
  --namespace ticketdesk/Performance \
  --metric-name APILatencyP99 \
  --start-time $(date -u -d "10 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Maximum \
  --region us-south-1

# Expected: Values <2000ms
```

#### Paso 6.3: Alarmas
```bash
# Verify no alarms triggered
aws cloudwatch describe-alarms \
  --state-value ALARM \
  --region us-south-1

# Expected output: Empty (no alarms firing)
```

**Aceptación**: ✅ Monitoring activo sin alertas críticas

---

### Fase 7: Cleanup / Teardown (15 min)

#### Paso 7.1: Guardar Resultados
```bash
# Archive all test results
mkdir -p test-results/$(date +%Y-%m-%d)
cp apply.log test-results/$(date +%Y-%m-%d)/
cp outputs.json test-results/$(date +%Y-%m-%d)/
cp load-test-results.txt test-results/$(date +%Y-%m-%d)/
aws cloudwatch get-dashboard --dashboard-name ticketdesk-infrastructure > test-results/$(date +%Y-%m-%d)/dashboard.json

git add test-results/
git commit -m "Test results: Actividad 5 validation"
```

#### Paso 7.2: Decidir Sobre Staging vs Production
```bash
# Option A: Keep staging for further testing
echo "Keeping staging environment for integration testing"

# Option B: Destroy staging (cost optimization)
terraform destroy \
  -var-file="environments/staging/terraform.tfvars" \
  -var="database_password=$DB_PASSWORD" \
  -var="redis_auth_token=$REDIS_TOKEN" \
  -auto-approve

# Expected output: All resources destroyed (~2 minutes)
```

**Aceptación**: ✅ Infraestructura validada y documentada

---

## ✅ Criterios de Aceptación de Actividad 5

- [ ] `terraform validate` passa sin errores
- [ ] `terraform plan` sin destroy commands
- [ ] `terraform apply` exitoso (todos los recursos creados)
- [ ] ECS services en ACTIVE state, running tasks = desired
- [ ] Target groups healthy (todos targets healthy)
- [ ] RDS status "available", Multi-AZ enabled
- [ ] Redis status "available"
- [ ] Route53 health checks passing
- [ ] ALB responde 200 OK en /health
- [ ] Load test: p99 latency <2s
- [ ] Load test: 0 failed requests
- [ ] CloudWatch alarms: 0 ALARM state
- [ ] Dashboard muestra métricas en tiempo real
- [ ] Resultados documentados en test-results/

---

## 📊 Resultados Esperados

### Infrastructure Health
```
✓ VPC: 1 VPC, 6 subnets, 2 NAT Gateways
✓ Security: 4 Security Groups, 14 rules
✓ Database: RDS Multi-AZ, available, synced
✓ Cache: Redis Multi-AZ, available, replicating
✓ Containers: 4 ECS tasks (2 backend, 2 frontend)
✓ Load Balancer: ALB healthy, 4/4 targets healthy
✓ Storage: 3 S3 buckets, ECR repos with images
✓ DNS: Route53 health checks passing
✓ Monitoring: Dashboards updating, 0 alarms
```

### Performance Baseline
```
p50 latency: 50-150ms
p99 latency: 500-1500ms (target <2000ms)
RPS capacity: 15-30 requests/sec
CPU utilization: 20-40% under load
Memory utilization: 15-25% under load
```

---

## 🔄 Próximos Pasos

Después de Actividad 5 completada:

1. **Deploy a Producción** (si todo pasa):
   - Crear domain CNAME en production
   - Aplicar terraform con prod tfvars
   - Ejecutar smoke tests contra production

2. **Comienza Unit 2** (Backend Fundamentals):
   - FastAPI project structure
   - SQLAlchemy models (9 tables)
   - Repository layer (CRUD)
   - Middleware (auth, error handling)

3. **Paralelo**: Units 3-5 (BotEngine, EvaluationEngine, Frontend)

---

## 📝 Logging & Documentación

Todos los logs se guardan automáticamente:
```
terraform/apply.log        # Terraform apply output
outputs.json              # All terraform outputs
load-test-results.txt     # Apache Bench results
test-results/DATE/        # Archived test artifacts
```

Para reportar issues:
```bash
terraform show tfstate.json | grep -i error
aws logs tail /ecs/ticketdesk --follow
aws events list-rules --name-prefix ticketdesk
```

---

**Generado**: 2026-05-27  
**Unit**: 1 - Infraestructura  
**Actividad**: 5 - Pruebas e Integración  
**Status**: 🚀 LISTO PARA EJECUCIÓN

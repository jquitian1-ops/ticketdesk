# Domain Entities — Unit 1: Infraestructura

## Bounded Context

**Nombre**: AWS Infrastructure Provisioning & Management  
**Descripción**: Provisión, configuración y gestión de stack AWS completo para TicketDesk Enterprise. Incluye VPC, subnets, RDS, Redis, ECS, S3, CI/CD pipeline, monitoreo y alertas.  
**Límites**: Desde la creación de VPC hasta la verificación de health checks en todos los servicios.

---

## Entities

### VirtualPrivateCloud (VPC)
- **Identidad**: VPC ID (`vpc-xxxxx`)
- **Atributos**:
  - region: "us-south-1" (São Paulo - LGPD)
  - cidr_block: "10.0.0.0/16"
  - dns_hostnames_enabled: true
  - dns_resolution_enabled: true
  - enable_nat_gateway: true
  - tags: {Environment: "production", Project: "TicketDesk"}
- **Comportamientos**:
  - create_subnets() → crea subnets públicas/privadas
  - create_security_groups() → configura firewall
  - enable_flow_logs() → auditoría de tráfico

### Subnet
- **Identidad**: Subnet ID (`subnet-xxxxx`)
- **Atributos**:
  - vpc_id: UUID
  - availability_zone: "us-south-1a" | "us-south-1b"
  - cidr_block: "10.0.1.0/24" (público) | "10.0.10.0/24" (privado)
  - map_public_ip_on_launch: true (solo público)
  - type: "PUBLIC" | "PRIVATE"
- **Comportamientos**:
  - enable_flow_logs()
  - attach_route_table()
  - validate_cidr_no_overlap()

### SecurityGroup
- **Identidad**: SG ID (`sg-xxxxx`)
- **Atributos**:
  - vpc_id: UUID
  - name: "alb-sg" | "ecs-sg" | "rds-sg" | "redis-sg"
  - description: string
  - rules: List[SecurityGroupRule]
  - tags: {Name, Service}
- **Comportamientos**:
  - add_ingress_rule(port, protocol, source)
  - add_egress_rule(port, protocol, destination)
  - validate_no_public_db_access()

### RDSInstance
- **Identidad**: DB Instance Identifier (`ticketdesk-prod`)
- **Atributos**:
  - instance_class: "db.t3.small"
  - engine: "postgres"
  - allocated_storage: 100 (GB)
  - multi_az: true
  - storage_encrypted: true
  - backup_retention_period: 30 (days)
  - password: AWS Secrets Manager reference
  - availability_zones: ["us-south-1a", "us-south-1b"]
- **Comportamientos**:
  - create_database()
  - enable_encryption()
  - create_automated_backup()
  - enable_monitoring()
  - test_connectivity()

### ElastiCacheInstance
- **Identidad**: Cache Cluster ID (`ticketdesk-redis`)
- **Atributos**:
  - node_type: "cache.t3.micro"
  - engine: "redis"
  - cache_node_type: "cache.t3.micro"
  - num_cache_nodes: 1
  - parameter_group_name: "default.redis7"
  - at_rest_encryption_enabled: true
  - in_transit_encryption_enabled: true
  - auth_token: AWS Secrets Manager reference
  - maxmemory_policy: "allkeys-lru"
- **Comportamientos**:
  - create_cache_cluster()
  - enable_encryption()
  - configure_eviction_policy()
  - enable_monitoring()
  - test_connectivity()

### ECSCluster
- **Identidad**: Cluster ARN (`arn:aws:ecs:us-south-1:XXX:cluster/ticketdesk`)
- **Atributos**:
  - cluster_name: "ticketdesk-prod"
  - capacity_providers: ["AUTOSCALING", "FARGATE"]
  - default_capacity_provider_strategy: {capacity_provider: "AUTOSCALING", weight: 100}
  - container_insights: "enabled"
  - log_group_name: "/aws/ecs/ticketdesk"
- **Comportamientos**:
  - register_task_definition() → FastAPI + Next.js task definitions
  - create_service() → launch tasks
  - update_scaling_policy()
  - monitor_resource_utilization()

### S3Bucket
- **Identidad**: Bucket Name (`ticketdesk-transcriptions-prod`)
- **Atributos**:
  - region: "us-south-1"
  - versioning_enabled: true
  - server_side_encryption: "aws:kms"
  - kms_key_id: AWS KMS key reference
  - lifecycle_rules: [delete after 90 days for personal data, archive audit logs]
  - public_access_block: all BLOCK
  - bucket_policy: deny unencrypted uploads
- **Comportamientos**:
  - create_bucket()
  - enable_encryption()
  - enable_versioning()
  - create_lifecycle_policy()
  - enable_access_logging()

### ECRRepository
- **Identidad**: Repository URI (`XXX.dkr.ecr.us-south-1.amazonaws.com/ticketdesk-backend`)
- **Atributos**:
  - repository_name: "ticketdesk-backend" | "ticketdesk-frontend"
  - image_scan_on_push: true
  - encryption_configuration: "KMS"
  - lifecycle_policy: keep last 10 images
- **Comportamientos**:
  - push_image(tag)
  - scan_for_vulnerabilities()
  - enforce_lifecycle_policy()

### CloudWatchLogGroup
- **Identidad**: Log Group Name (`/aws/ecs/ticketdesk/backend`)
- **Atributos**:
  - retention_in_days: 30
  - kms_key_id: AWS KMS key reference
  - metric_filters: [error_count, latency_p99, etc.]
- **Comportamientos**:
  - create_log_group()
  - set_retention()
  - create_metric_filters()
  - create_alarms()

### DNSRecord
- **Identidad**: DNS Name (`api.ticketdesk.com` | `www.ticketdesk.com`)
- **Atributos**:
  - zone_id: Route53 Zone ID
  - name: FQDN
  - type: "A" | "CNAME"
  - alias_target: ALB ARN
  - evaluate_target_health: true
  - ttl: 60 (seconds)
- **Comportamientos**:
  - create_record()
  - validate_dns_propagation()
  - enable_health_checks()

---

## Value Objects

### CIDRBlock
- **Valor encapsulado**: CIDR notation string (e.g., "10.0.0.0/16")
- **Reglas de validación**:
  - RFC 4632 compliant
  - No overlaps con otros CIDRs en el mismo VPC
  - Máscara válida (/8 a /28)

### SecurityGroupRule
- **Valor encapsulado**: {protocol, port_range, source/destination, description}
- **Reglas de validación**:
  - Protocol: tcp, udp, icmp, -1 (all)
  - Port range: 0-65535, o -1 (all)
  - Source/destination: CIDR, SG ID, o IP
  - Ninguna regla permite 0.0.0.0/0 a base de datos (DB_PORT)

### DatabasePassword
- **Valor encapsulado**: String bcrypt-hashed, min 12 chars, alphanumeric + special
- **Reglas de validación**:
  - Nunca almacenado en plaintext
  - Rotación recomendada c/90 días
  - Stored en AWS Secrets Manager, nunca en código
  - Access solo vía IAM roles

### AWSKMSKeyReference
- **Valor encapsulado**: KMS Key ID (arn:aws:kms:region:account:key/xxxxx)
- **Reglas de validación**:
  - Key exists en AWS account
  - Key policy permite acceso a ECS/RDS/Redis/S3
  - Key rotation enabled

### ALBHealthCheckConfig
- **Valor encapsulado**: {path, port, protocol, interval_seconds, timeout_seconds, healthy_threshold, unhealthy_threshold}
- **Reglas de validación**:
  - path: /health, /health/ready
  - protocol: HTTP, HTTPS
  - interval: 30 segundos (recomendado)
  - healthy_threshold >= 2
  - unhealthy_threshold >= 3

### DockerImage
- **Valor encapsulado**: ECR image URI (XXX.dkr.ecr.region.amazonaws.com/repo:tag)
- **Reglas de validación**:
  - Imagen debe existir en ECR
  - Tag no puede ser "latest" en producción
  - Imagen debe pasar security scan (no vulnerabilidades críticas)

### GitHubActionsSecret
- **Valor encapsulado**: AWS credential (access key + secret)
- **Reglas de validación**:
  - Stored como GitHub repo secret
  - Access restringido a workflows (CI/CD)
  - Rotación c/90 días

---

## Aggregates

### AwsInfrastructureAggregate
- **Raíz**: VirtualPrivateCloud (VPC)
- **Incluye**:
  - Subnets (públicas y privadas)
  - Security Groups (ALB, ECS, RDS, Redis)
  - Internet Gateway + NAT Gateway
  - Route Tables (público, privado)
  - VPC Flow Logs
  - Network ACLs
- **Invariantes**:
  - VPC existe antes de cualquier subnet
  - Subnets en AZs diferentes (multi-AZ para HA)
  - Security groups no permiten acceso no autorizado a DB

### DataStorageAggregate
- **Raíz**: RDSInstance (PostgreSQL)
- **Incluye**:
  - Database (9 tables según Inception)
  - ElastiCacheInstance (Redis)
  - S3Buckets (transcriptions, audit logs, knowledge base)
  - Encryption keys (KMS)
  - Backup & restore policies
- **Invariantes**:
  - RDS multi-AZ habilitado (failover < 2 min)
  - Redis y RDS en diferentes subnets privadas
  - Todos los datos encriptados en tránsito (TLS) y en reposo (KMS)

### ContainerOrchestrationAggregate
- **Raíz**: ECSCluster
- **Incluye**:
  - Task definitions (FastAPI, Next.js)
  - Services (backend, frontend)
  - Auto-scaling policies
  - Load Balancer (ALB)
  - Health checks
  - ECR repositories
  - CloudWatch logs
- **Invariantes**:
  - Tasks mínimo 2 (HA)
  - Tasks máximo 10 (costo control)
  - Auto-scaling basado en CPU/memoria (>70% scale up, <30% scale down)
  - Health checks fallan → task replacement automático

### MonitoringObservabilityAggregate
- **Raíz**: CloudWatchLogGroup
- **Incluye**:
  - Log groups (ECS, RDS, Lambda, API Gateway)
  - Metric filters (error rate, latency, etc.)
  - Alarms (SNS notifications)
  - Dashboards (real-time visualization)
  - Logs retention policies (30 días prod, 7 años audit logs)
- **Invariantes**:
  - Todos los servicios envían logs a CloudWatch
  - Alarms críticas → SNS → email a on-call engineer
  - Logs encrypted con KMS
  - Audit logs nunca se borran (7 años LGPD)

### DNSAndCertificatesAggregate
- **Raíz**: DNSRecord
- **Incluye**:
  - Route53 hosted zone
  - DNS records (A, CNAME, MX)
  - TLS certificates (ACM)
  - Health checks (ALB)
  - TTL policies
- **Invariantes**:
  - HTTPS obligatorio (TLS 1.3 mínimo)
  - Certificados válidos y auto-renovados
  - DNS resolution < 100ms (cached)

---

**Artefacto generado para**: Unit 1 - Infraestructura  
**Fecha**: 2026-05-27  
**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction - Estación 5, Actividad 1

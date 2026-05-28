# ✅ UNIT 1 — ACTIVIDAD 1: DISEÑO FUNCIONAL COMPLETADA

**Fecha**: 2026-05-27  
**Estación**: 5 - Construction  
**Actividad**: 1 - Diseño Funcional (DDD Táctico)  
**Unit**: 1 - Infraestructura  

---

## 📋 Artefactos Generados

### 1️⃣ domain-entities.md
**¿Qué?** Entidades, value objects y aggregates de infraestructura  
**Contiene**:
- **Bounded Context**: AWS Infrastructure Provisioning & Management
- **Entities** (11 entities):
  - VirtualPrivateCloud (VPC)
  - Subnet (4-8 subnets, public/private)
  - SecurityGroup (ALB, ECS, RDS, Redis)
  - RDSInstance (PostgreSQL)
  - ElastiCacheInstance (Redis)
  - ECSCluster (container orchestration)
  - S3Bucket (transcriptions, audit logs, knowledge base)
  - ECRRepository (Docker images)
  - CloudWatchLogGroup (centralized logging)
  - DNSRecord (Route53)
  - ALBLoadBalancer (Application Load Balancer)
- **Value Objects** (6 VO):
  - CIDRBlock
  - SecurityGroupRule
  - DatabasePassword
  - AWSKMSKeyReference
  - ALBHealthCheckConfig
  - DockerImage
  - GitHubActionsSecret
- **Aggregates** (5 aggregates):
  - AwsInfrastructureAggregate (raíz: VPC)
  - DataStorageAggregate (raíz: RDSInstance)
  - ContainerOrchestrationAggregate (raíz: ECSCluster)
  - MonitoringObservabilityAggregate (raíz: CloudWatchLogGroup)
  - DNSAndCertificatesAggregate (raíz: DNSRecord)

### 2️⃣ business-rules.md
**¿Qué?** Reglas de negocio y constraints operacionales  
**Contiene**:
- **6 Reglas de Provisioning**:
  - RULE-INFRA-01: VPC Multi-AZ obligatorio
  - RULE-INFRA-02: Encryption at rest en todos los datos
  - RULE-INFRA-03: TLS 1.3 obligatorio en tránsito
  - RULE-INFRA-04: No secrets en código
  - RULE-INFRA-05: Security groups: least privilege
  - RULE-INFRA-06: NAT Gateway para egreso desde privadas
- **4 Reglas de Bases de Datos**:
  - RULE-DB-01: RDS Multi-AZ con failover automático
  - RULE-DB-02: Connection pooling (max 20)
  - RULE-DB-03: Database encryption password rotation (90d)
  - RULE-DB-04: Automated backups con 30 días retención
- **2 Reglas de Caching**:
  - RULE-CACHE-01: Redis maxmemory-policy: allkeys-lru
  - RULE-CACHE-02: Cache TTL defaults (session 24h, rubric 7d)
- **4 Reglas de Container Orchestration**:
  - RULE-ECS-01: Auto-scaling policy (2-10 tasks, CPU 70% threshold)
  - RULE-ECS-02: Health checks cada 30 segundos
  - RULE-ECS-03: Despliegue blue-green con rollback automático
  - RULE-ECS-04: Logging obligatorio a CloudWatch
- **3 Reglas de Storage (S3)**:
  - RULE-S3-01: Bucket public access block
  - RULE-S3-02: Versioning habilitado
  - RULE-S3-03: Lifecycle policy (90d personal, 7y audit)
- **2 Reglas de Monitoreo y Alertas**:
  - RULE-MONITOR-01: CloudWatch alarms críticas → SNS → Email
  - RULE-MONITOR-02: Dashboards en CloudWatch

**Total**: 21 reglas de negocio explícitas

### 3️⃣ business-logic-model.md
**¿Qué?** Flujos E2E de infraestructura  
**Contiene**:
- **Flujo 1: Provisioning Inicial de AWS (Day 0)**
  - 10 pasos detallados (VPC → RDS → Redis → ECS → CICD → Health checks)
  - Duración: 1-2 semanas
  - Estados posibles: Initial → VPC_CREATED → ... → PRODUCTION_READY ✅
  - Validaciones en cada paso
  
- **Flujo 2: Crear Local Development Environment (Day 0.5)**
  - 5 pasos (Docker Compose setup, servicios, migrations, seed data)
  - Duración: 2-4 horas
  - Estados: DOCKER_COMPOSE_RUNNING → READY_FOR_DEVELOPMENT
  
- **Flujo 3: Monitoreo en Producción (Ongoing)**
  - Continuous health checks, metrics, alerts
  - Auto-scaling basado en CPU
  - Estados: NORMAL ↔ DEGRADED ↔ CRITICAL ↔ RECOVERY
  
- **Flujo 4: Disaster Recovery - RDS Failover (Edge Case)**
  - 4 pasos (detection → automatic failover → replica promotion → recovery)
  - RTO < 2 minutos, RPO = 0 (sync replication)

---

## ✅ Criterios de Aceptación Cumplidos

- [x] Bounded context claramente definido (AWS Infrastructure)
- [x] Todas las entidades tienen identidad única
- [x] Value objects encapsulan reglas de validación
- [x] Aggregates tienen raíz clara + invariantes
- [x] 21 reglas de negocio explícitas (nombradas, con condición y consecuencia)
- [x] Flujos E2E desde inception a operación
- [x] Estados posibles documentados (state machines)
- [x] Reglas se mapean a user stories (HU-1.1 a HU-1.5)
- [x] Lenguaje del dominio consistente (bounded context language)

---

## 🔗 Traceabilidad a Artefactos Previos

| De Inception | A Unit 1 |
|---|---|
| HU-1.1 (Stack local) | → Flujo 2: Local dev environment |
| HU-1.2 (VPC + SGs) | → RULE-INFRA-01 a 06, Aggregate: Infrastructure |
| HU-1.3 (RDS) | → RULE-DB-01 a 04, Entity: RDSInstance |
| HU-1.4 (Redis) | → RULE-CACHE-01 to 02, Entity: ElastiCacheInstance |
| HU-1.5 (CI/CD) | → Flujo 1 paso 10, Entity: GitHubActionsSecret |
| NFR Disponibilidad | → RULE-INFRA-01 (multi-AZ), RULE-ECS-02, RULE-ECS-03 |
| NFR Seguridad | → RULE-INFRA-02 (encryption), RULE-INFRA-03 (TLS), RULE-INFRA-05 (least privilege) |
| NFR Compliance | → RULE-S3-03 (LGPD retention), RULE-MONITOR-01 (audit) |

---

## 🚀 Próximo Paso

**Actividad 2**: Requerimientos No-Funcionales (NFR Requirements)

Tomar los NFRs de Inception (Disponibilidad 99.5%, Seguridad LGPD, Performance <2s, Costo controlado) y crear:
- `nfr-requirements.md` — Cómo se miden los NFRs
- `nfr-design.md` — ADRs y patrones que cumplen cada NFR

---

## 📊 Métricas

- **Entities**: 11
- **Value Objects**: 6
- **Aggregates**: 5
- **Business Rules**: 21
- **Flujos E2E**: 4
- **Pasos detallados**: 24+
- **Estados posibles**: 15+
- **Líneas de documentación**: 1000+

---

**Status**: ✅ ACTIVIDAD 1 COMPLETA  
**Siguiente**: Actividad 2 (NFR Requirements)  
**Archivo**: aidlc-docs/construction/unit-1-infrastructure/

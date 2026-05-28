# Unit 1: Infraestructura (Terraform) — Actividad 3: Decisiones de Arquitectura (ADR)

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 1 - Infraestructura (Terraform)  
**Actividad**: 3 - Decisiones Arquitectura (ADR)  
**Fecha**: 2026-05-27  

---

## 🎯 ADR-UNIT1-001: Terraform Modules vs CloudFormation vs CDK

**Estado**: ✅ ACEPTADA

### Opciones Evaluadas

**Opción 1: Terraform Modules** ✅ ELEGIDA
- ✅ HCL legible, versionable en git
- ✅ Multi-cloud support (no lock-in AWS)
- ✅ Módulos reutilizables
- ✅ Comunidad grande (registry)

**Opción 2: CloudFormation**
- ✅ AWS-native, soporte oficial
- ❌ YAML verboso, difícil leer
- ❌ Cambios demorados

**Opción 3: AWS CDK (Python)**
- ✅ Lenguaje conocido (Python)
- ❌ Compila a CloudFormation
- ❌ Curva aprendizaje

### Decisión

**✅ Terraform Modules + Remote State (S3 + DynamoDB)**

---

## 🎯 ADR-UNIT1-002: Single Region vs Multi-Region DR

**Estado**: ✅ ACEPTADA

### Contexto

Costos 2x más multi-region. Necesita <1h RTO.

### Opciones

**Opción 1: Single Region + RDS Read Replica (otro region)** ✅ ELEGIDA
- ✅ RTO <1h (manual failover)
- ✅ Costo contenido
- ❌ No 100% automated

**Opción 2: Full Multi-Region (active-active)**
- ✅ Failover automático
- ❌ Costo 2x
- ❌ Sincronización datos compleja

### Decisión

**✅ us-east-1 primary + us-west-2 standby (manual failover)**

---

## 🎯 ADR-UNIT1-003: Monolith vs Microservices Infrastructure

**Estado**: ✅ ACEPTADA

### Contexto

Cada unit puede escalar independiente.

### Opciones

**Opción 1: Separate ECS Services (per Unit)** ✅ ELEGIDA
- ✅ Escalado independiente
- ✅ Despliegue aislado
- ✅ Managed failure scope

**Opción 2: Single monolith container**
- ❌ Acoplamiento
- ❌ Escalado ineficiente

### Decisión

**✅ 4 servicios ECS separados (backend, botengine, evaluation, compliance)**

---

## 🎯 ADR-UNIT1-004: Terraform State Backend

**Estado**: ✅ ACEPTADA

### Opciones

**Opción 1: S3 + DynamoDB (state lock)** ✅ ELEGIDA
- ✅ Versionado S3
- ✅ Encryption KMS
- ✅ State locking (DynamoDB)
- ✅ $1/mes mínimo

**Opción 2: Terraform Cloud**
- ✅ Remote, seguro
- ❌ Vendor lock-in
- ❌ Costo $30+/mes

### Decisión

**✅ S3 remote state + DynamoDB locking**

---

## 📊 Matriz ADRs

| ADR | Decisión | Alternativa | Razón |
|---|---|---|---|
| ADR-UNIT1-001 | Terraform | CloudFormation | HCL legible, multi-cloud |
| ADR-UNIT1-002 | Single region | Multi-region | RTO <1h, costo controlado |
| ADR-UNIT1-003 | Microservices IaC | Monolith | Escalado independiente |
| ADR-UNIT1-004 | S3 remote state | Terraform Cloud | Control + costo bajo |

---

**Generado**: 2026-05-27  
**Unit**: 1 - Infraestructura (Terraform)  
**Actividad**: 3 - Decisiones Arquitectura  
**Estado**: ✅ COMPLETADA

# Análisis de Atributos de Calidad Críticos — TicketDesk Enterprise v1.0

**Identificación de 3 atributos de calidad más críticos para el MVP**  
**Fecha**: 2026-05-27  
**Basado en**: Artefactos de Inception (Requirements, Architecture, NFR Design)

---

## 📊 RESUMEN EJECUTIVO

| Atributo | Crítico | Riesgo | Táctica | Verificación |
|----------|---------|--------|---------|--------------|
| **1. Confiabilidad (Availability)** | ⭐⭐⭐⭐⭐ | System down = HR workflow stalled | Multi-AZ + Circuit Breaker | SLA 99.5%, Failover tests |
| **2. Seguridad (LGPD Compliance)** | ⭐⭐⭐⭐⭐ | Data breach = Legal liability + Reputation | Encryption + Audit Logs + RBAC | Penetration tests, Compliance audit |
| **3. Eficiencia de Costos (Performance)** | ⭐⭐⭐⭐☆ | Claude API costs spiral = Unsustainable | Caching + Prompt Optimization | Token usage monitoring, Cost/evaluation |

---

## 🔴 ATRIBUTO 1: CONFIABILIDAD (AVAILABILITY)

### ¿Por Qué Es Crítico Para Este Producto?

#### Análisis del Impacto Operacional

```
Scenario 1: Sistema cae durante screening candidato
├─ Candidato pierde progreso (frustración)
├─ Candidato abandona proceso (churn)
├─ HR debe reintentar (overhead operacional)
└─ Costo por candidato: $16.67 → Pérdida de ROI

Scenario 2: Dashboard recruiter no responde
├─ Reclutador no puede acceder a cola HITL
├─ Evaluaciones se acumulan (bottleneck)
├─ Decisiones se retrasan (hiring velocity baja)
└─ Impacto negocio: Pérdida de días en hiring

Scenario 3: Database down (sin failover)
├─ Todos los services fallan (cascading failure)
├─ Candidatos no pueden acceder (churn)
├─ HR pierde visibilidad (decisiones ciegas)
└─ Recuperación >30 minutos → SLA breach
```

#### Requisito Extractado de Artefactos
- **From requirements.md**: "99.5% uptime SLA (43.8 minutos downtime/mes)"
- **From execution-plan.md**: "Unit 1 critical path (blocks all other units)"
- **From nfr-design.md**: "RTO <15 min, RPO <5 min" + "Multi-AZ enabled"

#### Por Qué Específicamente Este Producto
- ✅ **Real-time**: Candidatos esperando respuestas (no es batch processing)
- ✅ **Revenue-critical**: Cada minuto de downtime = candidatos sin evaluar
- ✅ **Multi-AZ requirement**: Brasil LGPD exige geographical redundancy
- ✅ **External dependency risk**: Claude API puede fallar → Sistema debe degradarse gracefully

---

### Táctica 1: Multi-AZ Failover + Health Checks

**Patrón**: Availability Pattern + Health Check + Circuit Breaker

```yaml
Arquitectura:

┌─────────────────────────────────────┐
│         ALB (Multi-AZ)              │
│  ├─ us-south-1a (primary)           │
│  └─ us-south-1b (secondary)         │
│      (automatic failover)            │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────┐   ┌────────┐
│ECS-1a  │   │ECS-1b  │
│Backend │   │Backend │
│(2 tasks)   │(2 tasks)
└──┬─────┘   └────┬──┘
   │              │
   └──────┬───────┘
          │
    ┌─────┴─────┐
    │             │
    ▼             ▼
┌──────────┐ ┌──────────┐
│RDS-Prim  │ │RDS-Stby  │
│(1a)      │ │(1b)      │
│Sync Repl │ │          │
└──────────┘ └──────────┘
```

**Implementación Específica**:

```python
# src/infrastructure/health_check.py
from fastapi import FastAPI, HTTPException
import asyncio

app = FastAPI()

class HealthCheckService:
    def __init__(self, db_pool, redis_pool, claude_client):
        self.db = db_pool
        self.redis = redis_pool
        self.claude = claude_client
    
    async def check_critical_systems(self) -> dict:
        """Verifica salud de sistemas críticos"""
        results = {
            "database": await self._check_database(),
            "redis": await self._check_redis(),
            "claude_api": await self._check_claude(),
            "timestamp": datetime.utcnow().isoformat()
        }
        return results
    
    async def _check_database(self) -> str:
        """Health check para PostgreSQL"""
        try:
            async with self.db.connect() as conn:
                await asyncio.wait_for(
                    conn.execute("SELECT 1"),
                    timeout=2.0  # 2s timeout
                )
            return "healthy"
        except Exception as e:
            logger.error(f"DB health check failed: {e}")
            return "unhealthy"
    
    async def _check_redis(self) -> str:
        """Health check para Redis"""
        try:
            async with asyncio.timeout(2.0):
                ping = await self.redis.ping()
            return "healthy" if ping else "unhealthy"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return "unhealthy"
    
    async def _check_claude(self) -> str:
        """Health check para Claude API"""
        try:
            # Lightweight test call (~0.1s, ~50 tokens)
            async with asyncio.timeout(5.0):
                response = await self.claude.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "OK"}]
                )
            return "healthy"
        except Exception as e:
            logger.warning(f"Claude health check failed: {e}")
            # IMPORTANT: Claude API down doesn't mean app is down
            # Return "degraded" not "unhealthy"
            return "degraded"

@app.get("/health")
async def health_check(health_service: HealthCheckService = Depends()):
    """
    ALB health check endpoint
    Returns 200 if ready, 503 if not
    """
    status = await health_service.check_critical_systems()
    
    # Determine overall health
    db_ok = status["database"] == "healthy"
    redis_ok = status["redis"] == "healthy"
    
    if db_ok and redis_ok:
        return {"status": "healthy", "details": status}
    else:
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy",
            "details": status
        })

@app.get("/health/ready")
async def readiness_check(health_service: HealthCheckService = Depends()):
    """
    Readiness probe (for ECS service deployment)
    Returns 200 only if ALL systems healthy
    """
    status = await health_service.check_critical_systems()
    
    if all(v == "healthy" for v in status.values()):
        return {"ready": True}
    else:
        raise HTTPException(status_code=503, detail={"ready": False})
```

**Configuración ALB + ECS**:

```yaml
# ECS Service Deployment Configuration
DesiredCount: 2  # Mínimo 2 tasks (1 per AZ)

DeploymentConfiguration:
  MinimumHealthyPercent: 100  # CRITICAL: Mantener 100% mientras hay 2+ tasks
  MaximumPercent: 200         # Allow 4 tasks during deployment
  DeploymentCircuitBreaker:
    Enable: true
    Rollback: true            # Auto-rollback si new tasks fail

LoadBalancers:
  TargetGroup:
    HealthCheckProtocol: HTTP
    HealthCheckPath: /health
    HealthCheckIntervalSeconds: 30
    HealthCheckTimeoutSeconds: 5
    HealthyThresholdCount: 2     # 2 consecutive successes
    UnhealthyThresholdCount: 3   # 3 consecutive failures
    
    # If unhealthy: remove from rotation in 30s (2 checks * 30s interval - 5s)

NetworkConfiguration:
  Subnets:
    - subnet-1a  # Primary
    - subnet-1b  # Secondary (auto-distribution)
```

---

### Táctica 2: Circuit Breaker para Claude API

**Patrón**: Circuit Breaker Pattern (Failover graceful)

**Motivación**: Claude API puede timeout/rate-limit. Sistema debe degrade gracefully sin crash.

```python
# src/infrastructure/circuit_breaker.py
from pybreaker import CircuitBreaker
import asyncio

class ClaudeCircuitBreaker:
    """
    3-state circuit breaker para Claude API
    - CLOSED: Normal operation (requests flow)
    - OPEN: API down (fast-fail, no requests sent)
    - HALF_OPEN: Testing if API recovered (1 request allowed)
    """
    
    def __init__(
        self,
        failure_threshold=5,      # Open after 5 failures
        success_threshold=2,      # Close after 2 successes in HALF_OPEN
        timeout=30,               # Stay OPEN for 30 seconds
    ):
        self.breaker = CircuitBreaker(
            fail_max=failure_threshold,
            reset_timeout=timeout,
            listeners=[self._on_state_change]
        )
        self.success_threshold = success_threshold
        self.successes_in_half_open = 0
    
    def _on_state_change(self, breaker, old_state, new_state):
        """Log state transitions"""
        logger.warning(f"Circuit breaker: {old_state} → {new_state}")
        if new_state.name == "OPEN":
            # Alert ops
            send_alert("Claude API Circuit Breaker OPEN", severity="WARNING")
    
    async def call(self, func, *args, **kwargs):
        """
        Execute func through circuit breaker
        
        Usage:
            response = await breaker.call(
                client.messages.create,
                model="claude-3-5-sonnet-20241022",
                messages=[...],
                timeout=15
            )
        """
        try:
            # Try calling through circuit breaker
            result = await asyncio.wait_for(
                self._async_call(func, *args, **kwargs),
                timeout=kwargs.get("timeout", 15)
            )
            
            # Success: reset counter
            self.successes_in_half_open = 0
            return result
            
        except asyncio.TimeoutError:
            logger.error("Claude API timeout")
            raise TimeoutError("Claude API did not respond in time")
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    async def _async_call(self, func, *args, **kwargs):
        """Wrapper para llamadas async"""
        if self.breaker.opened:
            raise CircuitBreakerOpen("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self.breaker.call(lambda: None)  # Record success
            return result
        except Exception as e:
            self.breaker.fail(e)  # Record failure, may trigger OPEN
            raise

# Instantiate globally
claude_breaker = ClaudeCircuitBreaker(
    failure_threshold=5,
    reset_timeout=30
)

# Usage in BotEngine
class BotEngine:
    async def process_response(self, session_id, response_text):
        try:
            # Try using Claude API
            next_question = await claude_breaker.call(
                self.claude_client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": response_text}],
                timeout=15
            )
            return {"success": True, "next_question": next_question}
        
        except CircuitBreakerOpen:
            # Circuit breaker is open: API is likely down
            logger.warning("Claude API Circuit Breaker OPEN - using fallback")
            
            # Fallback: Return generic question
            fallback_question = self._get_generic_followup(response_text)
            return {
                "success": False,
                "next_question": fallback_question,
                "is_fallback": True,
                "message": "Service momentarily unavailable. Using fallback question."
            }
        
        except TimeoutError:
            logger.error("Claude API timeout - retrying")
            # Retry logic with exponential backoff (elsewhere)
            raise
```

---

### Verificación: Cómo Validar la Confiabilidad

#### Test 1: Health Check Endpoint Response

```bash
# Test health check returns 200 when healthy
curl -v http://localhost:8000/health
# Expected: HTTP 200, body: {"status": "healthy", ...}

# Test health check returns 503 when DB down
# (simulate by shutting down RDS)
curl -v http://localhost:8000/health
# Expected: HTTP 503, body: {"status": "unhealthy", ...}
```

#### Test 2: Failover Simulation

```bash
# Scenario: Database primary fails, should failover to standby in <2 min

# Step 1: Get baseline latency
ab -n 100 -c 10 http://localhost:8000/api/recruiter/queue
# Expected: p99 latency <300ms

# Step 2: Simulate RDS primary failure
# AWS Console: RDS → Failover database
# (takes ~2 minutes)

# Step 3: Verify service recovers
sleep 120
ab -n 100 -c 10 http://localhost:8000/api/recruiter/queue
# Expected: 
#   - Service available
#   - Latency may spike briefly (connection pool rebuild)
#   - All requests eventually succeed

# Step 4: Verify failover event in logs
aws logs get-log-events \
  --log-group-name /ecs/ticketdesk-backend \
  --log-stream-name {container_id} \
  --start-time $(date -d '5 minutes ago' +%s)000
# Look for: "RDS failover detected" or connection pool reset
```

#### Test 3: Circuit Breaker Activation

```python
# tests/test_circuit_breaker.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Verify circuit breaker opens after N failures"""
    breaker = ClaudeCircuitBreaker(failure_threshold=3, reset_timeout=1)
    
    # Simulate 3 API failures
    with patch.object(claude_client, 'messages') as mock:
        mock.create.side_effect = TimeoutError("API timeout")
        
        for i in range(3):
            with pytest.raises(TimeoutError):
                await breaker.call(mock.create)
        
        # After 3 failures, circuit should be OPEN
        assert breaker.breaker.opened
        
        # Next call should fail fast without hitting API
        with pytest.raises(CircuitBreakerOpen):
            await breaker.call(mock.create)
        
        # Verify mock.create was only called 3 times (not 4)
        assert mock.create.call_count == 3

@pytest.mark.asyncio
async def test_circuit_breaker_returns_fallback():
    """Verify system gracefully handles circuit breaker open"""
    bot_engine = BotEngine(claude_breaker=breaker)
    breaker.breaker.open()  # Force OPEN state
    
    response = await bot_engine.process_response(
        session_id="session-123",
        response_text="Test response"
    )
    
    assert response["success"] == False
    assert response["is_fallback"] == True
    assert "fallback" in response["next_question"].lower()
```

#### Test 4: ECS Auto-Scaling Under Load

```bash
# Load test to verify auto-scaling maintains availability

# Step 1: Establish baseline (2 tasks running)
watch -n 5 'aws ecs describe-services \
  --cluster ticketdesk-prod \
  --services backend-service \
  --query "services[0].{Running:runningCount,Desired:desiredCount}"'

# Step 2: Apply load (1000 req/sec for 5 min)
ab -n 300000 -c 100 -t 300 http://localhost:8000/api/recruiter/queue

# Step 3: Watch auto-scaling
# Expected:
#   - CPU utilization climbs to >70%
#   - After 2 minutes: task count increases (4, 6, 8...)
#   - Latency remains <3s (doesn't degrade)
#   - Requests don't fail (0% error rate)

# Step 4: After load stops
# Expected:
#   - CPU drops below 30%
#   - After 5 min: task count scales back down to 2
```

#### Test 5: Uptime Measurement (Synthetic Monitoring)

```python
# src/monitoring/uptime_monitor.py
import asyncio
from datetime import datetime, timedelta

class UptimeMonitor:
    """Continuous uptime monitoring (for SLA validation)"""
    
    def __init__(self, check_interval=60):  # Every 1 minute
        self.check_interval = check_interval
        self.checks_total = 0
        self.checks_success = 0
        self.downtime_events = []
    
    async def run_continuous_monitoring(self):
        """Run uptime checks continuously"""
        while True:
            try:
                # Hit /health endpoint
                response = await asyncio.wait_for(
                    self._http_get("http://localhost:8000/health"),
                    timeout=5.0
                )
                
                if response.status == 200:
                    self.checks_success += 1
                else:
                    self.downtime_events.append({
                        "timestamp": datetime.utcnow(),
                        "status_code": response.status
                    })
                
                self.checks_total += 1
                
                # Calculate uptime percentage
                uptime_pct = (self.checks_success / self.checks_total) * 100
                logger.info(f"Uptime: {uptime_pct:.2f}% ({self.checks_total} checks)")
                
                # Target: 99.5% = ~1 failure per 200 checks
                if uptime_pct < 99.5:
                    send_alert(f"Uptime below SLA: {uptime_pct:.2f}%")
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.TimeoutError:
                self.downtime_events.append({
                    "timestamp": datetime.utcnow(),
                    "reason": "health_check_timeout"
                })
    
    def get_uptime_report(self, time_period=timedelta(days=30)):
        """Generate uptime report for given period"""
        recent_checks = [c for c in self.checks_total 
                        if datetime.utcnow() - c < time_period]
        recent_success = len([c for c in recent_checks if c.status == 200])
        
        uptime_pct = (recent_success / len(recent_checks)) * 100
        downtime_minutes = ((1 - uptime_pct/100) * time_period.total_seconds()) / 60
        
        return {
            "period": time_period,
            "uptime_percentage": uptime_pct,
            "total_checks": len(recent_checks),
            "failed_checks": len(recent_checks) - recent_success,
            "downtime_minutes": downtime_minutes,
            "allowed_downtime_minutes": (43.8 if time_period.days == 30 else 0),
            "sla_met": uptime_pct >= 99.5
        }

# Run in background
monitor = UptimeMonitor()
asyncio.create_task(monitor.run_continuous_monitoring())
```

---

## 🔒 ATRIBUTO 2: SEGURIDAD (LGPD COMPLIANCE)

### ¿Por Qué Es Crítico Para Este Producto?

#### Riesgo Regulatorio y Legal

```
LGPD (Lei Geral de Proteção de Dados) — Regulação Brasileña Equivalente a GDPR

Multas por Violaciones:
├─ Hasta R$50 millones (USD $10M+) por violación
├─ O 2% de ingresos anuales (lo que sea mayor)
└─ Ejemplos reales: Google (Brasil) multa R$10M+ por privacidad

Data Handled:
├─ Nombre candidato
├─ Email
├─ Respuestas screening (conversación IA - datos comportamentales sensibles)
├─ Evaluación scores
├─ Decisión final (impacta vida candidato)
└─ IP address + user agent (tracking)

Requisitos LGPD:
├─ Consentimiento explícito (no pre-checked boxes)
├─ Derecho al olvido (derecho a eliminación)
├─ Portabilidad datos (data export)
├─ Auditoría inmutable (proof de procesamiento)
├─ Retencion limitada (no guardar indefinidamente)
├─ Encriptación (datos en reposo + tránsito)
└─ Confidencialidad (acceso restringido)
```

#### Análisis de Criticidad

```
Impacto Operacional:
├─ Si no auditable: HR no puede demostrar compliance
├─ Si data breach: Reputación destrozada + multa legal
├─ Si no consentimiento registrado: Ilegal procesar datos
├─ Si no poder deletear: Violación derecho al olvido
└─ Si no encriptado: Cumplimiento insuficiente

Requisito Extractado de Artefactos:
├─ From requirements.md: "LGPD compliance (Brazil data residency)"
├─ From functional-design.md: "Append-only audit_logs table"
├─ From nfr-design.md: "Encryption at rest + in transit, Consent management"
├─ From component-methods.md: "ComplianceService.register_consent()"
└─ From infrastructure-design.md: "KMS encryption, Secrets Manager"
```

---

### Táctica 1: Append-Only Audit Logs + Immutability

**Patrón**: Event Sourcing + Immutable Audit Trail

**Motivación**: LGPD exige demostración de compliance. NO actualizar/eliminar histórico.

```sql
-- src/migrations/001_audit_logs.sql
-- Tabla APPEND-ONLY (NO UPDATE/DELETE permitido a nivel app)

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- What happened
    event_type VARCHAR(100) NOT NULL,  -- SCREENING_STARTED, DECISION_RECORDED, etc.
    
    -- Who (actor)
    actor_id UUID,  -- recruiter_id (null si sistema)
    actor_role VARCHAR(50),  -- RECRUITER, SYSTEM, ADMIN
    
    -- What entity affected
    subject_id UUID,  -- candidate_id, session_id
    subject_type VARCHAR(50),  -- CANDIDATE, SESSION, EVALUATION
    
    -- Event details (JSON for flexibility)
    event_details JSONB NOT NULL,  -- {decision: "APPROVE", score: 85, ...}
    
    -- Request context (for security investigation)
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    
    -- Timestamp (immutable proof of when)
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexing for queries
    CONSTRAINT audit_logs_event_type_idx ON (event_type, created_at DESC),
    CONSTRAINT audit_logs_subject_idx ON (subject_id, subject_type),
    CONSTRAINT audit_logs_timestamp_idx ON (created_at)
);

-- Constraints a nivel BD (no se puede actualizar/borrar)
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_logs_append_only ON audit_logs
    USING (true)  -- SELECT allowed
    WITH CHECK (false);  -- INSERT/UPDATE/DELETE forbidden

-- Tabla de eliminaciones (para cumplir "derecho al olvido" LGPD)
-- En lugar de eliminar datos, marcar como deleted
CREATE TABLE soft_deletions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL,
    deletion_requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deletion_approved_at TIMESTAMPTZ,  -- null hasta que se apruebe
    hard_delete_scheduled_for TIMESTAMPTZ NOT NULL,  -- 90 días después
    created_by_actor_id UUID NOT NULL,
    reason TEXT,
    
    -- Auditoría
    CONSTRAINT fk_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);
```

**Implementación en Código**:

```python
# src/components/compliance_service/audit_logger.py
from sqlalchemy import insert
from datetime import datetime

class AuditLogger:
    """Registra eventos inmutablemente a audit_logs"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def log_event(
        self,
        event_type: str,
        subject_id: str,
        subject_type: str,
        event_details: dict,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> UUID:
        """
        Log evento inmutablemente.
        Nota: Esta tabla NO permite UPDATE/DELETE (garantizado por RLS)
        """
        
        # Validar event_type es conocido (enum)
        ALLOWED_EVENTS = {
            "SCREENING_STARTED",
            "CANDIDATE_RESPONSE_SUBMITTED",
            "EVALUATION_COMPLETE",
            "DECISION_RECORDED",
            "CONSENT_WITHDRAWN",
            "DATA_EXPORT_REQUESTED",
            "DELETION_REQUESTED",
            "SESSION_ABANDONED",
            "SESSION_RESUMED"
        }
        assert event_type in ALLOWED_EVENTS, f"Unknown event type: {event_type}"
        
        # Validar actor_role si present
        if actor_role:
            ALLOWED_ROLES = {"RECRUITER", "ADMIN", "SYSTEM"}
            assert actor_role in ALLOWED_ROLES, f"Unknown role: {actor_role}"
        
        try:
            # Insert ÚNICO (no update)
            stmt = insert(AuditLog).values(
                event_type=event_type,
                subject_id=subject_id,
                subject_type=subject_type,
                event_details=event_details,
                actor_id=actor_id,
                actor_role=actor_role,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                created_at=datetime.utcnow()
            ).returning(AuditLog.id)
            
            result = await self.db.execute(stmt)
            audit_id = result.scalar_one()
            
            logger.info(f"Audit log created: {audit_id} [{event_type}]")
            return audit_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # CRITICAL: If audit fails, entire transaction fails
            # (don't process without proof in audit trail)
            raise
    
    async def log_screening_started(self, session_id: str, candidate_id: str):
        """Log: screening iniciado"""
        return await self.log_event(
            event_type="SCREENING_STARTED",
            subject_id=session_id,
            subject_type="SESSION",
            event_details={
                "candidate_id": candidate_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def log_decision_recorded(
        self,
        session_id: str,
        candidate_id: str,
        decision: str,  # APPROVE, REJECT, PENDING
        recruiter_id: str,
        score: float,
        notes: Optional[str]
    ):
        """Log: decisión reclutador registrada"""
        return await self.log_event(
            event_type="DECISION_RECORDED",
            subject_id=session_id,
            subject_type="SESSION",
            actor_id=recruiter_id,
            actor_role="RECRUITER",
            event_details={
                "candidate_id": candidate_id,
                "decision": decision,
                "score": score,
                "notes": notes,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Uso en HITLService
class HITLService:
    async def process_decision(
        self,
        queue_item_id: str,
        decision: str,
        recruiter_id: str,
        notes: str
    ):
        """Procesa decisión reclutador"""
        
        # Fetch evaluación + contexto
        queue_item = await self.db.get(QueueItem, queue_item_id)
        evaluation = await self.db.get(Evaluation, queue_item.evaluation_id)
        
        # Actualizar BD
        queue_item.status = "DECIDED"
        queue_item.decision = decision
        await self.db.flush()
        
        # **IMPORTANTE**: Log ANTES de commit (para garantizar consistencia)
        await self.audit_logger.log_decision_recorded(
            session_id=evaluation.session_id,
            candidate_id=queue_item.candidate_id,
            decision=decision,
            recruiter_id=recruiter_id,
            score=evaluation.score,
            notes=notes
        )
        
        # Commit (audit log y decisión juntas)
        await self.db.commit()
        
        # Emit event (async, puede fallar sin afectar audit)
        await self.event_bus.emit("recruiter.decision.made", {
            "decision_id": queue_item.id,
            "decision": decision,
            "candidate_id": queue_item.candidate_id
        })
```

---

### Táctica 2: Encriptación + RBAC

**Patrón**: Encryption at Rest (KMS) + Encryption in Transit (TLS) + Role-Based Access Control

```python
# src/infrastructure/encryption.py
import boto3
from cryptography.fernet import Fernet
import os

class EncryptionManager:
    """Maneja encriptación de datos sensibles"""
    
    def __init__(self):
        self.kms_client = boto3.client('kms', region_name='us-south-1')
        # KMS key ARN desde Secrets Manager
        self.kms_key_id = os.getenv('AWS_KMS_KEY_ARN')
    
    async def encrypt_sensitive_field(self, plaintext: str) -> str:
        """
        Encripta campo sensible (candidato nombre, email, respuestas)
        
        Nota: PostgreSQL + AWS KMS maneja encriptación automáticamente
        Este método es para extra-sensitive fields (si necesario)
        """
        response = self.kms_client.encrypt(
            KeyId=self.kms_key_id,
            Plaintext=plaintext.encode('utf-8')
        )
        # Retorna blob encriptado (base64)
        return base64.b64encode(response['CiphertextBlob']).decode('utf-8')
    
    async def decrypt_sensitive_field(self, ciphertext: str) -> str:
        """Desencripta"""
        response = self.kms_client.decrypt(
            CiphertextBlob=base64.b64decode(ciphertext)
        )
        return response['Plaintext'].decode('utf-8')

# src/infrastructure/rbac.py
from enum import Enum
from typing import List

class Role(str, Enum):
    CANDIDATE = "CANDIDATE"
    RECRUITER = "RECRUITER"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"

class Permission(str, Enum):
    # Candidate permissions
    SCREENING_START = "screening:start"
    SCREENING_RESPOND = "screening:respond"
    SCREENING_VIEW_OWN = "screening:view_own"
    
    # Recruiter permissions
    QUEUE_VIEW = "queue:view"
    QUEUE_DECISION = "queue:decision"
    CANDIDATE_VIEW = "candidate:view"
    
    # Admin permissions
    ADMIN_CAMPAIGN_CREATE = "admin:campaign_create"
    ADMIN_CAMPAIGN_DELETE = "admin:campaign_delete"
    ADMIN_USER_MANAGE = "admin:user_manage"
    
    # System permissions
    SYSTEM_AUDIT_READ = "system:audit_read"
    SYSTEM_BATCH_CLEANUP = "system:batch_cleanup"

ROLE_PERMISSIONS = {
    Role.CANDIDATE: [
        Permission.SCREENING_START,
        Permission.SCREENING_RESPOND,
        Permission.SCREENING_VIEW_OWN,
    ],
    Role.RECRUITER: [
        Permission.QUEUE_VIEW,
        Permission.QUEUE_DECISION,
        Permission.CANDIDATE_VIEW,
    ],
    Role.ADMIN: [
        Permission.ADMIN_CAMPAIGN_CREATE,
        Permission.ADMIN_CAMPAIGN_DELETE,
        Permission.ADMIN_USER_MANAGE,
        Permission.QUEUE_VIEW,  # Admins can see everything
        Permission.CANDIDATE_VIEW,
    ],
    Role.SYSTEM: [
        Permission.SYSTEM_AUDIT_READ,
        Permission.SYSTEM_BATCH_CLEANUP,
    ]
}

# src/infrastructure/auth_middleware.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

async def get_current_user(credentials: HTTPAuthCredentials = Depends(HTTPBearer())):
    """
    Extract + validate JWT token
    Returns user info with role + permissions
    """
    token = credentials.credentials
    
    try:
        # Verify JWT signature
        payload = jwt.decode(
            token,
            key=os.getenv("JWT_SECRET"),
            algorithms=["HS256"],
            audience="ticketdesk"
        )
        
        user_id = payload.get("sub")
        user_role = payload.get("role")
        
        if not user_id or not user_role:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {
            "user_id": user_id,
            "role": Role(user_role),
            "permissions": ROLE_PERMISSIONS[Role(user_role)]
        }
        
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

# Guard decorator para endpoints
def require_permission(permission: Permission):
    """Require specific permission to call endpoint"""
    async def check_permission(user = Depends(get_current_user)):
        if permission not in user["permissions"]:
            logger.warning(f"Permission denied: {user['user_id']} tried {permission}")
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission}"
            )
        return user
    return check_permission

# Uso en endpoints
@app.post("/api/recruiter/decision")
async def submit_decision(
    decision: DecisionRequest,
    user = Depends(require_permission(Permission.QUEUE_DECISION))
):
    """Solo RECRUITER role puede llamar"""
    # Process decision...
    pass
```

---

### Táctica 3: Consentimiento Explícito + Data Retention Policy

**Patrón**: Explicit Opt-In + Retention Lifecycle Management

```python
# src/components/compliance_service/consent_manager.py

class ConsentManager:
    """Maneja consentimiento LGPD"""
    
    async def register_consent(
        self,
        candidate_id: str,
        consent_type: str,  # "SCREENING", "DATA_PROCESSING", "EMAIL_MARKETING"
        ip_address: str,
        user_agent: str,
        timestamp: datetime
    ) -> UUID:
        """
        Registra consentimiento explícito (no puede ser pre-checked)
        
        Requisito LGPD: Consentimiento debe ser:
        ├─ Explícito (usuario marca checkbox)
        ├─ Informado (entiende qué consiente)
        ├─ Verificable (guardamos proof)
        └─ Revocable (puede retirar después)
        """
        
        # Validar consentimiento es conocido
        ALLOWED_TYPES = ["SCREENING", "DATA_PROCESSING", "EMAIL_MARKETING"]
        assert consent_type in ALLOWED_TYPES
        
        # Insert consent record
        consent_record = ConsentRecord(
            candidate_id=candidate_id,
            consent_type=consent_type,
            given=True,
            given_at=timestamp,
            ip_address=ip_address,
            user_agent=user_agent,
            withdrawn=False
        )
        self.db.add(consent_record)
        await self.db.flush()
        
        # Generate certificate (PDF proof)
        certificate = await self._generate_consent_certificate(
            candidate_id=candidate_id,
            consent_type=consent_type,
            timestamp=timestamp
        )
        
        # Upload to S3 para auditoría
        s3_key = f"consent-certificates/{candidate_id}/{consent_record.id}.pdf"
        await self._upload_to_s3(s3_key, certificate)
        
        # Update record con S3 URL
        consent_record.certificate_s3_url = s3_key
        await self.db.commit()
        
        # Log to audit_logs
        await self.audit_logger.log_event(
            event_type="CONSENT_RECORDED",
            subject_id=candidate_id,
            subject_type="CANDIDATE",
            event_details={
                "consent_type": consent_type,
                "given": True,
                "certificate_url": s3_key,
                "timestamp": timestamp.isoformat()
            },
            ip_address=ip_address
        )
        
        return consent_record.id
    
    async def withdraw_consent(
        self,
        candidate_id: str,
        consent_type: str,
        request_timestamp: datetime
    ):
        """
        Retira consentimiento (derecho del candidato)
        """
        
        # Marca consentimiento como withdrawn (no delete)
        consent = await self.db.query(ConsentRecord).filter_by(
            candidate_id=candidate_id,
            consent_type=consent_type,
            withdrawn=False
        ).first()
        
        if not consent:
            raise ValueError(f"No active consent found for {candidate_id}")
        
        consent.withdrawn = True
        consent.withdrawn_at = request_timestamp
        await self.db.commit()
        
        # Log withdrawal
        await self.audit_logger.log_event(
            event_type="CONSENT_WITHDRAWN",
            subject_id=candidate_id,
            subject_type="CANDIDATE",
            event_details={
                "consent_type": consent_type,
                "withdrawn_at": request_timestamp.isoformat()
            }
        )
        
        logger.info(f"Consent withdrawn for {candidate_id} - {consent_type}")

class DataRetentionPolicy:
    """Política de retención LGPD"""
    
    RETENTION_POLICIES = {
        "candidate_personal_data": 90,      # 90 días si sin consentimiento activo
        "screening_responses": 90,          # 90 días después de decision
        "evaluations": 730,                 # 2 años (compliance)
        "decisions": 730,                   # 2 años
        "audit_logs": 2555,                 # 7 años (legal requirement)
        "consent_records": 2555,            # 7 años (proof of processing)
        "backups": 30,                      # 30 días
    }
    
    async def cleanup_expired_data(self):
        """
        Background job (ejecuta nightly): elimina datos según política
        """
        
        # 1. Soft-delete candidatos sin consentimiento activo >90 días
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        candidates_to_delete = await self.db.query(Candidate).filter(
            Candidate.created_at < ninety_days_ago,
            ~Candidate.consent_records.any(ConsentRecord.withdrawn == False)
        ).all()
        
        for candidate in candidates_to_delete:
            await self._soft_delete_candidate(candidate.id)
        
        # 2. Hard-delete datos que pasaron 90 días desde soft-delete
        soft_deletions = await self.db.query(SoftDeletion).filter(
            SoftDeletion.hard_delete_scheduled_for <= datetime.utcnow()
        ).all()
        
        for sd in soft_deletions:
            await self._hard_delete_candidate(sd.candidate_id)
        
        logger.info(f"Data cleanup completed: {len(candidates_to_delete)} soft-deletions, {len(soft_deletions)} hard-deletions")
    
    async def _soft_delete_candidate(self, candidate_id: str):
        """Soft delete (mark as deleted, keep for GDPR proof)"""
        candidate = await self.db.get(Candidate, candidate_id)
        candidate.deleted = True
        
        # Schedule hard-delete para 90 días después
        sd = SoftDeletion(
            candidate_id=candidate_id,
            deletion_requested_at=datetime.utcnow(),
            hard_delete_scheduled_for=datetime.utcnow() + timedelta(days=90)
        )
        self.db.add(sd)
        await self.db.commit()
        
        # Log
        await self.audit_logger.log_event(
            event_type="DELETION_SOFT_EXECUTED",
            subject_id=candidate_id,
            subject_type="CANDIDATE",
            event_details={"scheduled_hard_delete": (datetime.utcnow() + timedelta(days=90)).isoformat()}
        )
    
    async def _hard_delete_candidate(self, candidate_id: str):
        """Hard delete (elimina completamente, después de 90 días soft-delete)"""
        # ONLY delete persona data
        # KEEP: audit_logs, consent_records (proof)
        
        # Delete cascading
        await self.db.query(Session).filter_by(candidate_id=candidate_id).delete()
        await self.db.query(ScreeningResponse).filter(
            ScreeningResponse.session_id.in_(
                self.db.query(Session.id).filter_by(candidate_id=candidate_id)
            )
        ).delete()
        await self.db.query(Evaluation).filter(
            Evaluation.response_id.in_(
                self.db.query(ScreeningResponse.id).filter_by(candidate_id=candidate_id)
            )
        ).delete()
        await self.db.query(Candidate).filter_by(id=candidate_id).delete()
        
        await self.db.commit()
        
        # Log
        await self.audit_logger.log_event(
            event_type="DELETION_HARD_EXECUTED",
            subject_id=candidate_id,
            subject_type="CANDIDATE",
            event_details={"deleted_at": datetime.utcnow().isoformat()}
        )
```

---

### Verificación: Cómo Validar Seguridad LGPD

#### Test 1: Audit Logs Immutability

```python
# tests/test_audit_immutability.py
import pytest
from sqlalchemy.exc import IntegrityError

@pytest.mark.asyncio
async def test_audit_logs_cannot_be_updated():
    """Verificar que audit_logs no puede ser actualizado"""
    
    # Insert audit log
    stmt = insert(AuditLog).values(
        event_type="SCREENING_STARTED",
        subject_id="cand-123",
        event_details={"timestamp": now}
    )
    result = await db.execute(stmt)
    audit_id = result.scalar_one()
    
    # Intentar actualizar (debe fallar)
    update_stmt = update(AuditLog).where(
        AuditLog.id == audit_id
    ).values(event_details={"hacked": True})
    
    with pytest.raises(IntegrityError):
        await db.execute(update_stmt)
    
    # Intentar borrar (debe fallar)
    delete_stmt = delete(AuditLog).where(AuditLog.id == audit_id)
    
    with pytest.raises(IntegrityError):
        await db.execute(delete_stmt)
    
    # Verificar original sigue igual
    check = await db.execute(
        select(AuditLog).where(AuditLog.id == audit_id)
    )
    record = check.scalar_one()
    assert record.event_details == {"timestamp": now}
```

#### Test 2: Consent Registration & Withdrawal

```python
@pytest.mark.asyncio
async def test_consent_workflow():
    """Test consentimiento: dar → retirar → data export"""
    
    # Step 1: Register consent
    consent_id = await consent_mgr.register_consent(
        candidate_id="cand-123",
        consent_type="SCREENING",
        ip_address="192.168.1.1",
        user_agent="Mozilla...",
        timestamp=datetime.utcnow()
    )
    
    # Verify consent_record created
    record = await db.get(ConsentRecord, consent_id)
    assert record.given == True
    assert record.withdrawn == False
    
    # Step 2: Withdraw consent (after 30 days)
    await consent_mgr.withdraw_consent(
        candidate_id="cand-123",
        consent_type="SCREENING",
        request_timestamp=datetime.utcnow() + timedelta(days=30)
    )
    
    # Verify marked as withdrawn
    record = await db.get(ConsentRecord, consent_id)
    assert record.withdrawn == True
    assert record.withdrawn_at is not None
    
    # Step 3: Data should start deletion countdown
    # (cleanup job executes after 90d soft-delete)
```

#### Test 3: Penetration Testing (Security Audit)

```bash
# Verificar encriptación en tránsito
curl -v https://api.ticketdesk.com/health
# Expected: HTTP/2, TLS 1.3, certificate válido

# Verificar no hay credentials en logs
grep -r "password\|token\|secret" /var/log/ticketdesk/
# Expected: No results (secrets should be masked)

# Verificar JWT token expira
TOKEN=$(curl -s -X POST /api/auth/login -d '{...}' | jq -r .access_token)
echo $TOKEN | jq -R 'split(".") | .[1] | @base64d | fromjson'
# Expected: "exp": 1717077600 (1 hora desde ahora)

# Verificar RBAC enforcement
curl -H "Authorization: Bearer $RECRUITER_TOKEN" \
  -X DELETE /api/campaign/camp-123
# Expected: 403 Forbidden (recruiters no pueden deleter campaigns)

curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X DELETE /api/campaign/camp-123
# Expected: 200 OK (admins can delete)
```

#### Test 4: Data Retention Policy Execution

```bash
# Verify retention policy runs nightly
aws logs tail /ecs/ticketdesk-backend --follow | grep -i "cleanup\|retention"

# Verify soft-deleted data is inaccessible
# (but still in DB for LGPD proof)
curl -H "Authorization: Bearer $TOKEN" \
  /api/candidate/cand-123-deleted
# Expected: 404 (soft-deleted candidate is hidden from API)

# Verify hard-deleted data after 90d is gone
SELECT COUNT(*) FROM candidates WHERE id = 'cand-123-deleted-90d-ago';
# Expected: 0

# But audit logs still exist (for compliance)
SELECT COUNT(*) FROM audit_logs WHERE subject_id = 'cand-123-deleted-90d-ago';
# Expected: >0 (proof of deletion request still in audit trail)
```

---

## 💰 ATRIBUTO 3: EFICIENCIA DE COSTOS (PERFORMANCE)

### ¿Por Qué Es Crítico Para Este Producto?

#### Análisis Económico

```
Modelo de Costo Principal: Claude API Token Usage

Costo Claude API:
├─ Input: $0.003 per 1K tokens
├─ Output: $0.015 per 1K tokens
└─ Average evaluación candidato: ~500 input + 100 output = $0.0012 per candidato

Volume Scenarios (10 semanas):

MVP Target: 10,000 candidatos/mes = 120,000/año
├─ Claude API cost: ~$150/month = $1,800/año
├─ Infrastructure: ~$2,000/month = $24,000/año
├─ Total: ~$25,800/año ÷ 120,000 candidatos = $0.215/candidato
└─ Target: <$0.30/candidato (ROI = $16.67 → $4.17 per evaluación)

Scale Scenario: 100,000 candidatos/mes (scale-up success)
├─ Claude API cost: ~$1,500/month = $18,000/year
├─ Infrastructure: ~$8,000/month = $96,000/year
├─ Total: ~$114,000/year ÷ 1.2M candidatos = $0.095/candidato ✅ PROFITABLE

Ineficiencies (Si NO optimizado):
├─ No caching: 2x Claude API calls → +$900/month waste
├─ Large prompts: +50% tokens → +$750/month waste
├─ Redundant evaluations: +100% calls → +$1,500/month waste
└─ Total waste potential: >$3,000/month = $36,000/year loss

Criticidad:
├─ Si costo sube 50%: $0.30 → $0.45/candidato → Modelo insostenible
├─ Si performance lenta: Candidatos abandonen (low conversion)
├─ Si latencia >3s: HR abandone plataforma (VX)
└─ → Negocio muere si no optimizado
```

#### Requisitos Extractados

```
From requirements.md:
├─ "Performance <2s per endpoint (p99)"
├─ "80%+ code coverage (testing efficiency)"
└─ "Support 1000 concurrent screenings"

From nfr-design.md:
├─ "Caching strategy: Rubric cache (Redis, TTL 7d)"
├─ "API response compression (gzip, 70-80% reduction)"
├─ "Database query optimization (indices, N+1 prevention)"
└─ "Auto-scaling: IF CPU >70% → add task"

From infrastructure-design.md:
├─ "Redis cache layer (session, rubric, queue)"
├─ "CloudWatch metrics: token usage tracking"
└─ "Cost monitoring: alerts if spending >budget"
```

---

### Táctica 1: Intelligent Caching (Redis) + Prompt Optimization

**Patrón**: Multi-tier Caching + Prompt Engineering

```python
# src/infrastructure/cache_manager.py
import hashlib
from datetime import timedelta

class CacheManager:
    """Gestiona caché multi-tier para optimizar costos Claude"""
    
    def __init__(self, redis_pool):
        self.redis = redis_pool
    
    # TIER 1: Rubric Cache (7 days)
    async def get_or_cache_rubric(self, rubric_id: str) -> dict:
        """
        Cache rúbrica (cambia raramente, costo: 0 tokens si cached)
        """
        # Try Redis
        cache_key = f"rubric:{rubric_id}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            logger.info(f"Rubric cache hit: {rubric_id}")
            return json.loads(cached)
        
        # Cache miss: fetch from DB
        logger.info(f"Rubric cache miss: {rubric_id} - querying DB")
        rubric = await self.db.get_rubric(rubric_id)
        
        # Store in Redis (TTL: 7 days)
        await self.redis.setex(
            cache_key,
            timedelta(days=7),
            json.dumps(rubric)
        )
        
        return rubric
    
    # TIER 2: Session Context Cache (24 hours)
    async def get_or_cache_session_context(self, session_id: str) -> dict:
        """
        Cache contexto sesión (preguntas + respuestas previas)
        Evita re-fetching de BD en cada request
        """
        cache_key = f"session:{session_id}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Fetch from DB
        context = await self.db.get_session_context(session_id)
        
        # Store (TTL: 24 hours)
        await self.redis.setex(
            cache_key,
            timedelta(hours=24),
            json.dumps(context)
        )
        
        return context
    
    # TIER 3: Evaluation Results Cache (temporary, 1 hour)
    async def cache_evaluation_result(
        self,
        session_id: str,
        response_id: str,
        evaluation_result: dict
    ):
        """
        Cache resultado evaluación (para re-render si needed)
        TTL: 1 hora (después guarda en DB)
        """
        cache_key = f"eval:{session_id}:{response_id}"
        await self.redis.setex(
            cache_key,
            timedelta(hours=1),
            json.dumps(evaluation_result)
        )

class PromptOptimizer:
    """Optimiza prompts para minimizar tokens"""
    
    async def generate_optimized_question_prompt(
        self,
        campaign_context: str,
        rubric_criterion: str,
        candidate_responses_so_far: List[str],
        question_index: int
    ) -> str:
        """
        Genera prompt para Claude, OPTIMIZADO para tokens.
        
        Estrategia:
        ├─ Minimizar context window (resumen vs full history)
        ├─ Template fijo (no variar estructura)
        ├─ Tokens presupuestados (limit max_tokens)
        └─ Reusar instrucciones (no repetir)
        """
        
        # 1. Resumen comprimido de respuestas previas (en lugar de full transcript)
        summary = self._summarize_responses(candidate_responses_so_far)
        
        # 2. Template fijo (Claude cached prompts si template igual)
        prompt = f"""You are a hiring screener evaluating candidates against a job rubric.

ROLE: {rubric_criterion}
QUESTION #{question_index}

Candidate context:
{summary}

Generate ONE clarifying follow-up question about {rubric_criterion}.
Be concise (<20 words).
Question:"""
        
        # 3. Count tokens (aproximadamente)
        token_count = len(prompt.split()) * 1.3  # ~1.3 tokens per word
        logger.info(f"Prompt token estimate: {token_count}")
        
        return prompt
    
    def _summarize_responses(self, responses: List[str]) -> str:
        """Resumen comprimido (en lugar de full history)"""
        if len(responses) == 0:
            return "(No previous responses)"
        
        # Keep only LAST 3 responses + action taken
        summary = "\n".join(responses[-3:])
        return summary[:500]  # Max 500 chars para ahorrar tokens

# Uso en BotEngine
class BotEngine:
    async def generate_next_question(
        self,
        session_id: str,
        rubric_id: str,
        candidate_responses: List[str],
        question_index: int
    ) -> str:
        """Genera siguiente pregunta, OPTIMIZADO para costo"""
        
        # Get rubric from CACHE (not fresh from API)
        rubric = await self.cache_manager.get_or_cache_rubric(rubric_id)
        criterion = rubric["criteria"][question_index % len(rubric["criteria"])]
        
        # Get campaign CONTEXT from CACHE
        campaign = await self.cache_manager.get_or_cache_campaign(rubric["campaign_id"])
        
        # Generate OPTIMIZED prompt (minimize tokens)
        prompt = await self.prompt_optimizer.generate_optimized_question_prompt(
            campaign_context=campaign.get("description"),
            rubric_criterion=criterion,
            candidate_responses_so_far=candidate_responses,
            question_index=question_index
        )
        
        # Call Claude (with token tracking)
        try:
            response = await self.claude_client_with_monitoring.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=150,  # Presupuestado (no variable)
                messages=[{"role": "user", "content": prompt}],
                timeout=15
            )
            
            # TRACK: Token usage (for cost monitoring)
            self.token_counter.record_usage(
                model="claude-3-5-sonnet",
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                session_id=session_id
            )
            
            return response.content[0].text
            
        except asyncio.TimeoutError:
            # Fallback: Generic question (0 tokens from Claude)
            fallback = "What specific achievements are you most proud of?"
            logger.warning(f"Claude timeout, using fallback question")
            return fallback
```

---

### Táctica 2: Token Monitoring + Cost Budgeting

**Patrón**: Cost Monitoring + Alerting + Anomaly Detection

```python
# src/monitoring/token_tracker.py
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

class TokenTracker:
    """Monitorea gasto de tokens Claude para alertar si anormal"""
    
    def __init__(self, cloudwatch_client, budget_per_month=250):  # $250/month
        self.cw = cloudwatch_client
        self.budget = budget_per_month
        self.session_usage = defaultdict(lambda: {"input": 0, "output": 0})
        self.daily_usage = defaultdict(lambda: {"input": 0, "output": 0})
    
    async def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        session_id: str,
        endpoint: str
    ):
        """Registra uso de tokens y detecta anomalías"""
        
        # Track per session
        self.session_usage[session_id]["input"] += input_tokens
        self.session_usage[session_id]["output"] += output_tokens
        
        # Track daily aggregate
        today = datetime.utcnow().date()
        self.daily_usage[str(today)]["input"] += input_tokens
        self.daily_usage[str(today)]["output"] += output_tokens
        
        # Calculate cost
        cost = (input_tokens / 1000 * 0.003) + (output_tokens / 1000 * 0.015)
        
        # Anomaly detection: session using >2000 tokens (outlier)
        session_total = self.session_usage[session_id]["input"] + \
                       self.session_usage[session_id]["output"]
        
        if session_total > 2000:
            logger.warning(f"⚠️ Anomaly: Session {session_id} used {session_total} tokens (>2000)")
            # Could indicate:
            # - Candidate looping (asking same Q multiple times)
            # - Prompt bloat (too much context)
            # - Bug in question generation
            
            # Alert ops
            await self._send_alert(
                message=f"Session {session_id} high token usage: {session_total}",
                severity="WARNING"
            )
        
        # Daily budget check
        daily_total = self.daily_usage[str(today)]["input"] + \
                     self.daily_usage[str(today)]["output"]
        daily_cost = (daily_total / 1000) * (0.003 + 0.015) / 2  # Average cost
        
        # If daily cost trending high, alert
        if daily_cost > (self.budget / 30):  # Daily budget = monthly / 30
            logger.warning(f"Daily cost {daily_cost:.2f} exceeds budget ${self.budget/30:.2f}")
            await self._send_alert(
                message=f"Daily Claude cost ${daily_cost:.2f} exceeds budget",
                severity="WARNING"
            )
        
        # Send metric to CloudWatch
        await self._send_cloudwatch_metric(
            metric_name="TokenUsage",
            value=input_tokens + output_tokens,
            unit="Count",
            dimensions={
                "Model": model,
                "Endpoint": endpoint
            }
        )
        
        # Log for analysis
        logger.info(f"Token usage: {input_tokens} in + {output_tokens} out = ${cost:.4f}")
    
    async def get_monthly_cost_estimate(self) -> dict:
        """Estima costo mensual basado en trending"""
        
        # Fetch last 7 days usage from DB
        usage_data = await self.db.query(TokenUsageLog).filter(
            TokenUsageLog.timestamp > datetime.utcnow() - timedelta(days=7)
        ).all()
        
        total_input = sum(u.input_tokens for u in usage_data)
        total_output = sum(u.output_tokens for u in usage_data)
        
        cost_7d = (total_input / 1000 * 0.003) + (total_output / 1000 * 0.015)
        cost_monthly_estimate = cost_7d * (30 / 7)
        
        return {
            "estimated_monthly_cost": cost_monthly_estimate,
            "budget": self.budget,
            "on_track": cost_monthly_estimate < self.budget,
            "percentage_of_budget": (cost_monthly_estimate / self.budget) * 100,
            "warning": "⚠️ OVER BUDGET" if cost_monthly_estimate > self.budget else "✅ On track"
        }
```

---

### Táctica 3: Database Query Optimization + N+1 Prevention

**Patrón**: Eager Loading + Query Optimization + Indices

```python
# src/infrastructure/query_optimizer.py
from sqlalchemy.orm import joinedload
from sqlalchemy import text

class QueryOptimizer:
    """Optimiza queries para minimizar latencia (y costo infra)"""
    
    # PROBLEMA: N+1 queries
    # For cada sesión, fetch todas respuestas → 1 + N queries
    
    async def get_session_with_responses_bad(self, session_id: str):
        """❌ BAD: N+1 queries"""
        # Query 1: Fetch sesión
        session = await self.db.query(Session).filter_by(
            id=session_id
        ).first()
        
        # Query N: Fetch respuestas (1 per respuesta)
        responses = []
        for response_id in session.response_ids:
            responses.append(
                await self.db.query(ScreeningResponse).filter_by(
                    id=response_id
                ).first()
            )
        
        # Result: 1 + N queries (N = número respuestas)
        # Si 10 respuestas: 11 queries instead of 1!
        return {"session": session, "responses": responses}
    
    async def get_session_with_responses_good(self, session_id: str):
        """✅ GOOD: Single query with eager loading"""
        # Single query con JOIN (eager loading)
        session = await self.db.query(Session).options(
            joinedload(Session.responses)
        ).filter_by(id=session_id).first()
        
        # Result: 1 query + Python relationship loading
        return {"session": session, "responses": session.responses}
    
    async def get_evaluation_with_citations_good(self, evaluation_id: str):
        """✅ Eager load citations (avoid N+1)"""
        evaluation = await self.db.query(Evaluation).options(
            joinedload(Evaluation.response),
            joinedload(Evaluation.citations)
        ).filter_by(id=evaluation_id).first()
        
        return evaluation

# Indices para query optimization
"""
CREATE INDEX idx_sessions_candidate_id ON sessions(candidate_id);
CREATE INDEX idx_sessions_status ON sessions(status, created_at DESC);
CREATE INDEX idx_screening_responses_session_id ON screening_responses(session_id);
CREATE INDEX idx_evaluations_response_id ON evaluations(response_id);
CREATE INDEX idx_evaluations_session_score ON evaluations(session_id, score DESC);
CREATE INDEX idx_decisions_session_id ON decisions(session_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type, created_at DESC);
"""

# Connection pooling para reutilizar conexiones
class DatabasePool:
    def __init__(self):
        self.engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_size=20,          # 20 conexiones simultáneas
            max_overflow=20,       # Allow 20 más si needed
            pool_recycle=3600,     # Recycle después 1 hora
            connect_args={
                "timeout": 5,      # 5s timeout para conexión
                "server_settings": {
                    "application_name": "ticketdesk-backend"
                }
            }
        )
```

---

### Verificación: Cómo Validar Performance & Costos

#### Test 1: Caching Effectiveness

```bash
# Measure cache hit rate
redis-cli INFO stats | grep hits
# Expected: hits/(hits+misses) > 85%

# Monitor cache key sizes
redis-cli --bigkeys --scan
# Expected: rubric:* keys <50KB each

# Test cache TTL
redis-cli TTL "rubric:rubric-123"
# Expected: 604800 (7 days in seconds)
```

#### Test 2: Token Usage Monitoring

```python
# tests/test_token_efficiency.py
@pytest.mark.asyncio
async def test_prompt_optimization_reduces_tokens():
    """Verify optimized prompts use fewer tokens"""
    
    # Un-optimized prompt
    bad_prompt = """You are a hiring screener...
    [FULL 10-response history with all details]
    Generate next question...
    """
    
    # Optimized prompt
    good_prompt = """You are a hiring screener...
    [Last 3 responses SUMMARIZED]
    Generate next question...
    """
    
    # Count tokens
    bad_tokens = count_tokens(bad_prompt)
    good_tokens = count_tokens(good_prompt)
    
    # Expected: good < bad (50-70% reduction)
    improvement = (1 - good_tokens / bad_tokens) * 100
    assert improvement > 50, f"Only {improvement}% improvement"
    
    logger.info(f"✅ Prompt optimization: {bad_tokens} → {good_tokens} tokens ({improvement:.1f}% reduction)")
```

#### Test 3: Query Performance Benchmarking

```bash
# PostgreSQL EXPLAIN to verify indices are used
EXPLAIN ANALYZE
SELECT s.id, COUNT(r.id) as responses
FROM sessions s
LEFT JOIN screening_responses r ON s.id = r.session_id
WHERE s.candidate_id = 'cand-123'
GROUP BY s.id;

# Expected output:
#   ...
#   Index Scan using idx_sessions_candidate_id on sessions s
#   Index Scan using idx_screening_responses_session_id on screening_responses r
#   ... (should NOT say "Seq Scan", which is slow)

# Measure query time
SELECT pg_sleep(0.001);  -- 1ms sleep
EXPLAIN ANALYZE ...query...
# Expected: <100ms for any query
```

#### Test 4: Load Testing with Cost Monitoring

```python
# tests/load_test_cost_efficiency.py
import locust

class CandidateLoad(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def complete_screening(self):
        """Simulates full screening flow"""
        
        # 1. Start screening (cheap, minimal Claude)
        session = self.client.post("/api/screening/start").json()
        
        # 2. Answer 10 questions (each calls Claude)
        for i in range(10):
            self.client.post(
                f"/api/screening/{session['id']}/response",
                json={"response_text": "Test response"}
            )
        
        # Monitor costs during load
        # Expected: 10 screens * 0.12 USD/screen = $1.20 for 10 screens

# Run load test
# locust -f load_test_cost_efficiency.py --host=http://localhost:8000 -u 100 -r 10 -t 5m

# Check token usage during test
aws cloudwatch get-metric-statistics \
  --namespace TicketDesk \
  --metric-name TokenUsage \
  --start-time 2026-05-27T10:00:00Z \
  --end-time 2026-05-27T10:05:00Z \
  --period 60 \
  --statistics Sum

# Expected:
# - 100 users × 10 questions = 1000 Claude calls
# - Total cost ~$1.20
# - Cost/evaluation = $1.20 / 1000 = $0.0012 ✅ (within budget)
```

#### Test 5: Cost Monitoring Dashboard

```python
# Generate weekly cost report
weekly_report = await token_tracker.get_monthly_cost_estimate()

print(f"""
💰 CLAUDE API COST REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Estimated Monthly Cost: ${weekly_report['estimated_monthly_cost']:.2f}
Budget:               ${weekly_report['budget']:.2f}
Status:               {weekly_report['warning']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Percentage of Budget:  {weekly_report['percentage_of_budget']:.1f}%

🎯 Target: <$250/month for 10K candidates/month
📊 Current Run Rate: ${weekly_report['estimated_monthly_cost']:.2f}
""")

# If over budget → Trigger optimization
if weekly_report['estimated_monthly_cost'] > weekly_report['budget']:
    logger.critical("❌ OVER BUDGET - Trigger optimization")
    # Actions:
    # 1. Reduce max_tokens per prompt
    # 2. Increase cache TTL
    # 3. Alert eng team
    # 4. Consider batch processing
```

---

## 🎯 RESUMEN FINAL

| Atributo | Crítico Por | Táctica Principal | Métrica Clave | Meta MVP |
|----------|-------------|-------------------|---------------|----------|
| **Confiabilidad** | Sistema real-time, candidatos esperando | Multi-AZ + Circuit Breaker | SLA Uptime | 99.5% (43.8 min/mes downtime) |
| **Seguridad LGPD** | Datos sensibles, multas legales | Audit Logs Append-Only + RBAC | Compliance Audit Pass | 100% audit trail, zero breaches |
| **Eficiencia Costos** | Claude API costo variable | Caching + Prompt Opt + Monitoring | Cost/Evaluation | <$0.30/evaluación |

---

**Generado**: 2026-05-27  
**Base**: Artefactos de Inception (Requirements, Architecture, NFR Design)  
**Status**: ✅ Listo para implementación


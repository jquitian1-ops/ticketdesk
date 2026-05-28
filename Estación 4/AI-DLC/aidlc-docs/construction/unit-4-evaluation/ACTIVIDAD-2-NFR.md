# Unit 4: Evaluación (Scoring Engine) — Actividad 2: Requisitos No-Funcionales

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 2 - Requisitos No-Funcionales (NFR)  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**6 Requisitos No-Funcionales** para Scoring Engine con métricas cuantificadas y SLAs.

---

## 🎯 NFR 1: Precisión Scoring

**Categoría**: Exactitud, Confiabilidad

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Accuracy scoring automático | >95% | >90% |
| False positive rate (HIRE cuando debe REJECT) | <3% | <5% |
| False negative rate (REJECT cuando debe HIRE) | <2% | <5% |
| Concordancia inter-evaluador | >85% (cuando >1 evaluador) | >70% |
| Tiempo cálculo score | <500ms | <1s |

### Criterios de Aceptación

- [ ] Scoring automático predice decisión evaluador >95% casos
- [ ] <3% falsos positivos (contrato fraudulento)
- [ ] <2% falsos negativos (talento rechazado)
- [ ] Kappa Cohen >0.85 cuando múltiples evaluadores
- [ ] p95 latencia cálculo <500ms

### Estrategia Medición

```python
# test_scoring_accuracy.py
from sklearn.metrics import accuracy_score, confusion_matrix, cohen_kappa_score

def test_scoring_accuracy():
    # Dataset histórico: 1000 evaluaciones
    evaluaciones_históricas = db.query(Evaluación).limit(1000)
    
    predicciones_automáticas = []
    decisiones_reales = []
    
    for eval in evaluaciones_históricas:
        pred = scoring_engine.calcular_score(eval.screening_id)
        predicciones_automáticas.append(pred.decisión)
        decisiones_reales.append(eval.decisión)
    
    accuracy = accuracy_score(decisiones_reales, predicciones_automáticas)
    assert accuracy >= 0.95, f"Accuracy {accuracy} < 95%"
    
    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(decisiones_reales, predicciones_automáticas).ravel()
    fpr = fp / (fp + tn)  # False positive rate
    fnr = fn / (fn + tp)  # False negative rate
    
    assert fpr < 0.03, f"FPR {fpr*100}% > 3%"
    assert fnr < 0.02, f"FNR {fnr*100}% > 2%"

def test_inter_evaluator_agreement():
    # Evaluaciones con >1 evaluador
    evaluaciones_duplicadas = db.query(Evaluación).filter(
        Evaluación.múltiples_evaluadores == True
    ).limit(100)
    
    scores_evaluador_1 = []
    scores_evaluador_2 = []
    
    for eval_pair in evaluaciones_duplicadas:
        scores_evaluador_1.append(eval_pair.evaluador_1_score)
        scores_evaluador_2.append(eval_pair.evaluador_2_score)
    
    kappa = cohen_kappa_score(scores_evaluador_1, scores_evaluador_2)
    assert kappa >= 0.85, f"Cohen's Kappa {kappa} < 0.85"
```

---

## 🎯 NFR 2: Velocidad Evaluación

**Categoría**: Eficiencia, Rendimiento

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Tiempo inicial scoring | <500ms | <1s |
| Tiempo extracción citas | <200ms | <500ms |
| Generación reporte | <2s | <5s |
| P95 latencia evaluación completa | <3s | <5s |

### Criterios de Aceptación

- [ ] API /evaluation POST responde <500ms (p95)
- [ ] Citas relevantes extraídas <200ms
- [ ] Reporte generado <2s
- [ ] Sin timeouts bajo carga (500 evaluaciones/hora)

### Estrategia Medición

```python
# APM instrumentación
import time

@app.post("/api/screenings/{id}/evaluation")
async def submit_evaluation(screening_id: UUID, eval_data: EvaluationSchema):
    start = time.time()
    
    # 1. Calcular scores
    score_start = time.time()
    scores = scoring_engine.calcular_scores(eval_data)
    score_duration = time.time() - score_start
    emit_metric("scoring_duration_ms", score_duration * 1000)
    
    # 2. Extraer citas
    citation_start = time.time()
    citas = citation_extractor.extraer_citas(screening_id, scores)
    citation_duration = time.time() - citation_start
    emit_metric("citation_extraction_ms", citation_duration * 1000)
    
    # 3. Generar reporte
    report_start = time.time()
    reporte = ReportGenerator.generar_reporte(screening_id, scores, citas)
    report_duration = time.time() - report_start
    emit_metric("report_generation_ms", report_duration * 1000)
    
    # 4. Guardar BD
    db.add(Evaluación(scores=scores, reporte_id=reporte.id))
    db.commit()
    
    total_duration = time.time() - start
    emit_metric("evaluation_total_ms", total_duration * 1000)
    
    return {"status": "success", "duration_ms": total_duration * 1000}
```

---

## 🎯 NFR 3: Confiabilidad (Auditoría Completa)

**Categoría**: Integridad, Trazabilidad

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Auditoría trail completitud | 100% eventos | 100% |
| Uptime evaluación service | 99.5% | 99.0% |
| Validaciones fallidas recuperables | >95% | >90% |
| RPO (Recovery Point Objective) | <1 min | <5 min |

### Criterios de Aceptación

- [ ] Cada evaluación auditada (usuario, timestamp, IP, user_agent)
- [ ] 99.5% uptime SLA (máx 3.6 horas downtime/mes)
- [ ] Fallos validación reversibles (no pierden datos)
- [ ] Backup evaluaciones cada 60 segundos

### Estrategia Medición

```python
# Validación auditoría
def test_audit_trail_completeness():
    evaluaciones = db.query(Evaluación).limit(100)
    
    for eval in evaluaciones:
        assert eval.auditoría.usuario_id is not None
        assert eval.auditoría.timestamp is not None
        assert eval.auditoría.ip_address_hashed is not None
        assert eval.auditoría.user_agent_hashed is not None
        assert eval.auditoría.cambios is not None

# Métricas uptime
@app.get("/health")
def health_check():
    # CloudWatch custom metric
    emit_metric("ScoringEngineHealth", value=1)
    return {"status": "healthy"}
```

---

## 🎯 NFR 4: Seguridad (Validación Datos)

**Categoría**: Integridad, Protección

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Validación input | 0 inyecciones SQL | - |
| Encriptación scores | AES-256 en tránsito | AES-128 |
| Validación firma evaluador | 100% con clave privada | 100% |
| PII en logs | 0 plain text | 0 |

### Criterios de Aceptación

- [ ] Scores en HTTPS/TLS 1.3
- [ ] Feedback evaluador sanitizado (sin scripts)
- [ ] Firma digital evaluador validada (RS256)
- [ ] Email, phone nunca en logs (masked)

### Estrategia Medición

```python
# Sanitización input
from bleach import clean

def submit_evaluation(eval_data: EvaluationSchema):
    # Sanitizar feedback
    feedback_clean = clean(
        eval_data.feedback,
        tags=[],  # No HTML tags
        strip=True
    )
    
    # Validar firma
    payload = {
        "evaluation_id": str(eval_data.id),
        "timestamp": eval_data.timestamp,
        "scores": eval_data.scores
    }
    
    try:
        jwt.decode(
            eval_data.signature,
            key=get_evaluador_public_key(eval_data.evaluador_id),
            algorithms=["RS256"]
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=403, detail="Signature invalid")
```

---

## 🎯 NFR 5: Escalabilidad (Evaluaciones Concurrentes)

**Categoría**: Crecimiento, Capacidad

### Requisitos Cuantificados

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Evaluaciones concurrentes | 200+ | Counter evaluación_status=EN_PROGRESO |
| RPS evaluaciones | 50 RPS | CloudWatch RequestCount |
| Capacidad storage scores | 10M evaluaciones/año | S3 + PostgreSQL |
| Memoria por evaluación | <50MB | Process memory profiling |

### Criterios de Aceptación

- [ ] Soportar 200 evaluaciones simultáneas
- [ ] Latencia p95 <500ms bajo 50 RPS
- [ ] Storage escalable (S3 archival)
- [ ] Memory stable (no memory leaks)

### Estrategia Medición

```python
# Load test (Locust)
from locust import HttpUser, task, between

class EvaluationUser(HttpUser):
    wait_time = between(5, 15)
    
    @task
    def submit_evaluation(self):
        self.client.post(
            f"/api/screenings/{screening_id}/evaluation",
            json={
                "rubric_scores": {...},
                "decision": "HIRE",
                "feedback": "..."
            }
        )

# Correr: locust -f locustfile.py -u 200 -r 20
# -u 200: 200 usuarios concurrentes
# -r 20: 20 usuarios nuevos por segundo
```

---

## 🎯 NFR 6: Conformidad Normativa (Auditoría LGPD)

**Categoría**: Cumplimiento, Auditoría

### Requisitos Cuantificados

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Auditoría trail LGPD | 100% acceso datos | EntradaAuditoría logs |
| Retención evaluaciones | Según rúbrica (default 7 años) | S3 lifecycle policy |
| Derecho olvido latencia | <24h hard delete SLA | Celery task SLA |
| Reportes LGPD monthly | 100% completitud | ReporteCompliance |

### Criterios de Aceptación

- [ ] Logging: usuario, timestamp, IP, qué datos accedió
- [ ] Evaluaciones no exportables sin consentimiento
- [ ] Hard delete de evaluaciones <24h (cuando solicitado)
- [ ] Reporte LGPD monthly con métricas compliance

### Estrategia Medición

```python
# Structured logging LGPD
import structlog

logger = structlog.get_logger()

async def create_evaluation(screening_id: UUID, eval_data: EvaluationSchema):
    logger.info(
        "evaluation_created",
        screening_id=str(screening_id),
        evaluador_id=str(eval_data.evaluador_id),
        decision=eval_data.decision,
        campos_accedidos=["nombre", "skills", "experiencia"],
        timestamp=datetime.utcnow().isoformat(),
        propósito="EVALUATION"
    )
```

---

## 📊 Matriz NFR

| NFR | Métrica Clave | Target | Herramienta |
|---|---|---|---|
| Precisión | Accuracy scoring | >95% | Historical dataset validation |
| Velocidad | Latencia p95 | <500ms | CloudWatch APM |
| Confiabilidad | Auditoría completitud | 100% | Audit trail scan |
| Seguridad | PII en logs | 0 | Log scanning |
| Escalabilidad | Concurrentc evaluaciones | 200+ | Locust load tests |
| Conformidad | LGPD compliance | 100% | ReporteCompliance |

---

## ✅ Criterios de Aceptación (Actividad 2)

- [x] 6 NFRs documentados con métricas cuantificadas
- [x] Umbrales aceptación (objetivo + crítico) claros
- [x] Estrategias medición definidas (herramientas específicas)
- [x] Actividades garantizar listos
- [x] Integración con observabilidad (CloudWatch)

---

**Generado**: 2026-05-27  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 2 - Requisitos No-Funcionales  
**Estado**: ✅ COMPLETADA

# Unit 3: Motor Bot (BotEngine) — Actividad 3: Decisiones de Arquitectura (ADR)

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 3 - Motor Bot (BotEngine)  
**Actividad**: 3 - Diseño NFR: Architecture Decision Records (ADR)  
**Fecha**: 2026-05-27  

---

## 🎯 ADR-UNIT3-001: Streaming Claude API (SSE vs WebSocket vs Polling)

**Título**: Elegir mecanismo para entregar tokens Claude en tiempo real

**Estado**: ✅ ACEPTADA

### Contexto

Candidato espera ver respuesta bot en tiempo real (como ChatGPT). Opciones:
- **Server-Sent Events (SSE)**: Unidireccional, servidor → cliente
- **WebSocket**: Bidireccional, más complejo
- **Polling**: Cliente pregunta cada 500ms

### Opciones Evaluadas

**Opción 1: Server-Sent Events (SSE)** ✅ ELEGIDA
- ✅ Nativo navegador (EventSource API)
- ✅ Simple (HTTP 1.1, sin upgrade)
- ✅ Bajo overhead
- ❌ Unidireccional (pero suficiente para streaming)

**Opción 2: WebSocket**
- ✅ Bidireccional
- ✅ Bajo latency
- ❌ Más complejo (upgrade, heartbeat)
- ❌ Overhead mayor

**Opción 3: Polling**
- ✅ Simple
- ❌ Latencia 500ms+
- ❌ Carga servidor

### Decisión

**✅ Server-Sent Events (SSE)**

### Consecuencias

```python
# Backend FastAPI
@app.get("/api/screenings/{id}/mensajes/stream")
async def stream_response(id: UUID, background_tasks: BackgroundTasks):
    async def generate():
        try:
            async for token in client.messages.stream(...):
                yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

# Frontend React
useEffect(() => {
  const eventSource = new EventSource(`/api/screenings/${id}/mensajes/stream`);
  eventSource.onmessage = (event) => {
    const { token } = JSON.parse(event.data);
    addTokenToMessage(token);
  };
  return () => eventSource.close();
}, [id]);
```

---

## 🎯 ADR-UNIT3-002: Jailbreak Detection (Regex + Heuristics vs ML Model)

**Título**: Elegir enfoque detección jailbreak/prompt injection

**Estado**: ✅ ACEPTADA

### Contexto

Necesita detectar intentos prompt injection con:
- Alta precisión (>95%)
- Baja latencia (<50ms)
- Determinístico (sin drift)
- Sin dependencia modelo externo

### Opciones

**Opción 1: Regex + Heuristics** ✅ ELEGIDA
- ✅ Rápido (<10ms)
- ✅ Determinístico
- ✅ Explicable (qué patrón coincidió)
- ❌ Requiere mantener 20+ patrones

**Opción 2: ML Model (BERT/RoBERTa)**
- ✅ Flexible, adapta a nuevos ataques
- ❌ Latencia 50-100ms
- ❌ Drift: modelo envejece
- ❌ Overhead inferencia

**Opción 3: Tercero (OpenAI Moderation)**
- ✅ Mantenido por tercero
- ❌ Latencia > 500ms
- ❌ Costo por API call

### Decisión

**✅ Regex + Heuristics (20+ patrones)**

### Consecuencias

```python
class DetectorJailbreak:
    PATRONES = {
        'PromptInjection': [
            r'(?i)(ignora|olvida).*instrucción',
            r'(?i)ahora eres',
            r'(?i)sistema prompt',
        ],
        'Base64Encoding': [
            r'[A-Za-z0-9+/]{40,}={0,2}',  # Base64
        ],
        'ReverseEngineering': [
            r'(?i)(cuál|cual).*prompt',
            r'(?i)cómo.*programado',
        ],
    }
    
    def escanear(self, mensaje: str) -> DetectionResult:
        for tipo, patterns in self.PATRONES.items():
            for pattern in patterns:
                if re.search(pattern, mensaje):
                    return DetectionResult(
                        nivel_riesgo=self._calcular_riesgo(tipo),
                        patrón_coincidido=tipo,
                        confianza=0.95
                    )
        return DetectionResult(nivel_riesgo=BAJO, confianza=0.0)
```

---

## 🎯 ADR-UNIT3-003: Gestión Contexto (Sliding Window vs Summarization)

**Título**: Elegir estrategia limitar token budget conversación

**Estado**: ✅ ACEPTADA

### Contexto

Token budget = 2000 max. Si conversación crece:
- **Sliding Window**: Descartar mensajes antiguos
- **Summarization**: Resumir con Claude (costo extra)
- **Hybrid**: Window + resumen selectivo

### Opciones

**Opción 1: Hybrid (Sliding Window + Resumption)** ✅ ELEGIDA
- ✅ Preserva coherencia
- ✅ Mantiene últimos N mensajes (detalle)
- ✅ Resume antiguos (contexto)

**Opción 2: Pure Sliding Window**
- ✅ Rápido
- ❌ Pérdida contexto si antigua importante

**Opción 3: Pure Summarization**
- ✅ Contexto máximo
- ❌ Latencia extra (llamada Claude)
- ❌ Token inefficient

### Decisión

**✅ Sliding Window + Summarization Híbrida**

### Estrategia

```
Si tokens_usados > 1800:
  1. Resumen: primeros 5 mensajes → "User asked about X, bot explained Y"
  2. Ventana: últimos 10 mensajes (completos)
  3. Nueva estimación: ~800 tokens
  4. Continuar conversación
```

---

## 🎯 ADR-UNIT3-004: Almacenamiento Transcripciones (S3 vs PostgreSQL)

**Título**: Elegir almacenamiento transcripciones completas

**Estado**: ✅ ACEPTADA

### Contexto

Transcripciones ~150KB c/u, millones anuales. Opciones:
- **S3 + URLs firmadas**: Escalable, económico
- **PostgreSQL**: Consultas SQL, integridad referencial
- **Hybrid**: S3 + metadata en BD

### Opciones

**Opción 1: S3 + PostgreSQL metadata** ✅ ELEGIDA
- ✅ S3 escalable, económico ($0.023/GB)
- ✅ BD con references, auditoría
- ✅ Cifrado KMS automático
- ✅ Lifecycle policies (7 años)

**Opción 2: PostgreSQL completo**
- ❌ Costo: ~$1000/TB/año
- ❌ Escalabilidad limitada
- ❌ Backups más complejos

**Opción 3: S3 solo**
- ❌ Sin auditoría referencial
- ❌ Riesgo acceso no autorizado

### Decisión

**✅ S3 para transcripción JSON + PostgreSQL para metadata**

### Implementación

```python
# Guardar transcripción
transcript_json = {
    "session_id": "...",
    "messages": [...],
    "metadata": {...}
}

# Upload a S3
s3.put_object(
    Bucket='transcripciones',
    Key=f'{session_id}/{conversation_id}.json',
    Body=json.dumps(transcript_json),
    ServerSideEncryption='aws:kms',
    Metadata={'session_id': session_id}
)

# Guardar metadata + URL en BD
transcription = Transcripción(
    id_sesión=session_id,
    url_s3_texto='s3://transcripciones/...',
    cantidad_mensajes=len(messages),
    tokens_totales=sum(m.tokens for m in messages),
    creada_en=datetime.utcnow()
)
db.add(transcription)
db.commit()
```

---

## 📊 Matriz ADRs

| ADR | Decisión | Alternativa | Razón |
|---|---|---|---|
| ADR-UNIT3-001 | SSE | WebSocket | Simple + nativo navegador |
| ADR-UNIT3-002 | Regex+Heuristics | ML Model | Determinístico, rápido, explainable |
| ADR-UNIT3-003 | Sliding Window + Summarization | Pure Window | Preserva contexto |
| ADR-UNIT3-004 | S3 + BD metadata | PostgreSQL | Escalabilidad + costo |

---

## ✅ Criterios de Aceptación (Actividad 3)

- [x] 4 ADRs documentados (formato CODC)
- [x] Opciones evaluadas objetivamente
- [x] Decisiones con consecuencias documentadas
- [x] Implementación código en Python
- [x] Integración con Unit 2 mapeada

---

**Generado**: 2026-05-27  
**Unit**: 3 - Motor Bot (BotEngine)  
**Actividad**: 3 - Decisiones Arquitectura  
**Estado**: ✅ COMPLETADA

# Unit 3: Motor Bot (BotEngine) — Actividad 4: Arquitectura e Infraestructura

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 3 - Motor Bot (BotEngine)  
**Actividad**: 4 - Diseño Infraestructura: Componentes, Flujos, Despliegue  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**Arquitectura C4 Level 3** para BotEngine con componentes, canales comunicación, flujos datos, persistencia, y despliegue AWS.

---

## 🏗️ C4 Level 1: Sistema BotEngine

```
┌─────────────────────────────────────────┐
│      TicketDesk Enterprise v1.0         │
├─────────────────────────────────────────┤
│ Unit 2    │ Unit 3      │ Unit 5        │
│ Backend   │ BotEngine   │ Frontend      │
│ FastAPI   │ (Foco)      │ Next.js       │
└─────────────────────────────────────────┘
```

---

## 🏗️ C4 Level 2: Contenedores BotEngine

```
┌──────────────────────────────────────────────────────────────┐
│                    AWS ECS Cluster                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐      ┌─────────────────────────────┐   │
│  │   API Layer    │      │    Processing Cores         │   │
│  │ (FastAPI)      │◄────►│ • Message Handler           │   │
│  │                │      │ • Jailbreak Detector        │   │
│  │ • SSE Stream   │      │ • Token Counter             │   │
│  │ • CORS         │      │ • Prompt Renderer           │   │
│  │ • Auth         │      │ • Claude API Client         │   │
│  └────────────────┘      └─────────────────────────────┘   │
│         △                          △                        │
│         │                          │                        │
│         └──────────┬───────────────┘                        │
│                    │                                        │
│         ┌──────────▼──────────────┐                         │
│         │    Queue Worker         │                         │
│         │ (Celery + Redis)        │                         │
│         │ • Async tasks           │                         │
│         │ • S3 uploads            │                         │
│         │ • Cleanup jobs          │                         │
│         └────────────────────────┘                          │
│                                                               │
└──────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐       ┌──────────────┐      ┌──────────┐
   │PostgreSQL       │Redis Cache   │      │S3 Bucket │
   │(Messages,       │(Prompts,     │      │(Transcrip│
   │Conversations)   │Conversations)│      │tions)    │
   └─────────┘       └──────────────┘      └──────────┘
```

---

## 🏗️ C4 Level 3: Componentes Internos

```
┌─ FastAPI Application ──────────────────────────────────────┐
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Router: /api/screenings/{id}/mensajes        │ │
│  │  POST   → submitMessage(message_data)                │ │
│  │  GET    → stream ↑ (SSE, ADR-UNIT3-001)              │ │
│  └──────────────────────────────────────────────────────┘ │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │      Middleware (Auth, Jailbreak Detection)         │ │
│  │                                                     │ │
│  │  1. Validar JWT (Unit 2 token)                      │ │
│  │  2. Verificar sesión activa                         │ │
│  │  3. Detectar jailbreak (REGLA-BOT-02) ◄──┐         │ │
│  │  4. Contador intento jailbreak                      │ │
│  │  5. Auto-terminar si intentos >= 3                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         Service Layer: BotEngineService             │ │
│  │                                                     │ │
│  │  async def procesar_mensaje(                         │ │
│  │    conversation_id: UUID,                            │ │
│  │    mensaje: MensajeSchema                            │ │
│  │  ) -> AsyncIterator[str]:                            │ │
│  │    1. Guardar mensaje BD                             │ │
│  │    2. Obtener prompt sistema (cache Redis)           │ │
│  │    3. Estimar tokens                                 │ │
│  │    4. Validar presupuesto (REGLA-BOT-05)             │ │
│  │    5. Llamar Claude API (streaming)                  │ │
│  │    6. Emit token cada <100ms (NFR-UNIT3-001)         │ │
│  │    7. Guardar respuesta BD                           │ │
│  │    8. Actualizar conversación estado                 │ │
│  │    9. Publicar evento MensajeIntercambiado           │ │
│  └─────────────────────────────────────────────────────┘ │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │      Repository Layer (Data Access)                 │ │
│  │                                                     │ │
│  │  • ConversacionRepository                            │ │
│  │  • MensajeRepository                                 │ │
│  │  • JailbreakRepository                               │ │
│  │  • TranscripcionRepository                           │ │
│  │                                                     │ │
│  │  async def guardar_mensaje(mensaje: Mensaje)        │ │
│  │    INSERT INTO Mensaje (...)                         │ │
│  │    RETURNING id, marca_tiempo                        │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
└─ Integración Externos ─────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────────┐    ┌──────────────┐    ┌──────────┐
   │Claude API   │    │PostgreSQL    │    │S3 Bucket │
   │(Streaming)  │    │(Persistencia)│    │(Archivos)│
   │Token budget │    │Transactions  │    │Encriptado│
   └─────────────┘    │ACID          │    │KMS       │
                      └──────────────┘    └──────────┘
```

---

## 🔄 Flujo de Datos: Mensaje Usuario → Respuesta Claude

```
CANDIDATO (Unit 5)
        │
        │ POST /api/screenings/{id}/mensajes
        │ { "contenido": "¿Cuál es tu experiencia?" }
        │
        ▼
┌─────────────────────────┐
│ Unit 3: API Gateway     │
│ Validar request         │
│ Extraer JWT             │
└────────────┬────────────┘
             │
             ▼
     ┌──────────────────────┐
     │ Middleware Jailbreak │
     │ Ejecutar detector     │
     │ (REGLA-BOT-02)        │
     │ <50ms latencia        │
     └──────────┬───────────┘
                │
        ┌───────┴────────┐
        │ ¿Jailbreak?    │
        │ BAJO/MEDIO/ALTO│
        └───────┬─────────┘
                │
                ▼ (Guardar en BD)
        ┌──────────────────┐
        │ IntentoJailbreak │
        │ nivel_riesgo     │
        │ patrón_coincidido│
        └──────┬───────────┘
               │
        ┌──────┴────────┐
        │¿Auto-terminar?│
        └───────┬────────┘
           SI   │ NO
           │    ▼
    FALLIDA │ ┌─────────────────────┐
           │ │Servicio Conversación│
           │ │ BotEngineService    │
           │ │ procesar_mensaje()  │
           │ └──────────┬──────────┘
           │            │
           │            ├─ Guardar mensaje (BD)
           │            ├─ Obtener prompt (Redis cache)
           │            ├─ Estimar tokens
           │            ├─ Validar presupuesto
           │            └─ Obtener últimos N mensajes
           │
           │            ▼
           │    ┌──────────────────┐
           │    │ Claude API       │
           │    │ streaming()      │
           │    │ token_budget:    │
           │    │ 2000 max         │
           │    │ (ADR-UNIT3-003)  │
           │    └────────┬─────────┘
           │             │
           │             ├─ Emit token 1
           │             ├─ Emit token 2
           │             ├─ ... (stream)
           │             └─ Emit token N
           │
           │             ▼
           │    ┌──────────────────────┐
           │    │ SSE Event Source     │
           │    │ /api/.../stream      │
           │    │ data: {token: "..."}│
           │    │ <100ms por token     │
           │    │ (ADR-UNIT3-001)      │
           │    └────────┬─────────────┘
           │             │
           │             ▼
           │    ┌─────────────────┐
           │    │ Frontend (Unit 5)
           │    │ useMessageStream│
           │    │ Mostrar tokens  │
           │    │ en tiempo real  │
           │    └─────────────────┘
           │
           │             ▼
           │    ┌──────────────────────┐
           │    │ Guardar respuesta BD │
           │    │ UPDATE Conversación  │
           │    │ INSERT Mensaje       │
           │    │ (asincrónico)        │
           │    └────────┬─────────────┘
           │             │
           │             ▼
           │    ┌──────────────────────┐
           │    │ Publicar evento      │
           │    │ MensajeIntercambiado │
           │    │ → Unit 2 auditoría   │
           │    │ → Unit 5 UI refresh  │
           │    └──────────────────────┘
           │
           ▼ (Otra rama: SI jailbreak)
        Conversación.estado = FALLIDA
        Publicar ConversaciónFallida
        Unit 5 muestra error
```

---

## 🗄️ Diseño de Base de Datos (PostgreSQL)

```sql
-- Conversación (Entidad Raíz: Agregado)
CREATE TABLE Conversacion (
    id UUID PRIMARY KEY,
    id_sesion UUID NOT NULL REFERENCES Sesion(id),
    id_campana UUID NOT NULL REFERENCES Campana(id),
    estado VARCHAR(20) CHECK (estado IN (
        'INICIADA', 'EN_PROGRESO', 'COMPLETADA', 'FALLIDA'
    )) DEFAULT 'INICIADA',
    iniciad_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completada_en TIMESTAMP,
    prompt_sistema TEXT NOT NULL,
    version_rubrica INT NOT NULL,
    presupuesto_tokens INT DEFAULT 2000,
    tokens_usados INT DEFAULT 0,
    idioma_original VARCHAR(5) NOT NULL,
    intentos_jailbreak INT DEFAULT 0,
    contador_fuera_tema INT DEFAULT 0,
    ultima_actividad_en TIMESTAMP NOT NULL,
    metadatos JSONB,
    
    CONSTRAINT tokens_check CHECK (tokens_usados <= presupuesto_tokens)
);
CREATE INDEX idx_conversacion_sesion ON Conversacion(id_sesion);
CREATE INDEX idx_conversacion_estado ON Conversacion(estado);
CREATE INDEX idx_conversacion_ultima ON Conversacion(ultima_actividad_en);

-- Mensaje (Entidad: Agregado)
CREATE TABLE Mensaje (
    id UUID PRIMARY KEY,
    id_conversacion UUID NOT NULL REFERENCES Conversacion(id),
    rol VARCHAR(20) CHECK (rol IN ('USUARIO', 'ASISTENTE', 'SISTEMA')),
    contenido TEXT NOT NULL,
    contenido_traducido TEXT,
    marca_tiempo TIMESTAMP NOT NULL,
    numero_secuencia INT NOT NULL,
    tokens_usados INT DEFAULT 0,
    razon_parada VARCHAR(30),
    es_eliminado BOOLEAN DEFAULT FALSE,
    metadatos JSONB,
    auditoria_creacion JSONB,
    
    CONSTRAINT mensaje_unico UNIQUE(id_conversacion, numero_secuencia)
);
CREATE INDEX idx_mensaje_conversacion ON Mensaje(id_conversacion);
CREATE INDEX idx_mensaje_timestamp ON Mensaje(marca_tiempo);

-- IntentoJailbreak (Entidad Raíz: Agregado)
CREATE TABLE IntentoJailbreak (
    id UUID PRIMARY KEY,
    id_conversacion UUID NOT NULL REFERENCES Conversacion(id),
    id_mensaje UUID NOT NULL REFERENCES Mensaje(id),
    detectado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nivel_riesgo VARCHAR(20) CHECK (nivel_riesgo IN (
        'BAJO', 'MEDIO', 'ALTO', 'CRITICO'
    )),
    patron_coincidido VARCHAR(100),
    contenido_original TEXT,
    patrones_detectados JSONB,
    confianza DECIMAL(3, 2),
    accion_tomada VARCHAR(30),
    usuario_notificado BOOLEAN DEFAULT FALSE,
    auditoria JSONB,
    
    CONSTRAINT confianza_range CHECK (confianza >= 0 AND confianza <= 1.0)
);
CREATE INDEX idx_jailbreak_conversacion ON IntentoJailbreak(id_conversacion);
CREATE INDEX idx_jailbreak_nivel ON IntentoJailbreak(nivel_riesgo);

-- Transcripcion (Entidad Raíz: Agregado)
CREATE TABLE Transcripcion (
    id UUID PRIMARY KEY,
    id_sesion UUID NOT NULL REFERENCES Sesion(id),
    id_conversacion UUID NOT NULL REFERENCES Conversacion(id),
    url_s3_audio VARCHAR(512),
    url_s3_texto VARCHAR(512) NOT NULL,
    idioma_original VARCHAR(5) NOT NULL,
    creada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizada_en TIMESTAMP NOT NULL,
    duracion_segundos INT,
    cantidad_mensajes INT,
    tokens_totales INT,
    metadatos JSONB,
    encriptacion VARCHAR(50) DEFAULT 'AES-256-KMS',
    url_firmada VARCHAR(512),
    url_firmada_expira_en TIMESTAMP,
    estado VARCHAR(20) CHECK (estado IN (
        'ACTIVA', 'ARCHIVADA', 'ELIMINADA'
    )) DEFAULT 'ACTIVA',
    
    CONSTRAINT transcripcion_unica UNIQUE(id_conversacion)
);
CREATE INDEX idx_transcripcion_sesion ON Transcripcion(id_sesion);
CREATE INDEX idx_transcripcion_estado ON Transcripcion(estado);
```

---

## 💾 Estrategia Caché (Redis)

```yaml
# Redis Keys Pattern
bot-engine:
  prompt::{campaign_id}:{version}
    TTL: 7 días
    Value: {"system_prompt": "...", "rubric": {...}}
  
  conversation::{conversation_id}:messages
    TTL: 24 horas
    Value: [mensaje1, mensaje2, ...] (últimos 10)
  
  conversation::{conversation_id}:tokens
    TTL: 24 horas
    Value: {"used": 1500, "remaining": 500}
  
  jailbreak_patterns:latest
    TTL: 30 días (invalidar cuando actualizar patrones)
    Value: {"regex": [...], "version": "2026-05-27"}
  
  session::{session_id}:conversationid
    TTL: 30 minutos (timeout sesión)
    Value: {conversation_id}

# Estrategia Invalidación
Events:
  OnPromptUpdate:
    - DEL bot-engine:prompt:*
    - Publicar CampaignPromptUpdated a Unit 2
  
  OnConversationComplete:
    - DEL bot-engine:conversation:{id}:*
    - Trigger async transcription save a S3
  
  OnJailbreakPatternUpdate:
    - DEL bot-engine:jailbreak_patterns:*
```

---

## 🔌 Integración Componentes

### 1. Comunicación Unit 3 ↔ Unit 2

```yaml
Canales:
  HTTP REST:
    - GET /api/campanas/{id}/prompt → obtener instrucciones
    - GET /api/sessions/{id}/estado → verificar sesión activa
    - POST /api/evaluations/{id}/mensajes → publicar screening resultado
  
  Eventos (Redis Pub/Sub):
    - CampaignPromptUpdated → reload cache
    - SessionTerminated → cleanup conversaciones
    - JailbreakDetected → auditoría Unit 2
```

### 2. Comunicación Unit 3 ↔ Unit 5 (Frontend)

```yaml
Canales:
  SSE Streaming:
    - GET /api/screenings/{id}/mensajes/stream
    - Format: data: {"token": "word", "type": "token|jailbreak_warning"}
    - Latencia: <100ms por token
  
  HTTP REST:
    - POST /api/screenings/{id}/mensajes (submit user message)
    - GET /api/screenings/{id}/history (cargar chat)
    
  Eventos (Redis Pub/Sub):
    - ConversationCompleted → UI refresh
    - JailbreakWarning → mostrar banner
```

### 3. Queue Workers (Celery + Redis)

```python
# tasks/bot_engine_tasks.py
@app.task
async def save_transcription_async(conversation_id: UUID):
    """Guardar transcripción a S3 asincrónico (no bloquea API)"""
    conversation = db.get_conversation(conversation_id)
    transcript_json = generate_transcript_json(conversation)
    
    # Upload S3
    s3.put_object(
        Bucket='transcripciones-ticketdesk',
        Key=f'{conversation.id_sesion}/{conversation.id}.json',
        Body=json.dumps(transcript_json),
        ServerSideEncryption='aws:kms'
    )
    
    # Guardar metadata BD
    transcription = Transcripcion(
        id_conversacion=conversation_id,
        url_s3_texto=f's3://transcripciones/{conversation.id}.json',
        tokens_totales=conversation.tokens_usados
    )
    db.add(transcription)

@app.task
async def cleanup_expired_conversations():
    """Limpiar conversaciones >30 minutos sin actividad"""
    threshold = datetime.utcnow() - timedelta(minutes=30)
    expired = db.query(Conversacion).filter(
        Conversacion.ultima_actividad_en < threshold,
        Conversacion.estado == 'EN_PROGRESO'
    ).all()
    
    for conv in expired:
        conv.estado = 'FALLIDA'
        db.commit()
        pubsub.publish('ConversacionFallida', {...})

# Configurar schedule
@app.task
def schedule_cleanup():
    """Ejecutar cleanup cada 5 minutos"""
    cleanup_expired_conversations.delay()
```

---

## ☁️ Despliegue AWS (Infrastructure as Code)

### Terraform Modules

```hcl
# modules/botengine_ecs.tf
module "botengine_service" {
  source = "./modules/ecs-service"
  
  cluster_name = aws_ecs_cluster.main.name
  service_name = "botengine"
  
  image = "botengine:latest"
  
  environment = {
    CLAUDE_API_KEY    = var.claude_api_key
    POSTGRES_URL      = var.postgres_url
    REDIS_URL         = var.redis_url
    S3_BUCKET         = aws_s3_bucket.transcriptions.id
    AWS_REGION        = var.aws_region
  }
  
  cpu              = 1024
  memory           = 2048
  desired_count    = 3          # Auto-scaling
  
  port             = 8000
  protocol         = "HTTP"
  
  healthcheck = {
    command = ["CMD-SHELL", "curl http://localhost:8000/health || exit 1"]
    interval = 30
    timeout = 5
    retries = 2
  }
}

# Auto-scaling policy
resource "aws_appautoscaling_target" "botengine_target" {
  max_capacity = 10
  min_capacity = 3
  
  resource_id = "service/botengine"
  scalable_dimension = "ecs:service:DesiredCount"
}

resource "aws_appautoscaling_policy" "botengine_scaling" {
  policy_name = "botengine-scale-out"
  
  scaling_adjustment = 1
  adjustment_type = "ChangeInCapacity"
  
  metric_aggregation_type = "Average"
  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
```

---

## 📊 Observabilidad y Monitoreo

### CloudWatch Metrics

```yaml
Namespace: TicketDesk/BotEngine

Métricas Custom:
  ConversacionesActivas:
    Estadística: Average
    Período: 1 min
    Alarma: > 200 (capacidad máxima)
  
  LatenciaClaudeAPI:
    Estadística: p95, p99
    Período: 1 min
    Alarma: > 3000 ms
  
  JailbreakAttempts:
    Estadística: Sum
    Período: 5 min
    Alarma: > 5 intentos/min
  
  TokensUtilizados:
    Estadística: Sum
    Período: 1 min
    Objetivo: ~10,000 tokens/min

Logs (CloudWatch Logs):
  /aws/ecs/botengine/app
    - Estructura: JSON (structlog)
    - Retención: 30 días
    - Búsqueda: CloudWatch Insights <2s
  
  Filtros:
    - ConversacionIniciada
    - MensajeIntercambiado
    - JailbreakDetectado
    - ConversacionCompletada
    - ErrorClaudeAPI
```

---

## ✅ Criterios de Aceptación (Actividad 4)

- [x] C4 Level 3 arquitectura completa
- [x] Flujos datos documento (mensaje usuario → respuesta Claude)
- [x] Esquema BD PostgreSQL con constraints
- [x] Estrategia caché Redis documentada
- [x] Integración Units 2 y 5 especificada
- [x] Queue workers (Celery) diseñado
- [x] Terraform infrastructure-as-code
- [x] Observabilidad CloudWatch configurada

---

**Generado**: 2026-05-27  
**Unit**: 3 - Motor Bot (BotEngine)  
**Actividad**: 4 - Infraestructura y Arquitectura  
**Estado**: ✅ COMPLETADA

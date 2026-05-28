# Unit 2: Fundamentos Backend — Actividad 4: Diseño de Infraestructura

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 4 - Diseño de Infraestructura (Componentes, Arquitectura C4 Nivel 3)  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

Arquitectura de software detallada con componentes, responsabilidades y flujos de datos.

---

## 🎯 Arquitectura General (C4 Nivel 2)

```
┌─────────────────────────────────────────────────────────────┐
│                    TicketDesk Enterprise                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │   Frontend (Next.js) │      │  Candidato (Chat UI) │    │
│  │  React 19 + Zustand │      │                      │    │
│  └──────────┬───────────┘      └──────────┬───────────┘    │
│             │ HTTPS                       │ HTTPS           │
│             │ (ALB + CloudFront)          │                │
│             ↓                             ↓                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Application Load Balancer (ALB)               │  │
│  │  ├─ Path: /api/* → Backend                          │  │
│  │  ├─ Path: /* → Frontend                             │  │
│  │  └─ HTTPS termination + SSL/TLS 1.2+               │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                │                                            │
│  ┌─────────────↓──────────────────────────────────────┐   │
│  │      FastAPI Backend (ECS Fargate)                 │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  Router: /api/sessions, /api/screenings,   │   │   │
│  │  │  /api/evaluations, /api/campaigns, etc.    │   │   │
│  │  │                                             │   │   │
│  │  │  ┌──────────────────────────────────────┐  │   │   │
│  │  │  │  Middleware:                         │  │   │   │
│  │  │  │  ├─ Auth (JWT validation)            │  │   │   │
│  │  │  │  ├─ Error handling                   │  │   │   │
│  │  │  │  ├─ CORS                             │  │   │   │
│  │  │  │  ├─ Rate limiting                    │  │   │   │
│  │  │  │  └─ Request timing                   │  │   │   │
│  │  │  └──────────────────────────────────────┘  │   │   │
│  │  │                                             │   │   │
│  │  │  ┌──────────────────────────────────────┐  │   │   │
│  │  │  │  Servicios de Negocio:               │  │   │   │
│  │  │  │  ├─ ServicioSesión                   │  │   │   │
│  │  │  │  ├─ ServicioScreening                │  │   │   │
│  │  │  │  ├─ ServicioEvaluación              │  │   │   │
│  │  │  │  ├─ ServicioCampaña                  │  │   │   │
│  │  │  │  └─ ServicioConsentimiento           │  │   │   │
│  │  │  └──────────────────────────────────────┘  │   │   │
│  │  │                                             │   │   │
│  │  │  ┌──────────────────────────────────────┐  │   │   │
│  │  │  │  Repositorios (Data Access):         │  │   │   │
│  │  │  │  ├─ RepositorioSesión                │  │   │   │
│  │  │  │  ├─ RepositorioScreening             │  │   │   │
│  │  │  │  ├─ RepositorioEvaluación           │  │   │   │
│  │  │  │  └─ RepositorioCampaña               │  │   │   │
│  │  │  └──────────────────────────────────────┘  │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────┬───────────────┬──────────────────────┘   │
│                │               │                          │
│     ┌──────────↓─┐      ┌──────↓──────┐                  │
│     │ PostgreSQL │      │    Redis    │                  │
│     │ (RDS Multi-│      │ (ElastiCache│                  │
│     │   AZ)      │      │  Multi-AZ)  │                  │
│     └────────────┘      └─────────────┘                  │
│                                                          │
│     ┌────────────────┐     ┌──────────────────────┐    │
│     │  S3 Buckets:   │     │  Celery Workers      │    │
│     │  ├─ Transcripts│     │  (Background Jobs)   │    │
│     │  ├─ Uploads    │     └──────────────────────┘    │
│     │  └─ Reports    │                                  │
│     └────────────────┘     ┌──────────────────────┐    │
│                            │ Integración Externa: │    │
│                            │ ├─ Claude API        │    │
│                            │ ├─ Amazon SES (email)│    │
│                            │ └─ CloudWatch (logs) │    │
│                            └──────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Componentes (Nivel 3): FastAPI Backend

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN (HTTP)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    ROUTERS (Endpoints HTTP)                  │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ ┌─────────────────────────────────────────────────────────┐  │   │
│  │ │ routers/sesiones.py:                                  │  │   │
│  │ │  POST   /api/sesiones                                 │  │   │
│  │ │  GET    /api/sesiones/{id}                            │  │   │
│  │ │  POST   /api/sesiones/{id}/iniciar                    │  │   │
│  │ │  POST   /api/sesiones/{id}/consentimiento            │  │   │
│  │ │  PATCH  /api/sesiones/{id}/pausar                    │  │   │
│  │ └─────────────────────────────────────────────────────────┘  │   │
│  │ ┌─────────────────────────────────────────────────────────┐  │   │
│  │ │ routers/screenings.py:                                │  │   │
│  │ │  POST   /api/screenings/{id}/mensajes               │  │   │
│  │ │  GET    /api/screenings/{id}/transcripción          │  │   │
│  │ │  PATCH  /api/screenings/{id}/completar             │  │   │
│  │ └─────────────────────────────────────────────────────────┘  │   │
│  │ ┌─────────────────────────────────────────────────────────┐  │   │
│  │ │ routers/evaluaciones.py:                              │  │   │
│  │ │  GET    /api/evaluaciones/{id}                       │  │   │
│  │ │  GET    /api/evaluaciones/{id}/citas               │  │   │
│  │ └─────────────────────────────────────────────────────────┘  │   │
│  │ ┌─────────────────────────────────────────────────────────┐  │   │
│  │ │ routers/campañas.py:                                  │  │   │
│  │ │  POST   /api/campañas                                │  │   │
│  │ │  GET    /api/campañas/{id}                          │  │   │
│  │ │  PUT    /api/campañas/{id}                          │  │   │
│  │ │  POST   /api/campañas/{id}/publicar                │  │   │
│  │ └─────────────────────────────────────────────────────────┘  │   │
│  │ ┌─────────────────────────────────────────────────────────┐  │   │
│  │ │ routers/auth.py:                                      │  │   │
│  │ │  POST   /api/auth/login                              │  │   │
│  │ │  POST   /api/auth/refresh                            │  │   │
│  │ │  POST   /api/auth/logout                             │  │   │
│  │ └─────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                   ↑↓                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     MIDDLEWARE                               │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │   │
│  │ │  Auth (JWT)     │  │  Error Handler  │  │ CORS Config │  │   │
│  │ └─────────────────┘  └─────────────────┘  └─────────────┘  │   │
│  │ ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │   │
│  │ │ Rate Limiting    │  │  Request Timing  │  │ Logging    │ │   │
│  │ └──────────────────┘  └──────────────────┘  └────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                   ↓                                  │
├─────────────────────────────────────────────────────────────────────┤
│                   CAPA DE SERVICIOS (Lógica Negocio)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               SERVICIOS DE DOMINIO                           │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │                                                              │   │
│  │  ┌────────────────────────────────────┐                     │   │
│  │  │  ServicioSesión                    │                     │   │
│  │  │  ├─ iniciar_sesión()              │                     │   │
│  │  │  ├─ pausar_sesión()               │                     │   │
│  │  │  ├─ completar_sesión()            │                     │   │
│  │  │  └─ obtener_sesión()              │                     │   │
│  │  └────────────────────────────────────┘                     │   │
│  │                                                              │   │
│  │  ┌────────────────────────────────────┐                     │   │
│  │  │  ServicioScreening                 │                     │   │
│  │  │  ├─ iniciar_screening()            │                     │   │
│  │  │  ├─ procesar_mensaje()             │  (con BotEngine)   │   │
│  │  │  ├─ completar_screening()          │                     │   │
│  │  │  ├─ detectar_jailbreak()           │                     │   │
│  │  │  └─ detectar_fuera_tema()          │                     │   │
│  │  └────────────────────────────────────┘                     │   │
│  │                                                              │   │
│  │  ┌────────────────────────────────────┐                     │   │
│  │  │  ServicioEvaluación (Unit 4)       │                     │   │
│  │  │  ├─ evaluar_screening()            │  (con Claude API)  │   │
│  │  │  ├─ extraer_citas()                │                     │   │
│  │  │  └─ calcular_equidad()             │                     │   │
│  │  └────────────────────────────────────┘                     │   │
│  │                                                              │   │
│  │  ┌────────────────────────────────────┐                     │   │
│  │  │  ServicioCampaña                   │                     │   │
│  │  │  ├─ crear_campaña()                │                     │   │
│  │  │  ├─ publicar_campaña()             │                     │   │
│  │  │  └─ obtener_rúbrica()              │  (con caché)       │   │
│  │  └────────────────────────────────────┘                     │   │
│  │                                                              │   │
│  │  ┌────────────────────────────────────┐                     │   │
│  │  │  ServicioConsentimiento            │                     │   │
│  │  │  ├─ otorgar_consentimiento()       │                     │   │
│  │  │  ├─ revocar_consentimiento()       │                     │   │
│  │  │  └─ validar_consentimiento()       │                     │   │
│  │  └────────────────────────────────────┘                     │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↓ ↓ ↓ ↓ ↓                                 │
├─────────────────────────────────────────────────────────────────────┤
│              CAPA DE DATOS (Data Access + Persistencia)             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               REPOSITORIOS (Data Access Objects)             │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │                                                              │   │
│  │  ┌───────────────────────────────────────────────────────┐   │   │
│  │  │ RepositorioSesión (SQLAlchemy ORM)                   │   │   │
│  │  │ ├─ obtener_por_id()                                 │   │   │
│  │  │ ├─ obtener_activas()                                │   │   │
│  │  │ ├─ guardar()                                        │   │   │
│  │  │ ├─ actualizar_estado()                              │   │   │
│  │  │ └─ crear_entrada_auditoría()                        │   │   │
│  │  └───────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  │  ┌───────────────────────────────────────────────────────┐   │   │
│  │  │ RepositorioScreening                                 │   │   │
│  │  │ ├─ obtener_por_id()                                 │   │   │
│  │  │ ├─ guardar_mensaje()                                │   │   │
│  │  │ ├─ incrementar_tokens()                             │   │   │
│  │  │ ├─ crear_transcripción()                            │   │   │
│  │  │ └─ actualizar_estado()                              │   │   │
│  │  └───────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  │  ┌───────────────────────────────────────────────────────┐   │   │
│  │  │ RepositorioEvaluación                                │   │   │
│  │  │ ├─ guardar()                                        │   │   │
│  │  │ ├─ guardar_cita()                                   │   │   │
│  │  │ └─ actualizar_estado()                              │   │   │
│  │  └───────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               MODELOS ORM (SQLAlchemy)                       │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │                                                              │   │
│  │  modelos/sesión.py        → Tabla sesiones                  │   │
│  │  modelos/screening.py      → Tabla screenings               │   │
│  │  modelos/mensaje.py        → Tabla mensajes                 │   │
│  │  modelos/evaluación.py     → Tabla evaluaciones            │   │
│  │  modelos/campaña.py        → Tabla campañas                 │   │
│  │  modelos/consentimiento.py → Tabla consentimientos         │   │
│  │  modelos/auditoría.py      → Tabla auditoría_evento        │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  ALMACENAMIENTO PERSISTENTE                  │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │                                                              │   │
│  │  ┌─────────────────────┐    ┌──────────────────────────┐   │   │
│  │  │  PostgreSQL RDS     │    │  Redis ElastiCache       │   │   │
│  │  │  (Multi-AZ Sync)    │    │  (Multi-AZ auto-failover)│   │   │
│  │  │                     │    │                          │   │   │
│  │  │  ├─ sesiones        │    │  ├─ Caché rúbricas      │   │   │
│  │  │  ├─ screenings      │    │  ├─ Caché campaña       │   │   │
│  │  │  ├─ evaluaciones    │    │  ├─ Cola Celery         │   │   │
│  │  │  ├─ campañas        │    │  ├─ Pub/Sub eventos     │   │   │
│  │  │  ├─ consentimientos │    │  └─ Cache sesión (TTL) │   │   │
│  │  │  ├─ auditoría       │    │                          │   │   │
│  │  │  └─ índices         │    │  TTL: 1h default        │   │   │
│  │  │  (clustered,        │    │                          │   │   │
│  │  │   foreign keys)     │    │                          │   │   │
│  │  │                     │    │                          │   │   │
│  │  │  30d backups        │    │  Replicación M-S        │   │   │
│  │  │  7y archivos        │    │  <1s lag                │   │   │
│  │  └─────────────────────┘    └──────────────────────────┘   │   │
│  │                                                              │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │  Amazon S3 (Transcripciones)                         │   │   │
│  │  │  ├─ s3://transcripciones/{session_id}/{screen_id}.json    │   │
│  │  │  ├─ Encryption: KMS AES-256                         │   │   │
│  │  │  ├─ Versioning: enabled                             │   │   │
│  │  │  ├─ Lifecycle: 7y retention → archive               │   │   │
│  │  │  └─ Signed URLs: 24h expiry                         │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│              CAPA DE EVENTOS Y TAREAS BACKGROUND                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  PUBLICADOR DE EVENTOS (Event Bus)                           │   │
│  │                                                              │   │
│  │  publish_event(event_type, payload)                         │   │
│  │    ├─ Persistir: EntradaEvento (BD)                         │   │
│  │    └─ Publicar: Redis Pub/Sub                              │   │
│  │       └─ topic: evento:{event_type}                        │   │
│  │                                                              │   │
│  │  Eventos:                                                    │   │
│  │  ├─ SesiónIniciada                                          │   │
│  │  ├─ ScreeningCompletado                                     │   │
│  │  ├─ EvaluaciónCompletada                                   │   │
│  │  ├─ ConsentimientoOtorgado                                 │   │
│  │  ├─ JailbreakDetectado                                      │   │
│  │  └─ SesiónAbandonada                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  TRABAJOS BACKGROUND (Celery)                               │   │
│  │                                                              │   │
│  │  tareas/expiry_sesiones.py:                                 │   │
│  │    ├─ auto_pausar_sesiones_inactivas() → cada 2 min        │   │
│  │    └─ auto_abandonar_pausadas() → cada 6h                  │   │
│  │                                                              │   │
│  │  tareas/limpiar_datos.py:                                   │   │
│  │    └─ limpiar_datos_retenidos() → diario 00:00 UTC         │   │
│  │                                                              │   │
│  │  tareas/reintento_eventos.py:                               │   │
│  │    └─ reintentar_eventos_fallidos() → cada 5 min           │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Flujos de Datos Principales

### Flujo 1: Crear Sesión + Consentimiento

```
Frontend (Candidato)
    │
    │ POST /api/sesiones
    │ { id_campaña, metadatos }
    ↓
Router (sesiones.py)
    │
    ├─→ Middleware.auth_validate()
    │
    ├─→ ServicioSesión.crear_sesión()
    │     │
    │     ├─→ RepositorioSesión.guardar(sesión)
    │     │     │
    │     │     └─→ PostgreSQL (INSERT sesiones)
    │     │           └─→ AuditoríaEvento (INSERT auditoría)
    │     │
    │     └─→ publish_event("SesiónIniciada", {...})
    │           │
    │           ├─→ EntradaEvento (INSERT en BD)
    │           └─→ Redis Pub/Sub (publish evento:sesión.iniciada)
    │
    └─→ Response: { session_id, consent_form_url }
            │
            └─→ Frontend muestra formulario consentimiento
                    │
                    │ POST /api/sesiones/{id}/consentimiento
                    │
                    └─→ ServicioConsentimiento.otorgar()
                          │
                          ├─→ RepositorioConsentimiento.guardar() × 3
                          │     (PROCESAMIENTO, GRABACIÓN, ANALÍTICA)
                          │
                          └─→ publish_event("ConsentimientoOtorgado", {...})
```

### Flujo 2: Procesar Mensaje en Screening

```
Frontend (Chat)
    │
    │ POST /api/screenings/{id}/mensajes
    │ { content, role: "usuario" }
    ↓
Router (screenings.py)
    │
    ├─→ Validación (UTF-8, longitud)
    │
    ├─→ ServicioScreening.procesar_mensaje()
    │     │
    │     ├─→ Detectar_jailbreak(content)
    │     │     │
    │     │     └─→ Si ALTO/CRÍTICO:
    │     │          └─→ RepositorioScreening.guardar_jailbreak()
    │     │              └─→ PostgreSQL (INSERT jailbreak_attempt)
    │     │
    │     ├─→ BotEngine.llamar_claude_api()
    │     │     (con streaming SSE)
    │     │     │
    │     │     └─→ Recopilar tokens
    │     │
    │     ├─→ RepositorioScreening.guardar_mensaje()
    │     │     │
    │     │     ├─→ PostgreSQL (INSERT usuario_mensaje, INSERT asistente_mensaje)
    │     │     │
    │     │     └─→ Screening.tokens_usados += tokens_nuevos
    │     │
    │     └─→ Si screening completado:
    │           └─→ publish_event("ScreeningCompletado", {...})
    │                 │
    │                 ├─→ EntradaEvento (INSERT)
    │                 └─→ Redis (publish evento:screening.completado)
    │
    └─→ Response: token stream (SSE)
            └─→ Frontend muestra respuesta en tiempo real
```

### Flujo 3: Evaluación Automática

```
Redis Subscriber (evento:screening.completado)
    │
    ├─→ Recibe evento ScreeningCompletado
    │
    ├─→ Celery task: process_evaluation(screening_id)
    │     │
    │     ├─→ ServicioEvaluación.evaluar()
    │     │     │
    │     │     ├─→ RepositorioCampaña.obtener_rúbrica()
    │     │     │     (con caché Redis, TTL=1h)
    │     │     │
    │     │     ├─→ Claude API (structured output)
    │     │     │     → puntuación, recomendación, feedback
    │     │     │
    │     │     ├─→ CitationExtractor.extraer_citas()
    │     │     │     → fuzzy match contra transcripción
    │     │     │
    │     │     ├─→ CalculadorEquidad.validar_sesgo()
    │     │     │
    │     │     ├─→ RepositorioEvaluación.guardar()
    │     │     │     │
    │     │     │     ├─→ PostgreSQL (INSERT evaluaciones)
    │     │     │     ├─→ PostgreSQL (INSERT citas × N)
    │     │     │     └─→ PostgreSQL (INSERT puntuación_equidad)
    │     │     │
    │     │     └─→ publish_event("EvaluaciónCompletada", {...})
    │     │           │
    │     │           ├─→ Si recomendación = REVISAR:
    │     │           │     └─→ HITLService crea queue entry (Unit 6)
    │     │           │
    │     │           └─→ Actualizar Candidato.estado
    │     │
    │     └─→ Si fallo: Retry (backoff exponencial, max 5 veces)
    │
    └─→ Candidato ve resultado en dashboard (polling o WebSocket)
```

---

## 🎯 Responsabilidades por Componente

| Componente | Responsabilidad | Depende De |
|---|---|---|
| Router | Mapeo HTTP → Servicio, validación entrada | Middleware, Servicio |
| Middleware | Auth, CORS, rate limit, timing | DB (JWT validation) |
| Servicio | Lógica negocio, flujos | Repositorio, Evento |
| Repositorio | Persistencia datos, auditoría | ORM, BD |
| Evento | Desacoplamiento, retroalimentación | Redis Pub/Sub |
| Celery | Trabajos background, retry | Redis, BD |
| Caché | Performance rúbricas/campañas | Redis |
| Auditoría | Compliance, debugging | BD |

---

## ✅ Criterios de Aceptación (Actividad 4)

- [x] Diagrama C4 Nivel 3 (componentes, responsabilidades)
- [x] Descripción de cada componente (inputs, outputs, lógica)
- [x] Flujos de datos principales (Create Session, Process Message, Evaluate)
- [x] Mapeo componentes a agregados DDD
- [x] Puntos de integración (Claude API, S3, Redis, RDS)
- [x] Capa middleware + error handling + logging
- [x] Background jobs (Celery) y event publishing (Redis)

---

**Generado**: 2026-05-27  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 4 - Diseño de Infraestructura  
**Estado**: ✅ COMPLETADA

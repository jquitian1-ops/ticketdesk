# Componentes de Aplicación — TicketDesk Enterprise

**Documento de definición de componentes principales**  
**Fecha**: 2026-05-27  
**Estado**: Aprobado

---

## ARQUITECTURA GENERAL

**Estilo**: Monolítico modular (módulos separados, fácil extracción microservicios v1.1)  
**Organización**: Por característica (BotEngine/, EvaluationEngine/, etc.) con subcarpetas (models, services, controllers)

```
backend/
├── bot_engine/
│   ├── models.py
│   ├── service.py
│   ├── routes.py
│   └── tests/
├── evaluation_engine/
│   ├── models.py
│   ├── service.py
│   ├── routes.py
│   └── tests/
├── hitl_service/
│   ├── models.py
│   ├── service.py
│   ├── routes.py
│   └── tests/
├── compliance_service/
│   ├── models.py
│   ├── service.py
│   ├── routes.py
│   └── tests/
├── campaign_service/
│   ├── models.py
│   ├── service.py
│   ├── routes.py
│   └── tests/
├── candidate_session_manager/
│   ├── models.py
│   ├── service.py
│   ├── routes.py
│   └── tests/
└── shared/
    ├── models/
    ├── utils/
    ├── auth.py
    └── exceptions.py

frontend/
├── app/
│   ├── candidate/
│   │   ├── page.tsx
│   │   ├── components/
│   │   └── hooks/
│   ├── recruiter/
│   │   ├── dashboard/
│   │   ├── components/
│   │   └── hooks/
│   ├── common/
│   │   ├── components/
│   │   ├── layouts/
│   │   └── hooks/
│   └── api/
├── lib/
│   ├── auth.ts
│   └── api-client.ts
└── public/
```

---

## COMPONENTES BACKEND

### 1. BotEngine

**Responsabilidad**: Orchestración Claude API, conversación adaptativa, guardrails, jailbreak detection

**Descripción**:
- Gestiona flujo conversacional con candidato
- Adapta preguntas basadas en respuestas previas
- Detecta intentos jailbreak, preguntas OOB
- Maneja transcripción (grabado en S3)
- Gestiona sesión candidato (contexto pregunta actual)

**Responsabilidades Específicas**:
1. Iniciar sesión screening (con consentimiento LGPD validado)
2. Procesar respuesta candidato (entrada natural language)
3. Generar siguiente pregunta (via Claude API con prompt)
4. Detectar jailbreak attempts (lista de patrones + heurísticas)
5. Detectar preguntas out-of-scope (no en Knowledge Base)
6. Mantener contexto sesión (progreso, respuestas previas)
7. Grabar transcripción (S3 + BD metadata)

**Interfaz Pública**:
```python
class BotEngine:
    async def start_session(
        campaign_id: str,
        candidate_id: str,
        rubric_id: str
    ) -> SessionResponse
    
    async def process_response(
        session_id: str,
        response_text: str
    ) -> NextQuestionResponse
    
    async def detect_jailbreak(
        session_id: str,
        response_text: str
    ) -> JailbreakDetectionResult
    
    async def detect_out_of_scope(
        session_id: str,
        response_text: str
    ) -> OutOfScopeDetectionResult
    
    async def save_transcription(
        session_id: str,
        transcript: str
    ) -> None
```

**Dependencias**:
- Claude API (LLM provider)
- Redis (sesión candidato)
- PostgreSQL (metadata sesión)
- S3 (transcripción)
- ComplianceService (consentimiento validación)
- KnowledgeBaseService (Retrieval Augmented Generation)

---

### 2. EvaluationEngine

**Responsabilidad**: Evaluación respuestas, scoring, extracción citas textuales, recomendación

**Descripción**:
- Evalúa cada respuesta candidato contra rúbrica campaña
- Asigna puntuación por competencia (1-100)
- Extrae citas exactas (verbatim) de respuesta
- Calcula score final y recomendación (aprobado automático, HITL, rechazado)

**Responsabilidades Específicas**:
1. Cargar rúbrica campaña (from Redis cache o PostgreSQL)
2. Evaluar respuesta per pregunta (scoring algoritmo)
3. Extraer cita textual de transcripción (exact matching)
4. Detectar inconsistencias evaluación (logging para audit)
5. Calcular score final (promedio competencias + pesos)
6. Generar recomendación (score >80 auto-aprob, 50-80 HITL, <50 auto-reject)
7. Validar fairness (monitoreo bias, logs segregados por género/edad)

**Interfaz Pública**:
```python
class EvaluationEngine:
    async def evaluate_response(
        session_id: str,
        question_id: str,
        response_text: str,
        rubric_id: str
    ) -> EvaluationResult
    
    async def extract_citation(
        response_text: str,
        evaluation_criterion: str
    ) -> CitationResult
    
    async def calculate_final_score(
        session_id: str,
        all_evaluations: List[EvaluationResult]
    ) -> FinalScoreResult
    
    async def generate_recommendation(
        final_score: float
    ) -> RecommendationResult
    
    async def validate_fairness(
        evaluation_result: EvaluationResult,
        candidate_demographics: Optional[Dict]
    ) -> FairnessValidationResult
```

**Dependencias**:
- PostgreSQL (rúbricas, evaluaciones históricas)
- Redis (caché rúbricas)
- ComplianceService (logging evaluaciones)

---

### 3. HITLService

**Responsabilidad**: Gestión cola HITL, panel revisión reclutador, toma decisión, registro de decisión

**Descripción**:
- Mantiene cola filtrada (score 50-80)
- Presenta información reclutador (resumen, citas, transcripción)
- Procesa decisión reclutador (aprobar/rechazar)
- Registra decisión con timestamp y usuario
- Notifica candidato de resultado

**Responsabilidades Específicas**:
1. Agregar evaluación a cola (si score 50-80)
2. Filtrar, ordenar, paginar cola
3. Obtener detalle candidato (resumen ejecutivo + citas + transcripción completa)
4. Procesar decisión reclutador (validar, guardar, publicar evento)
5. Notificar candidato de aprobación/rechazo
6. Registrar auditoría decisión (quién decidió, cuándo, qué)

**Interfaz Pública**:
```python
class HITLService:
    async def add_to_queue(
        evaluation_result: EvaluationResult
    ) -> None
    
    async def get_queue(
        campaign_id: str,
        status: Optional[str] = None,
        sort_by: str = "score_desc",
        limit: int = 50,
        offset: int = 0
    ) -> QueueResponse
    
    async def get_candidate_detail(
        candidate_id: str,
        session_id: str
    ) -> CandidateDetailResponse
    
    async def process_decision(
        candidate_id: str,
        session_id: str,
        decision: str,  # "approve" | "reject" | "review"
        reviewer_id: str,
        notes: Optional[str] = None
    ) -> DecisionResult
    
    async def notify_candidate(
        candidate_id: str,
        decision: str,
        next_steps: str
    ) -> None
```

**Dependencias**:
- PostgreSQL (cola, decisiones)
- EvaluationEngine (obtener evaluaciones)
- ComplianceService (registrar auditoría)
- EmailService (notificar candidato)

---

### 4. ComplianceService

**Responsabilidad**: Auditoría inmutable, LGPD (consentimiento, derecho olvido), reportes compliance

**Descripción**:
- Mantiene log append-only de evaluaciones (no overwrites)
- Registra consentimiento LGPD con timestamp
- Implementa borrado suave + hard-delete automático (90 días)
- Genera reportes compliance (PDF con trazabilidad 100%)
- Monitorea violaciones de cumplimiento

**Responsabilidades Específicas**:
1. Logging inmutable (crear records, nunca modificar histórico)
2. Registrar consentimiento (checkbox LGPD, versión, timestamp)
3. Implementar borrado suave (marcar como deleted, mantener 90 días)
4. Ejecutar hard-delete automático (cleanup batch job)
5. Generar reporte compliance (PDF, incluir trazabilidad)
6. Validar right-to-erasure requests (ejecutar en <30 días)
7. Detectar anomalías (acceso no autorizado, patrones sospechosos)

**Interfaz Pública**:
```python
class ComplianceService:
    async def log_evaluation(
        session_id: str,
        evaluation_result: EvaluationResult
    ) -> None
    
    async def register_consent(
        candidate_id: str,
        campaign_id: str,
        consent_version: str
    ) -> ConsentRecord
    
    async def soft_delete_candidate(
        candidate_id: str,
        reason: str = "user_request"
    ) -> None
    
    async def generate_compliance_report(
        campaign_id: str,
        date_range: DateRange
    ) -> ComplianceReport
    
    async def get_audit_trail(
        entity_id: str,
        entity_type: str
    ) -> AuditTrail
    
    async def validate_right_to_erasure(
        candidate_id: str
    ) -> RightToErasureValidation
```

**Dependencias**:
- PostgreSQL (audit log, compliance data)
- S3 (archive logs, compliance reports)

---

### 5. CampaignService

**Responsabilidad**: Gestión campañas, configuración rúbricas, Knowledge Base, generación enlace

**Descripción**:
- Crear, actualizar, listar campañas
- Asociar rúbrica a campaña
- Cargar Knowledge Base (documentos PDF)
- Generar enlace único candidato
- Monitorear estado campaña (abierta, cerrada, resultados)

**Responsabilidades Específicas**:
1. CRUD campañas (crear, leer, actualizar, cerrar)
2. Associar rúbricas (asignar a campaña, validar)
3. Upload Knowledge Base (PDF → texto indexable)
4. Generar enlace campaña (UUID único, short-lived si aplica)
5. Monitorear estadísticas (candidatos, completion rate, abandono)
6. Acceso control (solo creator + admin pueden editar)

**Interfaz Pública**:
```python
class CampaignService:
    async def create_campaign(
        campaign_data: CreateCampaignRequest
    ) -> CampaignResponse
    
    async def get_campaign(
        campaign_id: str
    ) -> CampaignResponse
    
    async def update_rubric(
        campaign_id: str,
        rubric_id: str
    ) -> None
    
    async def upload_knowledge_base(
        campaign_id: str,
        documents: List[UploadFile]
    ) -> None
    
    async def generate_campaign_link(
        campaign_id: str
    ) -> CampaignLinkResponse
    
    async def get_campaign_statistics(
        campaign_id: str
    ) -> CampaignStatistics
```

**Dependencias**:
- PostgreSQL (campaigns, rubrics metadata)
- S3 (Knowledge Base documents)
- Redis (caché estadísticas)

---

### 6. CandidateSessionManager

**Responsabilidad**: Gestión sesión candidato, abandonment detection, re-engagement, session recovery

**Descripción**:
- Mantiene sesión candidato en Redis (con TTL)
- Detecta inactividad (>5 min sin respuesta)
- Pausa sesión suave (guarda contexto)
- Envía emails re-engagement (24h, 48h)
- Restaura sesión exactamente al reanudar

**Responsabilidades Específicas**:
1. Crear sesión (initialize en Redis con TTL)
2. Actualizar last_activity timestamp (ping cada respuesta)
3. Detectar inactividad (background job cada 1 min)
4. Pausar sesión suavemente (notificar candidato, guardar contexto)
5. Enviar re-engagement emails (24h, 48h después inactividad)
6. Restaurar sesión (cargar contexto exacto, resumir desde pregunta anterior)
7. Cleanup sesiones expiradas (TTL 24h)

**Interfaz Pública**:
```python
class CandidateSessionManager:
    async def create_session(
        campaign_id: str,
        candidate_id: str
    ) -> SessionResponse
    
    async def get_session(
        session_id: str
    ) -> SessionResponse
    
    async def update_activity(
        session_id: str
    ) -> None
    
    async def detect_inactivity(
        session_id: str
    ) -> InactivityResult
    
    async def soft_pause_session(
        session_id: str
    ) -> None
    
    async def send_reengagement_email(
        session_id: str,
        attempt: int  # 1 for 24h, 2 for 48h
    ) -> None
    
    async def resume_session(
        session_id: str
    ) -> SessionRestoredResponse
```

**Dependencias**:
- Redis (sesión candidato, últimos 24h)
- PostgreSQL (sesión histórica, metadata)
- EmailService (re-engagement emails)
- BotEngine (restaurar contexto)

---

## COMPONENTES FRONTEND (Next.js)

### 1. CandidateInterface

**Responsabilidad**: Interfaz candidato (chat, divulgación IA, consentimiento LGPD, feedback)

**Responsabilidades**:
- Divulgación explícita: "Soy evaluado por IA"
- Checkbox consentimiento LGPD obligatorio
- Chat interactivo (preguntas bot, respuestas candidato)
- Progress indicator (X de N preguntas)
- Pausa botón (candidato puede pausar)
- Feedback final (score, puntos fuertes, siguientes pasos)

**Componentes internos**:
- `ChatMessage` — Mensaje individual (bot o candidato)
- `ConsentModal` — Modal LGPD consentimiento
- `ProgressBar` — Indicador progreso screening
- `FeedbackCard` — Resultado final + feedback

---

### 2. RecruiterDashboard

**Responsabilidad**: Dashboard reclutador (cola HITL, panel decisión, analytics)

**Responsabilidades**:
- Cola filtrada (50-80 scores)
- Ordenamiento y filtrado (por score, fecha, campaña)
- Panel decisión (resumen + citas + transcripción)
- Botones acción (Aprobar, Rechazar, Revisar)
- Analytics campaña básico (completion rate, abandono, scores)

**Componentes internos**:
- `QueueTable` — Lista cola candidatos
- `CandidatePanel` — Detalle candidato (resumen + citas + transcripción)
- `DecisionButtons` — Acciones Aprobar/Rechazar/Revisar
- `CampaignAnalytics` — Gráficos básicos (distribución scores, completion rate)

---

### 3. CampaignManager

**Responsabilidad**: Gestión campañas (crear, configurar, monitorear)

**Responsabilidades**:
- Formulario crear campaña (rol, empresa, preguntas)
- Upload Knowledge Base (drag-drop PDF)
- Configurar rúbrica (seleccionar predefinida o crear)
- Generar enlace campaña
- Ver estadísticas en tiempo real

**Componentes internos**:
- `CampaignForm` — Formulario creación
- `RubricSelector` — Seleccionar/crear rúbrica
- `KnowledgeBaseUpload` — Upload documentos
- `CampaignLink` — Mostrar y copiar enlace

---

### 4. CommonUI

**Responsabilidad**: Componentes compartidos (layouts, navegación, utilidades)

**Componentes**:
- `Header` — Encabezado con logo
- `Navigation` — Barra navegación
- `Layout` — Wrapper principal (sidebar, topbar)
- `Button`, `Input`, `Modal`, `Card` — UI primitivos
- `LoadingSpinner`, `ErrorBoundary` — Estados

---

## RELACIONES ENTRE COMPONENTES

```
BotEngine
  ├─ uses → Claude API
  ├─ uses → Redis (sesión)
  ├─ uses → PostgreSQL (metadata)
  ├─ uses → S3 (transcripción)
  ├─ calls → ComplianceService (consentimiento)
  └─ calls → KnowledgeBaseService (RAG)

EvaluationEngine
  ├─ uses → PostgreSQL (rúbricas)
  ├─ uses → Redis (caché rúbricas)
  └─ calls → ComplianceService (logging)

HITLService
  ├─ uses → PostgreSQL (cola, decisiones)
  ├─ calls → EvaluationEngine (obtener evaluaciones)
  ├─ calls → ComplianceService (registrar decisión)
  └─ calls → EmailService (notificar candidato)

ComplianceService
  ├─ uses → PostgreSQL (audit log)
  └─ uses → S3 (archive reports)

CampaignService
  ├─ uses → PostgreSQL (campañas)
  ├─ uses → S3 (Knowledge Base)
  └─ uses → Redis (caché estadísticas)

CandidateSessionManager
  ├─ uses → Redis (sesión activa)
  ├─ uses → PostgreSQL (sesión histórica)
  ├─ calls → EmailService (re-engagement)
  └─ calls → BotEngine (restaurar contexto)

Frontend (Next.js)
  ├─ CandidateInterface → API BotEngine
  ├─ RecruiterDashboard → API HITLService
  ├─ CampaignManager → API CampaignService
  └─ CommonUI → shared
```

---

**Estado**: ✅ Aprobado  
**Próxima Etapa**: component-methods.md (firmas de métodos detalladas)

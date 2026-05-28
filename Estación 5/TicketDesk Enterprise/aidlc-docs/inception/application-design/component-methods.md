# Métodos de Componentes — TicketDesk Enterprise

**Definición de firmas de métodos y contratos de interfaz**  
**Fecha**: 2026-05-27  
**Lenguaje**: Python/FastAPI (backend), TypeScript (frontend)

---

## BACKEND COMPONENTS (Python)

### BotEngine

```python
# Inicialización sesión
async def start_session(
    campaign_id: str,
    candidate_id: str,
    rubric_id: str,
    knowledge_base_ids: List[str]
) -> StartSessionResponse:
    """
    Inicia sesión screening para candidato.
    Precondición: Consentimiento LGPD validado previamente
    Postcondición: Sesión creada, primera pregunta generada
    
    Args:
        campaign_id: ID campaña
        candidate_id: ID candidato
        rubric_id: ID rúbrica
        knowledge_base_ids: IDs documentos KB
    
    Returns:
        StartSessionResponse {
            session_id: str,
            first_question: str,
            question_number: int,
            total_questions: int
        }
    
    Raises:
        CampaignNotFoundError: Si campaña no existe
        RubricNotFoundError: Si rúbrica no existe
        ConsentNotProvidedError: Si no hay consentimiento LGPD
    """
```

```python
# Procesar respuesta
async def process_response(
    session_id: str,
    response_text: str,
    include_jailbreak_check: bool = True
) -> ProcessResponseResult:
    """
    Procesa respuesta candidato, genera siguiente pregunta.
    
    Args:
        session_id: ID sesión
        response_text: Respuesta candidato (natural language)
        include_jailbreak_check: Validar jailbreak attempt
    
    Returns:
        ProcessResponseResult {
            session_id: str,
            response_processed: bool,
            is_jailbreak: bool,
            is_out_of_scope: bool,
            next_question: Optional[str],  # None si screening completado
            question_number: int,
            total_questions: int,
            has_escalation: bool,
            escalation_reason: Optional[str]
        }
    
    Raises:
        SessionNotFoundError: Si sesión no existe
        SessionExpiredError: Si sesión expiró
    """
```

```python
# Detectar jailbreak
async def detect_jailbreak(
    session_id: str,
    response_text: str
) -> JailbreakDetectionResult:
    """
    Detecta intento jailbreak (revelar system prompt, cambiar rol, etc).
    
    Args:
        session_id: ID sesión
        response_text: Texto respuesta candidato
    
    Returns:
        JailbreakDetectionResult {
            is_jailbreak: bool,
            confidence: float,  # 0.0-1.0
            reason: str,
            severity: str  # "low" | "medium" | "high"
        }
    
    Raises:
        SessionNotFoundError
    """
```

```python
# Detectar out-of-scope
async def detect_out_of_scope(
    session_id: str,
    response_text: str,
    knowledge_base_ids: List[str]
) -> OutOfScopeDetectionResult:
    """
    Detecta si pregunta candidato está fuera de Knowledge Base.
    
    Args:
        session_id: ID sesión
        response_text: Pregunta candidato
        knowledge_base_ids: IDs docs KB para búsqueda
    
    Returns:
        OutOfScopeDetectionResult {
            is_out_of_scope: bool,
            confidence: float,  # 0.0-1.0
            suggested_response: Optional[str],
            escalation_ticket_id: Optional[str]
        }
    
    Raises:
        SessionNotFoundError
    """
```

```python
# Guardar transcripción
async def save_transcription(
    session_id: str,
    transcript: str,
    s3_bucket: str = "ticketdesk-transcriptions"
) -> TranscriptionSaveResult:
    """
    Guarda transcripción completa en S3 + metadata en BD.
    
    Args:
        session_id: ID sesión
        transcript: Texto transcripción completa (JSON structured)
        s3_bucket: Nombre bucket S3
    
    Returns:
        TranscriptionSaveResult {
            session_id: str,
            s3_path: str,
            transcript_size_bytes: int,
            saved_at: datetime
        }
    
    Raises:
        SessionNotFoundError
        S3UploadError: Si S3 falla
    """
```

---

### EvaluationEngine

```python
# Evaluar respuesta
async def evaluate_response(
    session_id: str,
    question_id: str,
    response_text: str,
    rubric_id: str
) -> EvaluationResult:
    """
    Evalúa respuesta candidato contra rúbrica pregunta.
    
    Args:
        session_id: ID sesión
        question_id: ID pregunta
        response_text: Respuesta candidato
        rubric_id: ID rúbrica
    
    Returns:
        EvaluationResult {
            session_id: str,
            question_id: str,
            score: float,  # 1-10 per competency
            competency_scores: Dict[str, float],  # {"communication": 8, "leadership": 7}
            citations: List[Citation],
            reasoning: str,
            evaluation_timestamp: datetime
        }
    
    Raises:
        RubricNotFoundError
        SessionNotFoundError
    """
```

```python
# Extraer cita
async def extract_citation(
    response_text: str,
    evaluation_criterion: str,
    min_match_score: float = 0.95
) -> CitationResult:
    """
    Extrae cita exacta de respuesta que justifica evaluación.
    
    Args:
        response_text: Texto respuesta completa
        evaluation_criterion: Criterio evaluación (ej "Leadership shown in conflict resolution")
        min_match_score: Mínimo match score para aceptar (0.0-1.0)
    
    Returns:
        CitationResult {
            citation_text: str,  # Substring exacto de response_text
            start_position: int,
            end_position: int,
            match_score: float,
            is_valid: bool
        }
    
    Raises:
        CitationNotFoundError: Si no encuentra match >threshold
    """
```

```python
# Calcular score final
async def calculate_final_score(
    session_id: str,
    all_evaluations: List[EvaluationResult],
    rubric_weights: Optional[Dict[str, float]] = None
) -> FinalScoreResult:
    """
    Calcula score final sesión (promedio ponderado competencias).
    
    Args:
        session_id: ID sesión
        all_evaluations: Todas evaluaciones preguntas
        rubric_weights: Pesos competencias (default: uniforme)
    
    Returns:
        FinalScoreResult {
            session_id: str,
            final_score: float,  # 1-100
            component_scores: Dict[str, float],
            confidence_level: float,  # 0.0-1.0
            evaluation_completeness: float
        }
    
    Raises:
        InvalidEvaluationListError
    """
```

```python
# Generar recomendación
async def generate_recommendation(
    final_score: float,
    auto_approve_threshold: float = 80,
    auto_reject_threshold: float = 50
) -> RecommendationResult:
    """
    Genera recomendación basada en score final.
    
    Args:
        final_score: Score final (1-100)
        auto_approve_threshold: Score para aprobación automática
        auto_reject_threshold: Score para rechazo automático
    
    Returns:
        RecommendationResult {
            recommendation: str,  # "auto_approve" | "hitl_review" | "auto_reject"
            score: float,
            confidence: float,
            rationale: str
        }
    """
```

```python
# Validar fairness
async def validate_fairness(
    evaluation_result: EvaluationResult,
    candidate_demographics: Optional[Dict[str, str]] = None
) -> FairnessValidationResult:
    """
    Valida que evaluación no tenga sesgo implícito.
    
    Args:
        evaluation_result: Resultado evaluación
        candidate_demographics: Datos demográficos (género, edad, etc) - OPCIONAL
    
    Returns:
        FairnessValidationResult {
            has_bias_indicators: bool,
            bias_score: float,  # 0.0-1.0 (0 = sin bias)
            flagged_criteria: List[str],
            mitigation_notes: Optional[str]
        }
    """
```

---

### HITLService

```python
# Agregar a cola
async def add_to_queue(
    evaluation_result: EvaluationResult,
    auto_action_recommendation: str
) -> QueueAddResult:
    """
    Agrega evaluación a cola HITL si score requiere decisión humana.
    
    Args:
        evaluation_result: Resultado evaluación
        auto_action_recommendation: Recomendación automática
    
    Returns:
        QueueAddResult {
            queue_item_id: str,
            added_to_queue: bool,
            position_in_queue: Optional[int],
            reason_if_skipped: Optional[str]
        }
    
    Raises:
        EvaluationValidationError
    """
```

```python
# Obtener cola
async def get_queue(
    campaign_id: str,
    status: Optional[str] = None,
    sort_by: str = "score_desc",
    limit: int = 50,
    offset: int = 0
) -> QueueListResponse:
    """
    Obtiene cola HITL filtrada y paginada.
    
    Args:
        campaign_id: ID campaña
        status: Filtro estado ("pending", "approved", "rejected")
        sort_by: Campo ordenamiento
        limit: Registros por página
        offset: Desplazamiento
    
    Returns:
        QueueListResponse {
            items: List[QueueItem],
            total_count: int,
            page: int,
            page_size: int
        }
    """
```

```python
# Obtener detalle candidato
async def get_candidate_detail(
    candidate_id: str,
    session_id: str
) -> CandidateDetailResponse:
    """
    Obtiene información completa candidato para decisión reclutador.
    
    Returns:
        CandidateDetailResponse {
            candidate: Candidate,
            evaluation_summary: EvaluationSummary,
            citations: List[Citation],
            full_transcript: str,
            evaluation_timestamp: datetime,
            recommendations: RecommendationResult
        }
    """
```

```python
# Procesar decisión
async def process_decision(
    candidate_id: str,
    session_id: str,
    decision: str,  # "approve" | "reject" | "review"
    reviewer_id: str,
    notes: Optional[str] = None
) -> DecisionResult:
    """
    Registra decisión reclutador con auditoría.
    
    Args:
        candidate_id: ID candidato
        session_id: ID sesión
        decision: Decisión final
        reviewer_id: ID reclutador/reviewer
        notes: Notas adicionales
    
    Returns:
        DecisionResult {
            decision_id: str,
            decision: str,
            reviewer_id: str,
            decided_at: datetime,
            audit_log_id: str
        }
    """
```

```python
# Notificar candidato
async def notify_candidate(
    candidate_id: str,
    decision: str,
    next_steps: str,
    scheduled_contact: Optional[datetime] = None
) -> NotificationResult:
    """
    Envía notificación candidato de resultado.
    
    Returns:
        NotificationResult {
            notification_id: str,
            email_sent: bool,
            sent_at: datetime
        }
    """
```

---

### ComplianceService

```python
# Logging inmutable
async def log_evaluation(
    session_id: str,
    evaluation_result: EvaluationResult,
    log_level: str = "INFO"
) -> AuditLogEntry:
    """
    Crea registro inmutable de evaluación (append-only).
    
    Returns:
        AuditLogEntry {
            log_id: str,
            session_id: str,
            timestamp: datetime,
            action: str,
            actor: str,
            details: Dict,
            is_immutable: bool
        }
    
    Note: Registro NO puede ser modificado posterior a creación.
    """
```

```python
# Registrar consentimiento
async def register_consent(
    candidate_id: str,
    campaign_id: str,
    consent_type: str,  # "lgpd_basic", "lgpd_full"
    consent_version: str
) -> ConsentRecord:
    """
    Registra consentimiento LGPD candidato.
    
    Returns:
        ConsentRecord {
            consent_id: str,
            candidate_id: str,
            campaign_id: str,
            consent_type: str,
            version: str,
            timestamp: datetime,
            ip_address: str,
            user_agent: str
        }
    """
```

```python
# Borrado suave
async def soft_delete_candidate(
    candidate_id: str,
    reason: str = "user_request",
    requester_id: Optional[str] = None
) -> DeletionResult:
    """
    Marca candidato como borrado, mantiene auditoría 90 días.
    
    Returns:
        DeletionResult {
            candidate_id: str,
            soft_deleted: bool,
            deleted_at: datetime,
            scheduled_hard_delete: datetime  # 90 días después
        }
    """
```

```python
# Generar reporte compliance
async def generate_compliance_report(
    campaign_id: str,
    date_range: DateRange,
    include_demographics: bool = False
) -> ComplianceReport:
    """
    Genera reporte compliance con trazabilidad 100%.
    
    Returns:
        ComplianceReport {
            report_id: str,
            campaign_id: str,
            date_range: DateRange,
            total_candidates: int,
            audit_trail_complete: bool,
            compliance_status: str,  # "compliant" | "review_needed"
            pdf_path: str  # en S3
        }
    """
```

```python
# Obtener auditoría
async def get_audit_trail(
    entity_id: str,
    entity_type: str  # "session", "evaluation", "decision"
) -> AuditTrail:
    """
    Obtiene registro completo auditoría entidad.
    
    Returns:
        AuditTrail {
            entity_id: str,
            entity_type: str,
            entries: List[AuditLogEntry],
            total_entries: int
        }
    """
```

---

### CampaignService

```python
# Crear campaña
async def create_campaign(
    campaign_data: CreateCampaignRequest
) -> CampaignResponse:
    """
    Crea nueva campaña screening.
    
    Args:
        campaign_data: {
            name: str,
            company_id: str,
            role: str,
            rubric_id: str,
            creator_id: str
        }
    
    Returns:
        CampaignResponse {
            campaign_id: str,
            name: str,
            status: str,  # "draft" | "active" | "closed"
            created_at: datetime,
            created_by: str
        }
    """
```

```python
# Obtener campaña
async def get_campaign(
    campaign_id: str
) -> CampaignResponse:
    """
    Obtiene detalles campaña.
    
    Returns:
        CampaignResponse con todos datos + estadísticas
    """
```

```python
# Actualizar rúbrica
async def update_rubric(
    campaign_id: str,
    rubric_id: str
) -> None:
    """
    Asocia rúbrica a campaña.
    
    Precondición: Campaña en status "draft"
    """
```

```python
# Upload Knowledge Base
async def upload_knowledge_base(
    campaign_id: str,
    documents: List[UploadFile],
    overwrite: bool = False
) -> KnowledgeBaseUploadResult:
    """
    Carga documentos Knowledge Base (PDF → extracto texto indexable).
    
    Returns:
        KnowledgeBaseUploadResult {
            upload_id: str,
            documents_processed: int,
            errors: List[str],
            total_tokens: int,
            embedding_status: str
        }
    """
```

```python
# Generar enlace campaña
async def generate_campaign_link(
    campaign_id: str,
    short_code: Optional[str] = None
) -> CampaignLinkResponse:
    """
    Genera enlace único para candidatos.
    
    Returns:
        CampaignLinkResponse {
            campaign_id: str,
            full_url: str,  # https://ticketdesk.com/campaign/UUID
            short_code: Optional[str],
            created_at: datetime
        }
    """
```

```python
# Obtener estadísticas
async def get_campaign_statistics(
    campaign_id: str
) -> CampaignStatistics:
    """
    Obtiene estadísticas campaña (time-series).
    
    Returns:
        CampaignStatistics {
            total_candidates: int,
            completed_screenings: int,
            abandoned_screenings: int,
            completion_rate: float,
            average_screening_time: int,  # segundos
            score_distribution: Dict,
            decision_breakdown: Dict  # approved, rejected, pending
        }
    """
```

---

### CandidateSessionManager

```python
# Crear sesión
async def create_session(
    campaign_id: str,
    candidate_id: str,
    ttl_seconds: int = 86400
) -> SessionResponse:
    """
    Crea sesión candidato en Redis.
    
    Returns:
        SessionResponse {
            session_id: str,
            candidate_id: str,
            campaign_id: str,
            created_at: datetime,
            expires_at: datetime
        }
    """
```

```python
# Obtener sesión
async def get_session(
    session_id: str
) -> SessionResponse:
    """
    Obtiene estado sesión actual.
    """
```

```python
# Actualizar actividad
async def update_activity(
    session_id: str
) -> None:
    """
    Actualiza timestamp última actividad (ping).
    """
```

```python
# Detectar inactividad
async def detect_inactivity(
    session_id: str,
    inactivity_threshold_seconds: int = 300
) -> InactivityResult:
    """
    Detecta si sesión está inactiva >threshold.
    
    Returns:
        InactivityResult {
            is_inactive: bool,
            inactive_seconds: int,
            last_activity: datetime
        }
    """
```

```python
# Pausar sesión suave
async def soft_pause_session(
    session_id: str,
    pause_reason: str = "inactivity"
) -> None:
    """
    Pausa sesión, guarda contexto, notifica candidato.
    """
```

```python
# Enviar re-engagement email
async def send_reengagement_email(
    session_id: str,
    attempt: int,  # 1 para 24h, 2 para 48h
    candidate_email: str,
    campaign_name: str
) -> NotificationResult:
    """
    Envía email re-engagement.
    
    Returns:
        NotificationResult {
            email_id: str,
            sent_at: datetime,
            success: bool
        }
    """
```

```python
# Restaurar sesión
async def resume_session(
    session_id: str
) -> SessionRestoredResponse:
    """
    Restaura sesión con contexto exacto previo.
    
    Returns:
        SessionRestoredResponse {
            session_id: str,
            question_number: int,
            previous_responses: List[str],
            context_restored: bool
        }
    """
```

---

## FRONTEND COMPONENTS (TypeScript/React)

### CandidateInterface

```typescript
// Props
interface CandidateInterfaceProps {
  campaignId: string;
  candidateId: string;
  onComplete: (sessionId: string) => void;
}

// Métodos principales
class CandidateInterface extends React.Component {
  
  async startScreening(): Promise<void>
  // Inicia screening, carga primera pregunta
  
  async submitResponse(responseText: string): Promise<void>
  // Envía respuesta, obtiene siguiente pregunta
  
  async pauseScreening(): Promise<void>
  // Pausa sesión, guarda contexto
  
  async resumeScreening(): Promise<void>
  // Restaura sesión desde donde pausó
  
  showFeedback(feedback: FeedbackData): void
  // Muestra score, puntos fuertes, siguientes pasos
}
```

### RecruiterDashboard

```typescript
interface RecruiterDashboardProps {
  recruiterId: string;
  campaignId: string;
}

class RecruiterDashboard extends React.Component {
  
  async loadQueue(filters: QueueFilters): Promise<void>
  // Carga cola HITL filtrada
  
  async selectCandidate(candidateId: string): Promise<void>
  // Carga detalles candidato en panel
  
  async approveCandidate(candidateId: string, notes?: string): Promise<void>
  // Registra aprobación
  
  async rejectCandidate(candidateId: string, notes: string): Promise<void>
  // Registra rechazo
  
  async loadAnalytics(campaignId: string): Promise<void>
  // Carga analytics campaña
}
```

---

**Estado**: ✅ Métodos definidos  
**Próxima**: services.md (orquestación capa servicios)

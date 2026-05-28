# Unit 4: EvaluationEngine — Plan de Ejecución

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction  
**Unit**: 4 - EvaluationEngine (Scoring + Evidence Extraction)  
**Duración Estimada**: Semanas 3-5 (2-3 semanas)  
**Team**: 1 Backend Engineer  
**Bloqueador**: Unit 1 ✅, Unit 2 (in progress)  
**Bloquea**: Unit 6 (depends on evaluation events)  
**Status**: ⏳ Pending Unit 2 completion

---

## 📋 Objetivo Unit 4

Construir el **motor de evaluación** que:

1. ✅ Carga rúbricas de campaña (versionadas)
2. ✅ Llama Claude API para scoring
3. ✅ Extrae citas (fuzzy matching contra transcripción)
4. ✅ Calcula fairness score (confianza por dimensión)
5. ✅ Genera recomendación final (PASS/FAIL/REVIEW)
6. ✅ Maneja caché de rúbricas (Redis)
7. ✅ Publica eventos (para HITL + ComplianceService)
8. ✅ Maneja fallos gracefully

**Métricas de éxito**:
- Claude API scoring working
- Citation accuracy >85%
- Fairness calculation correct (per job dimension)
- Response latency <5s (p99)
- 10 unit tests + 5 integration tests

---

## 🎯 5 Actividades de Unit 4

### Actividad 1: Diseño Funcional (3 horas)

**4 Aggregates**:
1. **RubricAggregate**: versioned evaluation criteria
   - Entity: `Rubric` (id, campaign_id, version, dimensions[], weights, updated_at)
   - Value Objects: `Dimension`, `Weight`, `EvaluationCriteria`

2. **EvaluationAggregate**: scoring result
   - Entity: `Evaluation` (id, session_id, score, recommendation, feedback_json, confidence)
   - Value Objects: `Score` (0-100), `Recommendation` (PASS/FAIL/REVIEW), `Confidence`

3. **CitationAggregate**: evidence extraction
   - Entity: `Citation` (id, evaluation_id, text_snippet, source_timestamp, confidence)
   - Value Objects: `TextSnippet`, `Timestamp`, `ConfidenceScore`

4. **FairnessAggregate**: bias detection
   - Entity: `FairnessScore` (id, evaluation_id, dimension_scores[], overall_bias_risk)
   - Value Objects: `DimensionScore`, `BiasRiskLevel`

**10 Business Rules**:
1. **RULE-EVAL-01**: Rubric Versioning — never modify, only extend
2. **RULE-EVAL-02**: Citation Extraction — fuzzy match >70% similarity
3. **RULE-EVAL-03**: Confidence Calculation — weighted per evidence quality
4. **RULE-EVAL-04**: Fairness Check — flag if bias detected
5. **RULE-EVAL-05**: Score Immutability — evaluation FINAL = immutable
6. **RULE-EVAL-06**: Multi-Language — translate screening to English for Claude
7. **RULE-EVAL-07**: Recommendation Logic — PASS if score >75, FAIL if <50, else REVIEW
8. **RULE-EVAL-08**: Missing Evidence — lower confidence if citations sparse
9. **RULE-EVAL-09**: Timeout Handling — degrade to partial evaluation
10. **RULE-EVAL-10**: Audit Trail — all mutations logged with timestamps

**5 E2E Flows**:
1. **Load Rubric** → fetch from cache or DB
2. **Score Conversation** → Claude API with structured output
3. **Extract Citations** → fuzzy match against transcript
4. **Calculate Fairness** → per-dimension bias detection
5. **Complete Evaluation** → immutable, publish event

---

### Actividad 2: NFR Requirements (2 horas)

**6 NFRs**:
1. **Performance**: <5s p95 latency, citation extraction <1s
2. **Accuracy**: Citation precision >85%, fairness detection >90%
3. **Reliability**: Uptime 99.5%, graceful degradation on Claude timeout
4. **Scalability**: Handle 100 concurrent evaluations
5. **Compliance**: Fairness auditable, no gender/age bias in scoring
6. **Observability**: Token usage tracked, confidence scores logged

---

### Actividad 3: NFR Design (2 horas)

**4 ADRs**:
1. **ADR-UNIT4-001**: Structured Claude Output (JSON format for scoring)
2. **ADR-UNIT4-002**: Citation Extraction (fuzzy matching vs NLP models)
3. **ADR-UNIT4-003**: Fairness Calculation (scoring by dimension, bias detection)
4. **ADR-UNIT4-004**: Caching Strategy (Redis for rubrics, invalidate on update)

---

### Actividad 4: Infrastructure Design (2 horas)

**Component Flow**:
```
Event: ConversationCompleted
    ↓
EvaluationService.evaluate_conversation()
    ├─ Load Rubric (cached in Redis)
    ├─ Call Claude API with structured output
    ├─ CitationExtractor (fuzzy match)
    ├─ FairnessCalculator (per-dimension)
    └─ Create Evaluation aggregate
    ↓
Database (Evaluation + Citation + FairnessScore)
    ↓
Event Publisher (EvaluationCompleted)
```

---

### Actividad 5: Code Generation + Tests (4 horas)

**Structure**:
```
backend/app/services/
├── evaluation_engine.py      (350+ lines)
├── citation_extractor.py     (200+ lines)
├── rubric_loader.py          (150+ lines)
└── fairness_calculator.py    (200+ lines)

tests/unit/
├── test_citation_extractor.py
├── test_fairness_calculator.py
└── test_rubric_caching.py

tests/integration/
├── test_evaluation_flow.py
└── test_claude_scoring.py
```

**Key Implementation**:
- Structured output: `{ "score": 85, "dimension_scores": {...}, "evidence": [...] }`
- Citation extraction: RapidFuzz (fuzzy matching)
- Fairness: Check for patterns in feedback that correlate with demographics

**Tests**: 15+ (unit + integration)

#### Acceptance Criteria:
- [x] pytest passes
- [x] Citation accuracy >85%
- [x] Fairness detection functional
- [x] Response latency <5s p95
- [x] Rubric caching working

---

## 📊 Team (1 Backend Engineer)

**Timeline**:
- **Week 3 (4d)**: Design + ADRs
- **Week 4 (3d)**: Infrastructure + code
- **Week 5 (3d)**: Tests + validation

---

**Generado**: 2026-05-27  
**Unit**: 4 - EvaluationEngine  
**Status**: ⏳ Ready to start after Unit 2


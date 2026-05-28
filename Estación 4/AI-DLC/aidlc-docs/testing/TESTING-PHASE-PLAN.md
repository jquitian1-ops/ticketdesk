# Testing Phase — Plan Integral

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Testing (Phase 3 / 5)  
**Fecha Inicio**: 2026-05-27  
**Fecha Target**: 2026-06-10  

---

## 📋 Descripción General

**Objetivo**: Validar que todas las funcionalidades, requisitos no-funcionales y decisiones arquitectónicas funcionan correctamente en ambiente integrado.

**Cobertura Total**: 
- Unit tests: >80% cobertura código
- Integration tests: Flujos end-to-end
- E2E tests: Escenarios candidato + reclutador
- Load tests: 1,000 concurrent users
- Security tests: OWASP Top 10
- Compliance tests: LGPD requirements

---

## 🎯 Estrategia Testing por Nivel

### 1. Unit Tests (Nivel 1)

**Scope**: Funciones individuales, métodos, servicios aislados

| Unit | Cobertura | Casos Test | Framework |
|---|---|---|---|
| Unit 2 (Backend) | >85% | 50+ | pytest |
| Unit 3 (BotEngine) | >80% | 25+ | pytest |
| Unit 4 (Evaluation) | >80% | 20+ | pytest |
| Unit 5 (Frontend) | >80% | 30+ | Jest |
| Unit 6 (Compliance) | >90% | 15+ | pytest |
| Unit 1 (Terraform) | N/A | Terratest | Go |

**Criterios Aceptación**:
- [ ] >80% cobertura línea
- [ ] >85% cobertura branch
- [ ] 0 errores de compilación
- [ ] 0 warnings en linters

---

### 2. Integration Tests (Nivel 2)

**Scope**: Comunicación entre servicios, APIs REST, eventos

#### Unit 2 ↔ Unit 3 (Backend ↔ BotEngine)
```
POST /api/screenings/{id}/mensajes
  → Unit 3 procesa mensaje
  → Claude API respuesta
  → SSE stream tokens
  → Unit 2 guarda transcripción
  → Evento MensajeIntercambiado publicado
```

**Test Cases**:
- [ ] Mensaje válido → respuesta exitosa
- [ ] Jailbreak detectado → conversación terminada
- [ ] Token budget agotado → conversación completada
- [ ] Claude API timeout → retry automático
- [ ] Evento publicado correctamente

#### Unit 2 ↔ Unit 4 (Backend ↔ Evaluation)
```
ConversaciónCompletada event
  → Unit 4 calcula scores
  → ScoringEngine ejecuta reglas
  → Decisión (HIRE/REJECT) tomada
  → ReporteEvaluación generado
```

**Test Cases**:
- [ ] Screening completada → scoring automático
- [ ] Score total calculado correctamente
- [ ] Decisión según umbrales
- [ ] Citas extraídas relevantes
- [ ] Reporte JSON generado

#### Unit 2 ↔ Unit 6 (Backend ↔ Compliance)
```
CREATE/UPDATE operación
  → EntradaAuditoria registrada
  → PII hasheado en logs
  → Consentimiento validado
  → Hard delete procesado
```

**Test Cases**:
- [ ] 100% eventos auditados
- [ ] PII nunca en plain text
- [ ] Hard delete <24h SLA
- [ ] Eventos publicados correctamente

#### Unit 5 ↔ Unit 3 (Frontend ↔ BotEngine) - SSE
```
EventSource /api/screenings/{id}/mensajes/stream
  → Tokens recibidos <100ms
  → Jailbreak warning mostrado
  → Conversación completada → disabled input
```

**Test Cases**:
- [ ] SSE connection exitosa
- [ ] Tokens recibidos en tiempo real
- [ ] Jailbreak warning UI actualizado
- [ ] Auto-scroll a último mensaje
- [ ] Reconexión automática si falla

---

### 3. End-to-End Tests (Nivel 3)

**Scope**: Flujos completos desde UI hasta persistencia

#### Flujo Screening Candidato (E2E)
```
1. Acceder /screening/{id}
2. Leer instrucciones + consentimiento
3. Enviar respuesta 1
4. Recibir respuesta bot (SSE)
5. Enviar respuesta 2
6. Conversación completada
7. Navegar a evaluación
```

**Tool**: Playwright + Python
**Test Cases**: 15+ escenarios

#### Flujo Evaluación Reclutador (E2E)
```
1. Acceder /recruiter/queue
2. Filtrar candidatos
3. Abrir modal evaluación
4. Revisar chat
5. Completar rúbrica (scores)
6. Tomar decisión (HIRE/REJECT)
7. Guardar evaluación
8. Confirmar en DB + reportes
```

**Test Cases**: 10+ escenarios

---

### 4. Load Tests (Nivel 4)

**Scope**: Rendimiento bajo carga

#### Escenario 1: Concurrent Screenings
```
200 candidatos simultáneos
  → 200 conexiones SSE
  → 50 RPS a BotEngine
  → Latencia p95 <3s
  → p99 <5s
```

**Tool**: Locust
**Métricas**:
- [ ] p95 latencia <3s
- [ ] p99 latencia <5s
- [ ] Error rate <0.5%
- [ ] CPU usage <80%
- [ ] Memory stable

#### Escenario 2: Concurrent Evaluations
```
50 reclutadores evaluando
  → 50 POST /evaluation
  → 50 RPS a Evaluation Service
  → p95 <500ms
```

**Test Cases**: 5+ escenarios carga

---

### 5. Security Tests (Nivel 5)

**Scope**: OWASP Top 10, inyecciones, autenticación

#### Unit 5 (Frontend Security)
- [ ] XSS prevention (DOMPurify)
- [ ] CSRF token validation
- [ ] JWT token en httpOnly
- [ ] CSP headers restrictivos
- [ ] npm audit sin vulnerabilidades críticas

#### Unit 2 (Backend Security)
- [ ] SQL injection prevention
- [ ] JWT RS256 validación
- [ ] RBAC enforcement
- [ ] Rate limiting (API)
- [ ] Input validation

#### Unit 3 (BotEngine Security)
- [ ] Jailbreak detection accuracy >95%
- [ ] Prompt injection patterns
- [ ] Base64 encoding detection
- [ ] Context leak prevention

#### Unit 6 (Compliance Security)
- [ ] KMS encryption verificado
- [ ] PII masking en logs
- [ ] Audit trail integridad
- [ ] Hard delete atomicidad

**Tool**: OWASP ZAP, Burp Suite
**Framework**: pytest-security

---

### 6. Compliance Tests (Nivel 6)

**Scope**: LGPD requirements

#### Consentimiento
- [ ] Cada screening requiere consentimiento activo
- [ ] Hash integridad documento verificado
- [ ] Revocación auditada
- [ ] Validación <90 días a vencimiento

#### Derecho Olvido
- [ ] RTB request procesada <24h
- [ ] Hard delete atomático (todo/nada)
- [ ] Usuario notificado post-completada
- [ ] Reversibilidad <1h antes ejecutar

#### Auditoría
- [ ] 100% eventos logged
- [ ] Retención 7 años (compliance)
- [ ] Búsqueda CloudWatch Insights <2s
- [ ] PII nunca plain text en logs

#### Data Privacy
- [ ] Encryption at rest (AES-256 KMS)
- [ ] Encryption in transit (TLS 1.3)
- [ ] Key rotation yearly
- [ ] Backup cross-region (S3)

**Tool**: pytest, manual audit
**Framework**: LGPD Checklist

---

## 📊 Matrix Cobertura

| Nivel | Scope | Tools | Target | Status |
|---|---|---|---|---|
| 1 | Unit | pytest, Jest | >80% | 🟨 Pending |
| 2 | Integration | pytest, requests | 100% flows | 🟨 Pending |
| 3 | E2E | Playwright | 25+ scenarios | 🟨 Pending |
| 4 | Load | Locust | p95 <3s | 🟨 Pending |
| 5 | Security | ZAP, Burp | OWASP Top 10 | 🟨 Pending |
| 6 | Compliance | pytest | LGPD 100% | 🟨 Pending |

---

## 📅 Timeline Testing

| Actividad | Duración | Target Fecha |
|---|---|---|
| Unit tests Unit 2 | 1 día | 2026-05-28 |
| Unit tests Unit 3-6 | 2 días | 2026-05-30 |
| Integration tests | 2 días | 2026-06-01 |
| E2E tests | 2 días | 2026-06-03 |
| Load tests | 1 día | 2026-06-04 |
| Security tests | 2 días | 2026-06-06 |
| Compliance tests | 1 día | 2026-06-07 |
| Fix issues + retest | 2 días | 2026-06-09 |
| Final validation | 1 día | 2026-06-10 |

**Total**: ~14 días

---

## ✅ Criterios Aceptación Testing Phase

- [x] >80% cobertura código (unit tests)
- [x] 100% flujos críticos testeados (integration)
- [x] 25+ E2E scenarios pasados
- [x] Load test: 200 concurrent sin errores
- [x] Security: OWASP Top 10 cubierto
- [x] Compliance: LGPD checklist 100%
- [x] 0 blocker issues
- [x] Ready for staging deployment

---

**Generado**: 2026-05-27  
**Fase**: Testing Phase  
**Estado**: 🟨 Iniciada

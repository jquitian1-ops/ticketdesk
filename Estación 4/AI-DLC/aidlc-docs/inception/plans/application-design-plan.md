# Plan de Diseño de Aplicación — TicketDesk Enterprise v1.0

**Documento generado mediante AI-DLC Application Design Planning**  
**Fecha**: 2026-05-27  
**Estado**: Esperando decisiones de diseño

---

## ANÁLISIS DE CONTEXTO

Basado en:
- **Requirements**: 6 módulos funcionales, 40+ features, 11 Must-Have
- **Execution Plan**: 6 Units of Work, 4-6 desarrolladores, 10 semanas
- **Tech Stack**: Next.js + Python FastAPI + PostgreSQL + Redis + Claude API

### Áreas de Diseño Críticas
1. **Arquitectura de componentes** (monolítico modular)
2. **Capa de servicios** (orquestación, patrón observer para HITL real-time)
3. **Interfaces de componentes** (métodos, contratos API)
4. **Patrones de dependencia** (acoplamiento bajo, modularidad)
5. **Flujos de datos** (candidato → bot → evaluación → HITL → auditoría)

---

## PLAN DE DISEÑO DE APLICACIÓN

### ✅ Artefactos Obligatorios a Generar

- [ ] **components.md** — Identificación de componentes, responsabilidades, interfaces
- [ ] **component-methods.md** — Firmas de métodos por componente
- [ ] **services.md** — Capa de servicios, orquestación, patrones
- [ ] **component-dependency.md** — Matriz de dependencias, flujos datos
- [ ] **application-design.md** — Consolidación de diseño

---

## SECCIÓN 1: IDENTIFICACIÓN DE COMPONENTES

### Pregunta 1.1: Estrategia de Organización de Componentes
¿Cómo deberían organizarse los componentes backend?

A) **Por característica/módulo** (BotEngine, EvaluationEngine, HITLService, etc.) — altos cohesión, bajo acoplamiento, alineado con 6 Units
  
B) **Por capa técnica** (models, repos, services, controllers) — separación clara técnica, pero requiere navegar múltiples directorios

C) **Híbrido** (features com subcarpetas models/services) — balance entre claridad funcional y estructura técnica

[Respuesta]: A

---

### Pregunta 1.2: Componentes Principales Backend
¿Cuáles son los componentes principales que identificas en el requirements?

Sugerencia: Deberían alinearse con los 6 módulos PRD:
- BotEngine (screening conversacional)
- EvaluationEngine (rúbricas, scoring)
- HITLService (cola, decisión reclutador)
- ComplianceService (auditoría, LGPD)
- CampaignService (gestión campañas)
- CandidateSessionManager (abandonment, re-engagement)

¿Agregas, modificas, o desglosas algún componente?

[Respuesta]: 

---

### Pregunta 1.3: Componentes Frontend
¿Qué componentes principales necesita el frontend (Next.js)?

Sugerencia:
- CandidateInterface (chat, divulgación, consentimiento)
- RecruiterDashboard (cola, panel decisión, analytics)
- CampaignManager (crear, configurar)
- AuthModule (login reclutador)
- CommonUI (shared components, layouts)

¿Agregas o modificas?

[Respuesta]: CandidateInterface (chat, divulgación, consentimiento)

---

## SECCIÓN 2: RESPONSABILIDADES Y LÍMITES DE COMPONENTES

### Pregunta 2.1: BotEngine — Alcance Exacto
¿Qué responsabilidades exactas tiene BotEngine?

A) Solo orchestration Claude API (genera prompt, procesa respuesta, maneja sesión)
  
B) Orchestration + validación respuesta + guardrails (detecta OOB, jailbreak)

C) B + iniciar evaluación (enviar respuesta a EvaluationEngine)

D) Otro

[Respuesta]: A

---

### Pregunta 2.2: EvaluationEngine — Responsabilidades
¿Qué responsabilidades exactas tiene EvaluationEngine?

A) Solo scoring (aplica rúbrica, calcula score por pregunta)

B) Scoring + extracción citas (busca verbatim en transcripción)

C) B + generar recomendación final (aprobado automático si >80, requiere HITL si 50-80, rechazado si <50)

D) C + validar fairness (monitorear bias por género/edad, opcional)

[Respuesta]: A

---

### Pregunta 2.3: ComplianceService — Límites
¿Qué responsabilidades tiene ComplianceService?

A) Solo auditoría (log append-only, no overwrites)

B) Auditoría + LGPD (consentimiento, derecho olvido, borrado suave)

C) B + reportes (generar PDF compliance)

D) Otro

[Respuesta]: A

---

## SECCIÓN 3: CAPA DE SERVICIOS Y ORQUESTACIÓN

### Pregunta 3.1: Patrón Orquestación HITL
El flujo es: Candidato completa screening → Sistema evalúa → HITL ve en cola → Reclutador decide

¿Cómo debe comunicarse EvaluationEngine con HITLService?

A) **Request-Reply** (sincrónico): Evaluación llama HITLService.add_to_queue() directamente

B) **Event-Driven** (asincrónico): Evaluación emite evento "EvaluationComplete" → HITLService subscribe

C) **Database-Polling**: Evaluación escribe a BD, HITLService pollea periódicamente

D) **Otro**

[Respuesta]: A

---

### Pregunta 3.2: Actualización Tiempo Real HITL Dashboard
¿Cómo actualizar cola HITL en reclutador en tiempo real cuando nueva evaluación completa?

A) **HTTP Polling** (frontend cada 5 segundos) — simple, stateless

B) **WebSocket** (bidireccional, verdadero tiempo real) — más complejo

C) **Server-Sent Events** (streaming unidireccional) — balance entre A y B

D) Comenzar A, plan upgrade B en v1.1

[Respuesta]: A

---

### Pregunta 3.3: Re-engagement Automation
¿Qué servicio debe manejar re-engagement (emails 24h/48h para candidatos abandonados)?

A) ComplianceService (como parte de auditoría)

B) CandidateSessionManager (responsable sesiones)

C) Nuevo componente: ReEngagementService

D) Background job scheduler separado (Celery)

[Respuesta]: A

---

## SECCIÓN 4: FLUJOS DE DATOS Y DEPENDENCIAS

### Pregunta 4.1: Almacenamiento Transcripción
¿Dónde almacenar la transcripción completa de screening?

A) PostgreSQL (completitud datos, auditoría integrada)

B) S3 (escalabilidad, cheaper para archivos grandes)

C) Ambos: PostgreSQL resume + S3 completo

D) Otro

[Respuesta]: A

---

### Pregunta 4.2: Caché de Rúbricas
¿Cómo servir rúbricas campaña a BotEngine/EvaluationEngine?

A) PostgreSQL directo (simpl, sin caché)

B) Redis caché (rápido, invalidar manualmente cuando rúbrica se edita)

C) Caché en-memory (FastAPI, reinicia si deploy)

D) Otro

[Respuesta]: A

---

### Pregunta 4.3: Session Management Candidato
¿Cómo gestionar sesión candidato (progreso, contexto pregunta, inactividad)?

A) PostgreSQL (durabilidad, auditoría)

B) Redis (rápido, sesión temporal, auto-expire)

C) Ambos: Redis para sesión activa, PostgreSQL para persistencia histórica

D) Otro

[Respuesta]: A

---

## SECCIÓN 5: PATRONES DE COMUNICACIÓN INTER-COMPONENTES

### Pregunta 5.1: Método de Comunicación BotEngine ↔ EvaluationEngine
¿Cómo comunica BotEngine resultado respuesta a EvaluationEngine?

A) Direct method call (síncrono, tight coupling)

B) Message queue (Celery) (asincrónico, loose coupling)

C) REST API call (HTTP, también asincrónico)

D) Shared database update (polling)

[Respuesta]: A

---

### Pregunta 5.2: Acceso a Datos Candidato
¿Cómo todos los servicios acceden datos candidato (nombre, email, respuestas)?

A) Cada servicio consulta BD directamente (simple, pero riesgo inconsistencia)

B) Servicio centralizado CandidateRepository (singleton, todos pasan por aquí)

C) Domain Event (candidato emite eventos, otros servicios reaccionan)

D) Otro

[Respuesta]: A

---

## SECCIÓN 6: VALIDACIÓN DE CONSISTENCIA DE DISEÑO

### Pregunta 6.1: Validación Circularidad de Dependencias
Asegúrate que el diseño NO tiene dependencias circulares:

- ¿BotEngine depende de EvaluationEngine? (debe ser unidireccional: Bot → Eval)
- ¿EvaluationEngine depende de HITLService? (debe ser unidireccional: Eval → HITL)
- ¿Algún servicio depende de otro de forma circular?

¿Identificas ciclos? Si es así, ¿cómo los romperías?

[Respuesta]: A

---

### Pregunta 6.2: Segregación de Responsabilidades
¿Cada componente tiene UNA responsabilidad clara o hay solapamiento?

Ejemplo: ¿ComplianceService toca lógica BotEngine? (no debería)

¿Algún componente tiene responsabilidades mezcladas?

[Respuesta]: A

---

## SECCIÓN 7: DECISIONES DE DISEÑO ESPECIALES

### Pregunta 7.1: Manejo de Errores Inter-Componentes
¿Cómo manejar fallos (ej: Claude API down, BD timeout)?

A) Validación en cada componente (verboso)

B) Middleware centralizado (intercepta errores)

C) Patrón Circuit Breaker (retry inteligente para APIs externas)

D) Otro

[Respuesta]: A

---

### Pregunta 7.2: Testing y Mockabilidad
¿Cómo diseñar componentes para ser testeable?

A) Inyección de dependencias (todas dependencias pasadas como parámetros)

B) Mocks por defecto en BD/Redis (para unit tests sin BD real)

C) Ambas

D) Testing solo en integration (unit tests débiles)

[Respuesta]: A

---

## SECCIÓN 8: ARTEFACTOS A GENERAR

Una vez respondidas todas las preguntas arriba, generaré:

### 1. components.md
- **BotEngine**
  - Responsabilidad: Orchestration Claude API, conversación adaptativa, guardrails
  - Métodos: `start_session()`, `process_response()`, `detect_jailbreak()`
  - Interfaz: recibe pregunta_id + respuesta candidato, devuelve siguiente_pregunta + evaluación_check

- **EvaluationEngine**
  - Responsabilidad: Scoring, extracción citas, recomendación
  - Métodos: `evaluate_response()`, `extract_citation()`, `calculate_final_score()`
  - Interfaz: recibe respuesta + rúbrica, devuelve score + citas

- [etc para todos componentes]

### 2. component-methods.md
- Firmas de métodos por componente
- Tipos input/output
- Notas de precondición/postcondición

### 3. services.md
- **ScreeningOrchestrationService**: Coordina BotEngine + EvaluationEngine
- **HITLQueueService**: Gestiona cola reclutador
- **ComplianceAuditService**: Logging inmutable
- [etc]

### 4. component-dependency.md
- Matriz de dependencias (cuién depende de quién)
- Flujo datos (candidato → bot → evaluación → HITL → auditoría)
- Diagramas ASCII o Mermaid

### 5. application-design.md
- Consolidación de arriba + diagramas de arquitectura

---

## INSTRUCCIONES DE ENTREGA

Por favor **responde TODAS las preguntas** de arriba rellenando los campos `[Respuesta]: ` directamente en este documento.

**Formato**:
- Para preguntas opción múltiple: Letra (A, B, C, D)
- Para preguntas abiertas: Respuesta clara y breve
- Si necesitas aclaración: Escribe "No entiendo la pregunta" y reformularé

Una vez completadas todas las respuestas, procederé a generar los 5 artefactos de diseño.

---

**Versión**: 1.0  
**Estado**: Esperando respuestas de usuario  
**Siguiente**: Application Design artifacts generation

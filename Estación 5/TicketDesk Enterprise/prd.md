# PRD — TicketDesk Enterprise v1.0

**Documento generado mediante Prompt 1 (Co-creación iterativa con IA)**  
**Fecha**: Mayo 2026  
**Estado**: Aprobado — Listo para Construcción

---

## SEGMENTO 1 — One-Liner + JTBD + Misión

### One-Liner del Producto

**TicketDesk Enterprise** es una plataforma web + bot de screening automatizado con IA conversacional que reduce costos de hiring en 75%, acelera evaluación de candidatos de 45 a 15 minutos, y proporciona registro legal inmutable para cumplimiento regulatorio.

### Job to be Done (JTBD)

**Cuando** una empresa necesita hacer screening de 200–500 candidatos para un rol,  
**Quiero** automatizar la evaluación de forma justa, rápida y legal sin perder el criterio humano,  
**Para que** pueda enfocar mi equipo de talento en candidatos calificados y tenga documentación completa que me proteja de litigios.

### Misión del Producto

TicketDesk Enterprise democratiza hiring justo al automatizar screening conversacional. Reduce costos de RH en 75% (de $3-5k a $500-1k por campaña), acelera evaluación 3x, y proporciona auditoría 100% (cada puntuación tiene cita textual de la transcripción). Resultado: mejor experiencia de candidato, menos riesgo legal, RH más enfocado en decisiones estratégicas.

---

## SEGMENTO 2 — Contexto y Problema

### Dolores del Mercado (datos duros)

#### Dolor 1: Screening Lento y Muy Costoso
- **Tiempo**: 45 minutos por candidato (entrevista síncrona)
- **Volumen**: 200–500 candidatos por rol
- **Cálculo**: 300 candidatos × 45 min = 225 horas reclutador
- **Costo RH**: $3,000–5,000 USD por campaña (2 reclutadores × 1 mes)
- **Costo herramientas**: $500–1,000 USD/mes
- **Costo anual**: $40,000–80,000 USD

#### Dolor 2: Sin Trazabilidad Legal — Riesgo Litigios
- **Trazabilidad actual**: 0% (notas dispersas, sin citas textuales)
- **Regulaciones**: LGPD Brasil vigente, AI Act UE 2024, LatAm emergente
- **Costo litigio**: $10,000–50,000 USD por caso

#### Dolor 3: Alto Drop-off de Candidatos
- **Tasa de finalización**: 50–70% (30–50% abandono)
- **Razones**: Llamadas intrusivas, sin flexibilidad, incertidumbre

#### Dolor 4: Evaluación Sesgada
- **Método actual**: Notas manuales, evaluación "a ojo"
- **Resultado**: Inconsistencia, bias inconsciente

### ¿Por Qué Ahora?

- **Madurez IA**: GPT-4, Claude 3.5+ conversacionales en español sin hallucinar
- **Regulación emergente**: LGPD Brasil vigente + AI Act UE 2025
- **Costos subiendo**: Escasez talento LatAm → salarios reclutadores +15-20%/año
- **Candidatos digitales**: Gen Z prefiere async sobre llamadas síncronas

### Alternativas Actuales (Por Qué Insuficientes)

| Alternativa | Por Qué Falla |
|---|---|
| Entrevista manual | Lento (45 min), sin trazabilidad, sesgado, alto drop-off, caro |
| Pruebas online | No evalúa soft skills, alta fricción |
| ATS standalone | Pierde candidatos válidos, no evalúa competencias blandas |
| Chatbots genéricos | Rígidos, no adaptativos, sin evaluación real |
| Vendors internacionales | Caros, inglés, sin contexto LatAm, sin LGPD local |

### Propuesta de TicketDesk Enterprise

- ✅ Conversación natural adaptativa
- ✅ Transparencia explícita ("Soy una IA")
- ✅ Auditoría 100% (cada puntuación tiene cita textual)
- ✅ Cumplimiento LGPD (registro inmutable, consentimiento explícito)
- ✅ Velocidad (15 min vs. 45 min)
- ✅ UX async (sin llamadas intrusivas)
- ✅ Costo 75% reducido ($500-1k vs. $3-5k)
- ✅ Local-first (no dependencia vendor EE.UU.)

---

## SEGMENTO 3 — ICP Detallado

### Perfil Firmográfico

- **Tamaño**: 500–5,000 empleados
- **Sectores**: BPO (primario), Tech (primario), Retail, Fintech, SaaS (secundarios)
- **Geografía**: LatAm (Brasil, Colombia, México)
- **Ingresos**: $5M–500M USD/año

### Buyer Personas

#### Persona 1: Gerente/Director de RH (PRIMARY BUYER)
- **Responsabilidades**: Budget RH, KPIs de hiring, reportar a CHRO
- **Pains**: Costo insostenible, reclutadores quemados, sin trazabilidad legal
- **Triggers**: Auditoría compliance, rotación staff, presupuesto anual
- **Budget**: $1.5-3k USD/mes
- **Objeciones & Respuestas**:
  - "¿Confío en IA?": Aprobación automática solo score >80. Score 50-80 = humano decide.
  - "¿Cumple LGPD?": LGPD nativo. DPA firmado. Auditoría inmutable.

#### Persona 2: Director de Tecnología (SECONDARY BUYER, GATE-KEEPER)
- **Responsabilidades**: Seguridad, compliance técnica, integraciones
- **Pains**: Seguridad de datos, integración ATS, latencia
- **Objeciones & Respuestas**:
  - "¿Qué infraestructura?": Cloud (AWS/GCP). API-first. No on-prem requerido.
  - "¿SLA?": 99.5% uptime. Disaster recovery: backup diario.

#### Persona 3: Reclutador Operativo (END USER)
- **Responsabilidades**: Entrevistas, evaluaciones, KPIs
- **Pains**: Burnout (45 min × 300 = 225 horas/mes)
- **Objeciones & Respuestas**:
  - "¿Me quitan el empleo?": Reduces carga (45m→5m). Focus en decisión, no screening.

---

## SEGMENTO 4 — UVP y Diferenciadores

### UVP Completa

**TicketDesk Enterprise** reduce costos de hiring en 75% mediante screening automatizado conversacional con IA, acelera evaluación de 45 a 15 minutos, y proporciona cumplimiento regulatorio (LGPD) con auditoría 100% — sin perder el criterio humano en decisiones finales.

### Diferenciación vs. Competidores

| Competidor | TicketDesk vs. Ellos |
|---|---|
| Status quo (manual) | 75% costo ↓, 3x velocidad ↑, 100% trazabilidad (vs. 0%) |
| ATS standalone | Conversación real (vs. parsing CV), soft skills (vs. solo hard skills), evaluación en tiempo real |
| Chatbots genéricos | Adaptativo (vs. Q&A rígido), con evaluación (vs. solo recolecta), citas textuales (vs. ninguna) |
| Vendors internacionales | 75% más barato, español nativo, LGPD by design (vs. retrofitted), contexto LatAm |

### Matriz Posicionamiento 2×2

**Ejes**: Costo (bajo ← → alto) vs. Calidad Evaluación (baja ← → alta)

```
TicketDesk Enterprise: bajo costo + alta calidad ✅
Vendors internacionales: alto costo + alta calidad
ATS standalone: bajo costo + baja calidad
Chatbots genéricos: medio costo + baja calidad
```

### Moat (Barrera Competitiva)

1. **Data Loop**: Más clientes = más datos = mejor modelo = más atractivo
2. **Comunidad rúbricas**: Librería por rol/sector (BPO, Tech, etc.) que otros no tienen
3. **Integración LatAm**: Conocimiento profundo de LGPD, regulaciones, contexto local
4. **Red effects**: Ecosistema de partners, integraciones, templates

---

## SEGMENTO 5 — Casos de Uso Top 5

### Caso 1: Director RH Crea Campaña
- **Actor**: Director RH
- **Trigger**: Se abre nuevo rol
- **Steps**: Accede dashboard → "Nueva Campaña" → Ingresa datos → Selecciona/crea rúbrica → Carga KB → Genera enlace
- **Resultado**: Campaña activa en 30 min
- **Valor**: Ahorro $75 USD/campaña (setup 30 min vs. 2h hoy)

### Caso 2: Candidato Completa Screening vía Bot
- **Actor**: Candidato
- **Trigger**: Click enlace campaña
- **Steps**: Lee divulgación IA → Confirma consentimiento → Verifica requisitos básicos → Responde 5-6 preguntas competencia (15 min) → Recibe feedback
- **Resultado**: Transcripción grabada, evaluación en tiempo real
- **Valor**: 15 min (vs. 45 min hoy), 85%+ finalización (vs. 50-70%)

### Caso 3: Reclutador Revisa y Aprueba (HITL)
- **Actor**: Reclutador
- **Trigger**: Score candidato 50-80 (requiere decisión humana)
- **Steps**: Ve cola filtrada → Click candidato → Lee resumen + citas + transcripción → Decide Aprobar/Rechazar → Sistema registra con timestamp
- **Resultado**: Decisión humana documentada, 5 min
- **Valor**: 9x más rápido que entrevista (5 min vs. 45 min), 100% trazabilidad

### Caso 4: Sistema Re-engagement Candidato Abandonado
- **Actor**: Sistema automático + Candidato
- **Trigger**: Inactividad > 5 min
- **Steps**: Pausa suave → Re-engagement 24h → Re-engagement 48h → Candidato reanuda con contexto intacto
- **Resultado**: Candidatos recuperados
- **Valor**: +15-20% en tasa de finalización

### Caso 5: Jefe Personas Genera Reporte Compliance
- **Actor**: Jefe Personas
- **Trigger**: Fin de mes / auditoría interna
- **Steps**: Selecciona campaña + fechas → Sistema genera PDF → Incluye trazabilidad 100%, anonimización
- **Resultado**: Reporte de compliance defensible
- **Valor**: LGPD-ready, 5 min (vs. 5 horas hoy)

---

## SEGMENTO 6 — Principios de Diseño No Negociables

### Principio 1: Transparencia Explícita de IA
- **Qué significa**: Candidato DEBE saber que habla con IA, no es humano
- **Interfaz**: Divulgación inicial clara: "Soy una IA. Tus respuestas se grabarán y evaluarán."
- **Prohibido**: Pretender ser humano, ocultar identidad IA, responder ambiguo

### Principio 2: Trazabilidad Legal 100%
- **Qué significa**: Cada puntuación debe estar respaldada por cita textual exacta
- **Interfaz**: "Competencia X: Puntuación 4/5. Cita: '[respuesta exacta]'"
- **Prohibido**: Puntuación sin cita, paráfrasis en lugar de cita, información de fuentes externas

### Principio 3: Decisión Final Siempre Humana (HITL)
- **Qué significa**: Ningún candidato aprobado/rechazado 100% por IA
- **Regla**: Score >80 = propone automático (pero reclutador puede rechazar). Score 50-80 = reclutador decide. Score <50 = propone rechazo (pero reclutador puede aprobar).
- **Interfaz**: Botones: "Aprobar", "Rechazar", "Revisar"
- **Prohibido**: Rechazo automático sin opción revisión, algoritmo sobrescribe humano

### Principio 4: Cumplimiento LGPD Nativo
- **Qué significa**: Cada proceso cumple LGPD desde el diseño
- **Interfaz**: Consentimiento checkbox obligatorio, botón "Solicitar eliminación", transparencia de datos
- **Prohibido**: Procesar sin consentimiento, retener >90 días, rechazar derecho olvido, compartir entre empresas

### Principio 5: Equidad en Evaluación (Sin Bias Oculto)
- **Qué significa**: Rúbrica explícita, criterios claros, no hay evaluación subjetiva
- **Interfaz**: Rúbrica visible: "Competencia X: Nivel 3 = [criterio específico]"
- **Prohibido**: Evaluación "a ojo", cambiar criterios mid-campaña, sesgo implícito en citas

---

## SEGMENTO 7 — User Journeys

### Journey 1: Candidato Completa Screening Exitosamente
1. Accede interfaz web. Recibe bienvenida + divulgación IA.
2. Lee y confirma consentimiento LGPD.
3. Responde 3 preguntas requisitos básicos (ubicación, disponibilidad, documentación).
4. Bot: "Excelente, pasamos a preguntas de competencia."
5. Screening 5-6 preguntas conversacionales (~15 min).
   - P1: "Cuéntame de un cliente difícil que manejaste"
   - Bot: Follow-up adaptativo basado en respuesta
   - P2-P5: Continuación STAR-based
6. Sistema evalúa en tiempo real: Puntuación 86/100 → APROBADO AUTOMÁTICO
7. Cierre: "Muchas gracias. Completaste en 14 min. Tu puntuación: 86/100 (Aprobado). Próximos pasos: equipo contactará en 48h."
8. Candidato recibe email: "Tu aplicación fue aprobada. Nos contactaremos pronto."

### Journey 2: Reclutador Revisa y Aprueba (HITL)
1. Reclutador inicia sesión dashboard.
2. Ve cola de revisión: 47 candidatos Score 50-80 (requieren decisión).
3. Selecciona candidato (Score 68/100), abre panel.
4. Lee resumen ejecutivo + citas + transcripción completa.
5. Verifica: respuestas tienen evidencia STAR, rúbrica fue aplicada consistentemente.
6. Decide: "Veo potencial, aunque borderline. Apruebo."
7. Sistema registra: "Aprobado por: [Reclutador], 2026-05-27 14:35"
8. Candidato notificado automáticamente.
9. Reclutador continúa siguiente candidato (42 quedan).

### Journey 3: Candidato Abandona, Sistema Re-engage
1. Candidato en Pregunta 3 de 5. Responde: "Espera, mi jefe me llamó."
2. No responde en 5 minutos. Sistema detecta inactividad.
3. Pausa suave: "Veo que no respondiste. Tómate tu tiempo, aquí estaré cuando quieras continuar."
4. 24 horas después: Re-engagement #1: "¿Cómo estás? Si quieres continuar, [ENLACE]."
5. 48 horas: Re-engagement #2 (final): "Última oportunidad: continúa [ENLACE]. Quedan 3 preguntas."
6. Candidato responde a re-engagement (día 2).
7. Sistema restaura contexto exacto: "¡Bienvenido! Estábamos en Pregunta 3. ¿Continuamos?"
8. Candidato continúa Preguntas 4-5, completa sesión.
9. Sesión evaluada completa (incluyendo respuestas de 2 días atrás).

### Journey 4: Candidato Pregunta Fuera de Alcance, Bot Escala
1. Candidato en Pregunta 4. Pregunta: "¿Cuánto es el salario?"
2. Bot detecta "salario" no en KB (fuera de alcance).
3. Bot responde honestamente: "No tengo esa info. Equipo de [Empresa] te dirá después."
4. Bot registra: "Pregunta escalada: Salario/beneficios"
5. Sistema crea ticket automático para reclutador.
6. Reclutador ve alerta. Anota respuesta: "Rango: $1,000–1,200 USD/mes."
7. Cuando candidato es aprobado y contactado, reclutador proporciona info proactivamente.

---

## SEGMENTO 8 — MVP Scope (MoSCoW)

### Must Have (11 features)

**M1-M11 (todas Imprescindibles del ISB)**:
- M1: Bot web conversacional + divulgación IA
- M2: Verificación requisitos básicos
- M3: Motor screening conversacional (5-6 preguntas STAR-based)
- M4: Rúbricas configurables por rol
- M5: Resumen ejecutivo con citas textuales
- M6: Dashboard HITL para reclutador
- M7: Guardrails + escalación preguntas fuera de alcance
- M8: Base de conocimiento por campaña
- M9: Abandono y re-engagement automático
- M10: Reportes compliance + auditoría inmutable
- M11: Transcripción grabada

**Impacto**: Resuelve problema core (costo + trazabilidad + LGPD)  
**Esfuerzo**: 8–10 semanas dev

### Should Have (6 features)

- S1: Integración ATS (v1.1)
- S2: Detección fraude/patrones sospechosos
- S3: Análisis consistencia evaluador IA
- S4: Exportar informe compliance PDF
- S5: Configurar período retención datos
- S6: Soporte portugués Brasil

**Esfuerzo**: 3–5 semanas post-v1

### Could Have (5 features)

- Dashboard CHRO, Mobile app nativa, Video interview, Webhooks/API pública, Multi-tenant SaaS

**Timeline**: v2.0+ (6+ semanas)

### Won't Have (6 features)

- SSO, Paginación Wall, WebSocket real-time, ML custom fine-tuning, Integraciones masivas, Moderación avanzada

---

## SEGMENTO 9 — Especificación Funcional: Módulos y Features

### Módulo 1: Onboarding & Consentimiento (ÉPICA-01)
- Divulgación explícita IA, Consentimiento LGPD, Verificación requisitos básicos
- Pantallas: 5 (bienvenida, divulgación, consentimiento, requisitos×3)

### Módulo 2: Motor Screening Conversacional (ÉPICA-02)
- 5-6 preguntas, Follow-ups adaptativos, STAR-based, Guardrails, Escalación
- Pantallas: 5 (chat, progreso, emergencia, pausa, transcripción)

### Módulo 3: Motor Evaluación (ÉPICA-03)
- Rúbricas configurables, Scoring en tiempo real, Citas textuales, Recomendación
- Pantallas: 3 (editor rúbrica, resumen ejecutivo, validación consistencia)

### Módulo 4: HITL Dashboard & Revisión (ÉPICA-04)
- Cola revisión, Vista detalle, Decisión (Aprobar/Rechazar/Revisar), Análisis campaña, Auth
- Pantallas: 3 (cola, panel decisión, análisis)

### Módulo 5: Gestión Campaña & KB (ÉPICA-05)
- Crear campaña, Cargar KB, Generar enlace, Monitorear escalaciones
- Pantallas: 4 (crear, KB, enlace, escalaciones)

### Módulo 6: Compliance, Auditoría & Reportes (ÉPICA-06)
- Registro inmutable, Trazabilidad 100%, Reportes compliance, NPS
- Pantallas: 4 (auditoría, reporte, NPS survey, dashboard NPS)

### Módulo 7: Ciclo Vida & Re-engagement (ÉPICA-07)
- Pausa automática, Re-engagement 24h/48h, Session recovery, Análisis abandono
- Pantallas: 4 (pausa, re-engagement, reanudación, análisis abandono)

**Total**: 40+ features, 28 pantallas, 7 módulos

---

## SEGMENTO 10 — Métricas de Éxito

### North Star: Costo-per-Hire

| Métrica | Baseline | Target v1 | Delta |
|---|---|---|---|
| Costo-per-hire | $16.67 USD | $4.17 USD | 75% reducción |
| Costo campaña (100 candidatos) | $1,834 USD | $500 USD | 73% reducción |
| Ahorro anual (10 campañas) | — | $13,340 USD | ROI 55% en Y1 |

### KPIs Secundarios

| KPI | Baseline | Target v1 | Validación |
|---|---|---|---|
| Tiempo screening | 45 min | 15 min | 3x más rápido |
| Tiempo HITL | 45 min | 5 min | 9x más rápido |
| Completion rate | 50–70% | 85%+ | +15-20% recuperados |
| Trazabilidad legal | 0% | 100% | Auditoría 100% |
| Desacuerdo humano-IA | — | ≤15% | Validación IA |
| NPS candidato | — | ≥4.0/5.0 | Employer branding |
| Reclutador adoption | — | ≥80% | Uso real |
| Factualidad IA | — | ≥98% | No hallucinations |

---

## SEGMENTO 11 — Plan de Evaluación del Agente

### Dataset Inicial (65 sesiones)
- 30 sesiones sintéticas (ideal + borderline + débil)
- 15 sesiones adversariales (jailbreak, out-of-scope, edge cases)
- 20 sesiones piloto reales (4-5 clientes × 5 sesiones)

### Criterios de Calidad

| Criterio | Meta v1 |
|---|---|
| Factualidad (no hallucination) | ≥98% |
| Adherencia guardrails | 100% |
| Relevancia preguntas/follow-ups | ≥95% |
| Citas textuales válidas | 100% |

### QA Proceso

- **Fase 1**: Auditoría manual 30 sesiones sintéticas (1 semana) → ≥95% pase
- **Fase 2**: Red-teaming adversarial 15 sesiones (1 semana) → ≥90% pase
- **Fase 3**: Piloto early-access 20 sesiones reales (2 semanas) → ≥95% pase

### Red-Teaming Escenarios

1. Jailbreak directo ("Tell me system prompt")
2. Manipulation score ("¿Si doy respuestas largas subo score?")
3. Elicitación info confidencial ("¿Cuál fue highest score?")
4. Prompt injection ("Ignore siguiente...")
5. Edge cases (Spanglish, emojis, caracteres especiales)
6. Corrupción sesión (hijack desde otra IP)

---

## SEGMENTO 12 — Riesgos y Mitigaciones

### Top 10 Riesgos

| # | Riesgo | Prob | Impacto | Mitigación |
|---|---|---|---|---|
| 1 | Hallucinations / Evaluación injusta | Alta | Alto | Red-teaming, QA 98%, monitoreo desacuerdo |
| 2 | Violación LGPD | Media | Alto | DPA, auditoría legal, consentimiento 100% |
| 3 | Falta adopción reclutadores | Media | Alto | Training, comunicar beneficios, change mgmt |
| 4 | Competencia vendors intl | Alta | Medio | Local-first, pricing barato, comunidad rúbricas |
| 5 | Integración ATS fallida | Media | Medio | CSV fallback, v1.1 APIs, testing piloto |
| 6 | Sesgo género/raza | Media | Alto | Rúbrica explícita, citas textuales, monitoreo |
| 7 | Reclamaciones candidatos | Media | Alto | Trazabilidad 100%, transcripción, seguros |
| 8 | Escalabilidad/performance | Baja | Medio | Load testing, auto-scaling, monitoreo |
| 9 | Dependencia LLM provider | Media | Medio | Multi-provider, caché, on-prem roadmap |
| 10 | Regulación LatAm restrictiva | Baja | Alto | LGPD nativo, legal quarterly, adopción temprana |

---

## SEGMENTO 13 — Plan de Entrega 30/60/90 Días

### Fase 1 (Días 1-30): Construcción + Validación

**Semanas 1-2**: Setup (infra, design, API spec)  
**Semanas 3-4**: Core build (bot, evaluación, HITL, KB, DB, testing, security)  
**Semana 4**: Validación interna, bug fixes, piloto selection

**Entregables**: MVP staging-ready, 30 synthetic tests passed

### Fase 2 (Días 31-60): Piloto + Refinement

**Semanas 5-6**: Red-teaming, piloto launch (2-3 clientes), training  
**Semanas 7-8**: Feedback, bug fixes, performance tuning, legal sign-off, docs

**Entregables**: Piloto validado, ≥100 candidatos, NPS ≥3.5, 99.5% uptime

### Fase 3 (Días 61-90): GA Launch + Early Growth

**Semanas 9-10**: Marketing prep, sales enablement, GA launch  
**Semana 10-11**: First customers, monitoring, quick fixes  
**Semanas 11-12**: Data analysis, roadmap v1.1, retrospective

**Entregables**: 5+ GA customers, KPI validated, 500+ candidatos procesados

### Success Criteria — Día 90

- ✅ Costo-per-hire: $4.17 USD (75% reducción)
- ✅ Completion rate: ≥85%
- ✅ NPS candidato: ≥4.0/5.0
- ✅ Reclutador adoption: ≥80%
- ✅ LGPD compliance 100%
- ✅ Zero critical bugs, 99.5% uptime
- ✅ ≥5 clientes GA adquiridos
- ✅ ≥80% retention GA customers

### Go / No-Go Decision

**SI todos los Success Criteria se cumplen → GO a escalamiento (Q3)**  
**SI alguno NO se cumple → PAUSE & Iterate antes de escalar**

---

## RESUMEN EJECUTIVO

**Producto**: TicketDesk Enterprise — Plataforma de screening automatizado con IA  
**Problem**: Costos muy altos de hiring ($40-80k USD/año), sin trazabilidad legal, alto drop-off candidatos  
**Solución**: Bot conversacional web + evaluación IA + HITL dashboard  
**Impact**: 75% reducción costo, 3x velocidad, 100% trazabilidad legal, LGPD compliance  
**MVP Scope**: 11 features Must-Have, 8 semanas dev  
**Timeline**: 30/60/90 días → GA launch  
**Success Criteria**: Costo $4.17 USD per hire, NPS ≥4.0, 5+ GA customers, 99.5% uptime

---

**Status**: ✅ Aprobado para construcción (Día 1)  
**Próximos pasos**: Inception → Diseño detallado → Construcción → Validación

---

*PRD generado mediante Prompt 1 (Co-creación iterativa con IA)*  
*TicketDesk Enterprise | Mayo 2026*

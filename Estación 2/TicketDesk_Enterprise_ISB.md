# Internal Solution Brief — TicketDesk Enterprise

## SOLUCIÓN

**Nombre de la solución:** TicketDesk Enterprise

**Descripción en una línea:**
Plataforma web + bot de screening automatizado con IA que reduce costos de hiring mediante evaluación conversacional justa y auditable.

**Empresa / Organización:** [Tu Empresa Actual]

---

## 1. PROBLEMA DE NEGOCIO

**¿Cuál es el problema?**

El proceso actual de screening de candidatos consume recursos excesivos de personal y tecnología:
- Reclutadores dedican 45 minutos por candidato en llamadas/entrevistas
- Se procesan 200–500 candidatos por rol abierto
- Herramientas actuales (ATS, evaluación manual) generan overhead administrativo
- Sin trazabilidad legal clara → riesgo de litigios por discriminación

**¿Cuánto cuesta este problema?**

- **Costo de RH actual**: ~$3,000–5,000 USD por campaña de 100 candidatos (2 reclutadores × 1 mes)
- **Costo tecnológico**: Suscripciones a ATS + herramientas de evaluación + integraciones = ~$500–1,000 USD/mes
- **Riesgos legales**: Reclamaciones por falta de documentación = $10,000–50,000 USD por caso
- **Costo de oportunidad**: Procesos lentos retrasan contrataciones, pérdida de candidatos top

**Total anual estimado**: $40,000–80,000 USD + riesgos legales

**¿Hace cuánto existe este problema?**

Desde hace 2–3 años (conforme crecieron volúmenes de aplicantes y se endurecieron regulaciones LatAm).

---

## 2. STAKEHOLDERS Y SPONSOR

**¿Quién es el sponsor?**
- Gerente/Director de Recursos Humanos (presupuesto y decisión final)
- Director de Tecnología (aprobación técnica e integración con sistemas)

**¿Quiénes son los usuarios finales?**
- Reclutadores operativos (usan plataforma de revisión HITL)
- Directores/VP de Talento (configuran campañas, analizan resultados)
- Jefe de Personas/Compliance (auditoría y reportes legales)
- Candidatos (interactúan con bot de screening vía web)

**¿Quién puede bloquear la adopción?**
- **IT/Seguridad**: Requiere validación de seguridad, integración con sistemas existentes
- **Legal/Compliance**: Validación de cumplimiento LGPD, regulaciones LatAm
- **Sindicato** (si aplica): Riesgo de que automatización sustituya empleo de reclutadores
- **Directores de área**: Si no ven ROI claro en costos/calidad

---

## 3. ESTADO ACTUAL

**¿Cómo se resuelve hoy?**

1. **Publicación**: Se abre rol en portales (LinkedIn, bolsas locales)
2. **Recopilación**: Reclutador recopila CVs manualmente, filtro básico
3. **Screening**: Llamada/videollamada de 45 min por candidato (entrevista de preguntas predefinidas)
4. **Evaluación**: Reclutador toma notas manuales, califica subjetivamente
5. **Decisión**: Reunión con stakeholders, decisión manual
6. **Documentación**: Notas dispersas, sin trazabilidad clara

**¿Qué herramientas se usan actualmente?**
- ATS (ej: Workday, BambooHR, LinkedIn Recruiter)
- Google Meet / Zoom (para entrevistas)
- Google Sheets / Excel (tracking de candidatos)
- Email (comunicación con candidatos)
- No hay herramienta centralizada de evaluación

**¿Qué funciona bien del proceso actual? (no tocar)**
- Conexión personal reclutador-candidato (genera confianza)
- Flexibility en preguntas (adaptarse a respuestas)
- Decisión final por humanos (no automatizada)

**¿Qué no funciona? (oportunidad de mejora)**
- **Lento**: 45 min/candidato × 300 candidatos = 225 horas de reclutador
- **Caro**: Salarios de reclutadores + overhead
- **Sin trazabilidad**: Notas dispersas, sin citas textuales → riesgo legal
- **Sesgado**: Evaluación subjetiva, sin rúbrica clara
- **Alto drop-off**: Candidatos abandonan por fricción (llamadas intrusivas)
- **Sin análisis**: Imposible identificar dónde se pierden candidatos

---

## 4. ESTADO FUTURO DESEADO

**¿Cómo se vería el proceso si la solución funciona perfectamente?**

1. **Publicación**: Se abre rol en portales + se genera enlace único para campaña
2. **Screening automatizado**: Candidato inicia screening vía bot web (async, sin llamadas)
   - Bot: divulgación explícita de IA
   - Candidato: responde preguntas conversacionales con seguimientos adaptativos
   - Duración: 15 min (vs. 45 min hoy)
3. **Evaluación en tiempo real**: Sistema evalúa respuestas contra rúbrica configurada
4. **Decisión automática o HITL**:
   - Score > 80: aprobado automático (reduce revisión humana)
   - Score 50-80: cola de revisión humana (reclutador revisa + aprueba/rechaza)
   - Score < 50: rechazado automático (con opción de revisión si aplica)
5. **Documentación inmutable**: Cada puntuación tiene cita textual de transcripción
6. **Re-engagement automático**: Si candidato abandona, bot envía recordatorio a 24h y 48h
7. **Reportes legales**: Compliance obtiene reportes auditables con trazabilidad 100%

**¿Qué cambia para el usuario final en su día a día?**

- **Reclutador**: De 45 min por candidato → 5 min de revisión (solo Score 50-80). Reduce burnout, mejor quality of life.
- **Director/VP Talento**: Dashboard con métricas (tasa de finalización, distribución de puntuación, análisis de abandono). Mejor visibilidad.
- **Jefe de Personas**: Reportes de compliance automáticos. Menos riesgo legal.
- **Candidato**: Experiencia async, sin llamadas incómodas. Feedback claro sobre por qué fue aprobado/rechazado.

---

## 5. CRITERIOS DE ÉXITO

Define 2-3 métricas medibles que demuestren que la solución funciona.

| Métrica | Valor actual | Target | Impacto |
|---------|-------------|--------|---------|
| **Costo por campaña (100 candidatos)** | $3,000–5,000 USD | $500–1,000 USD | 75% reducción de costos RH |
| **Tiempo de screening por candidato** | 45 minutos | 15 minutos | 3x más rápido |
| **Tasa de finalización de screening** | 50–70% (muchos abandonos) | 85%+ | Menos candidatos perdidos |
| **Trazabilidad legal (% con citas)** | 0% (notas manuales sin citas) | 100% (cada puntuación tiene cita textual) | Riesgo legal eliminado |

**KPI Primario: Reducción de Costos**  
- Ahorro anual esperado: $40,000–80,000 USD (RH + herramientas + riesgos legales)
- ROI esperado: 300%+ en año 1

---

## 6. RESTRICCIONES

**Restricciones técnicas:**
- Integración con ATS existente (ej: Workday, BambooHR) — requiere APIs
- Stack actual de tecnología: [completar según tu infraestructura: cloud, on-prem, vendors específicos]
- Evaluación en tiempo real requiere inferencia rápida de IA (latencia < 5s)
- Compatibilidad con navegadores web modernos (Chrome, Safari, Firefox)

**Restricciones de datos:**
- Acceso a datos de candidatos (CVs, evaluaciones históricas) para entrenar y validar rúbricas
- Cumplimiento LGPD (Brasil) y normativas LatAm en privacidad
- Retención de datos: máximo 90 días post-evaluación (política interna o regulatoria)
- No se pueden usar datos de candidatos para otros propósitos sin consentimiento

**Restricciones organizacionales:**
- **Presupuesto**: Debe alinearse con presupuesto de IT/RH actual
- **Timeline**: MVP en 4 semanas (Estación 2–3)
- **Aprobaciones**: Requiere firma del Director de Tecnología + Gerencia de RH
- **Change management**: Reclutadores deben entrenarse en nuevo flujo (2–3 días)

**Restricciones de compliance/seguridad:**
- Cumplimiento LGPD Brasil (si aplica)
- Auditoría de decisiones de IA (regulación LatAm emergente)
- Encriptación de datos en tránsito y en reposo
- No exposición de rúbricas/prompts de sistema a candidatos (jailbreak risk)

---

## 7. ENFOQUE TÉCNICO PROPUESTO

**¿Qué capacidad de AI aplica a este problema?**

- **Orquestación de agentes**: Bot conversa con candidato, adapta preguntas basadas en respuestas (generación)
- **Clasificación/Evaluación**: Modelo de IA evalúa respuestas contra rúbrica, asigna puntuación por competencia
- **Extracción**: Extrae citas textuales de transcripción para justificar puntuaciones
- **RAG (Retrieval Augmented Generation)**: Bot accede a base de conocimiento de la campaña (documentos sobre rol, beneficios, políticas) para responder preguntas de candidatos

**¿Por qué AI es la solución correcta y no una automatización tradicional?**

- **Flexibilidad**: Preguntas conversacionales adaptativas (vs. Q&A rígido de bots tradicionales)
- **Contexto**: IA entiende matices de respuestas humanas, detecta evasiones, solicita seguimiento relevante
- **Escala**: Evalúa 100+ candidatos en paralelo sin límite de reclutadores
- **Justificabilidad**: Genera citas textuales que justifican puntuaciones (vs. scoring black-box)
- **Cumplimiento**: Registra todo (consentimiento, conversación, evaluación) para auditoría

Automatización tradicional (e.g., reglas IF-THEN) no soporta conversación natural ni adaptación de preguntas.

**Arquitectura de alto nivel:**

```
┌─────────────────────────────────────────────┐
│         Candidato                           │
│   (HTML Web + Bot via chat)                 │
└──────────────┬──────────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────────────┐
│     Backend API (Node.js / Python)          │
│  ├─ Auth (JWT)                              │
│  ├─ Session management                      │
│  ├─ Screening orchestration                 │
│  └─ Evaluation engine                       │
└──────────────┬──────────────────────────────┘
               │
   ┌───────────┼───────────┬────────────┐
   │           │           │            │
┌──▼─┐    ┌──▼──┐    ┌───▼───┐    ┌──▼───┐
│ AI │    │ DB  │    │Pinecone│    │ S3  │
│LLM │    │(SQL)│    │ (KB)   │    │Logs │
└────┘    └─────┘    └────────┘    └─────┘
```

---

## 8. RIESGOS Y DEPENDENCIAS

**Riesgo 1: Rechazo de candidatos por decisión automática**
**Mitigación:** Threshold de aprobación automática es alto (score > 80). Scoring 50-80 siempre va a HITL humano. Comunicar claramente a candidatos que decisiones finales son humanas.

**Riesgo 2: Hallucinations o evaluación injusta de IA**
**Mitigación:** Rúbricas configuradas + validación humana de primeros 20 candidatos. Monitoreo de tasa de desacuerdo humano-IA. Reentrenamiento de modelo si drift detectado.

**Riesgo 3: Falta de adopción por reclutadores (miedo a reemplazo de empleo)**
**Mitigación:** Comunicar que herramienta **reduce carga de trabajo** (de 45 min a 5 min por candidato), no elimina empleo. Reclutadores enfoque en candidates Score 50-80 (requiere criterio humano). Training obligatorio.

**Riesgo 4: Compliance/regulatorio (LGPD, regulaciones LatAm)**
**Mitigación:** Asesoría legal antes de lanzamiento. Cumplimiento explícito de LGPD en consentimiento de candidato. Auditoría de trazabilidad 100%.

**Riesgo 5: Integración con ATS existente (datos, APIs)**
**Mitigación:** Validar APIs disponibles con Director de Tecnología antes de dev. Si no hay APIs, plan B es manual CSV export/import.

**Dependencias externas:**
- Acceso a **APIs de ATS actual** (para candidatos, decisiones, feedback)
- Aprobación de **Legal/Compliance** en LGPD y regulaciones
- **Presupuesto** aprobado por Gerencia RH + Director de Tecnología
- Datos de evaluación histórica (si existen) para validar rúbricas

---

## 9. LÍMITES DE ALCANCE

**En alcance (lo que SÍ construyo en 4 semanas):**

- Screening conversacional vía bot web (Telegram/web UI)
- Divulgación explícita de identidad IA + consentimiento
- Evaluación en tiempo real contra rúbrica configurable
- Aprobación automática (score > 80)
- HITL dashboard para Score 50-80
- Transcripción + citas textuales de respuestas
- Re-engagement automático (24h, 48h)
- Reportes de campaña (tasa finalización, puntuaciones, análisis abandono)
- Registro de auditoría inmutable

**Fuera de alcance (roadmap post-MVP):**

- Integración con ATS (v1.1)
- Soporte multi-idioma (portugués, etc.) (v1.2)
- Análisis de consistencia humano-IA (v1.3)
- Detección de fraude / jailbreak avanzada (v1.3)
- Dashboard de RH para reportes ejecutivos (v2.0)
- Mobile app nativa (web-only en v1)

---

## Checklist de entrega

- [x] Problema identificado y cuantificado con datos reales ($40-80k USD/año)
- [x] Sponsor y stakeholders identificados (Gerencia RH + Director Tech)
- [x] Estado actual documentado (45 min/candidato, costos altos, sin trazabilidad)
- [x] Estado futuro deseado definido (15 min/candidato, 75% reducción costo, 100% trazabilidad)
- [x] Deep research de contexto completado (regulaciones LatAm, costos de hiring)
- [x] Deep research de riesgos completado (hallucinations, adopción, compliance)
- [x] Internal Solution Brief completado (este documento)
- [x] Listo para Estación 2: Prompt 1 (co-crear PRD)

---

*TicketDesk Enterprise — Internal Solution Brief*  
*Proyecto actual | Mayo 2026*

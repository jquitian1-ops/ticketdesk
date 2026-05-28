# Unit 4: Evaluación (Scoring Engine) — Actividad 1: Entidades del Dominio

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 1 - Diseño Funcional: Entidades del Dominio  
**Fecha**: 2026-05-27  

---

## 📋 Contexto Acotado: Motor de Evaluación Automática

**Alcance**: Cálculo puntuaciones automáticas basado rúbrica, extracción citas relevantes, validación respuestas contra criterios, generación reportes evaluación.

**Patrón**: Domain-Driven Design con Agregados, Objetos de Valor e Invariantes

---

## 🎯 4 Agregados del Dominio

### 1. AgregadoRúbrica

**Entidad Raíz**: `Rúbrica`

```
Rúbrica (Raíz)
├── id: UUID
├── id_campaña: UUID (foreign key a Campaña Unit 2)
├── nombre: String (e.g., "Junior Python Developer")
├── descripción: String
├── versión: Int (versionado, audit trail)
├── estado: EstadoRúbrica (ACTIVA, ARCHIVADA, SUSPENDIDA)
├── creada_en: DateTime
├── actualizada_en: DateTime
├── criterios: Lista[Criterio] (1-10 campos evaluación)
├── pesos_criterios: JSON (weighting, sum=100%)
├── escala_puntuación: EscalaPuntuación (1-5, 0-10, cualitativa)
├── umbrales_aprobación: UmbralAprobación
│   ├── score_mínimo: Float (e.g., 7.0 / 10.0)
│   ├── criterios_obligatorios: Lista[String] (must >= 6.0)
│   └── flag_revisión: Boolean (true si <7.0)
├── metadata: JSON
│   ├── autor_id: UUID
│   ├── skills_requeridas: Lista[String]
│   └── experiencia_años: Int
└── auditoría: AuditoríaEntry

Invariantes:
- Rúbrica.versión ≥ 1 (inmutable, nueva versión != UPDATE)
- sum(pesos_criterios) == 100.0 (distribución válida)
- criterios.length >= 3 (mínimo 3 campos)
- estado: ACTIVA → ARCHIVADA (una dirección)
- Una rúbrica activa por campaña en cualquier momento
```

**Objetos de Valor**:
- `EstadoRúbrica` enum
- `Criterio` (nombre, descripción, tipo: texto|numérico|escala)
- `EscalaPuntuación` (min, max, step)
- `UmbralAprobación` (score_mínimo, criterios_obligatorios)
- `PesosCriterios` (suma 100%)

**Reglas Aplicadas**: REGLA-EVAL-01 a REGLA-EVAL-05

---

### 2. AgregadoEvaluación

**Entidad Raíz**: `Evaluación`

```
Evaluación (Raíz)
├── id: UUID
├── id_screening: UUID (foreign key a Screening Unit 2)
├── id_rúbrica: UUID (versión específica)
├── id_evaluador: UUID (reclutador Unit 2)
├── evaluada_en: DateTime
├── estado: EstadoEvaluación (BORRADOR, COMPLETADA, RECHAZADA)
├── score_total: Float (0.0-10.0, calculado)
├── decision: Decisión (HIRE, REJECT, PENDING, ON_HOLD)
├── feedback: String (notas evaluador, max 2000 chars)
├── tiempo_evaluación: Int (segundos, para analytics)
├── scores_criterio: Lista[ScoreCriterio]
│   ├── id_criterio: UUID
│   ├── score: Float (0.0-10.0)
│   ├── feedback: String
│   ├── confianza: Float (0.0-1.0, para IA scoring)
│   └── justificación: String (cita o resumen)
├── citas_relevantes: Lista[Cita] (trozos chat usados para scoring)
├── banderas: Lista[Bandera] (RED_FLAG, GREEN_FLAG, REVIEW_NEEDED)
├── validación_manual: Boolean (true si evaluador override automático)
├── auditoría: AuditoríaEntry
└── metadatos: JSON

Invariantes:
- score_total = sum(score_criterio[i] * peso[i]) / 100 (fórmula)
- score_total ∈ [0.0, 10.0]
- decision ∈ {HIRE, REJECT, PENDING, ON_HOLD}
- Si decision == HIRE: score_total >= 7.0 (REGLA-EVAL-06)
- Si decision == REJECT: score_total < 6.0 O criterio_obligatorio < 5.0
- Evaluación inmutable después COMPLETADA
- validación_manual=true si score_total != score_automático
```

**Objetos de Valor**:
- `EstadoEvaluación` enum
- `Decisión` enum
- `ScoreCriterio` (criterio_id, score, feedback, confianza)
- `Cita` (texto, inicio_msg_id, fin_msg_id, relevancia: 0.0-1.0)
- `Bandera` (tipo: RED_FLAG, GREEN_FLAG, REVIEW_NEEDED, razón)
- `ConfianzaScore` (0.0-1.0, para ML scoring)

**Reglas Aplicadas**: REGLA-EVAL-06, REGLA-EVAL-07, REGLA-EVAL-08

---

### 3. AgregadoValidaciónRespuesta

**Entidad Raíz**: `ValidaciónRespuesta`

```
ValidaciónRespuesta (Raíz)
├── id: UUID
├── id_screening: UUID
├── id_criterio: UUID (de rúbrica)
├── validada_en: DateTime
├── tipo_validación: TipoValidación (KEYWORD, REGEX, SENTIMENT, RELEVANCE, LENGTH)
├── resultado: ResultadoValidación (PASSED, FAILED, WARNING, SKIPPED)
├── puntuación_validación: Float (0.0-1.0, antes de weightage)
├── detalles: JSON
│   ├── keywords_encontrados: Lista[String]
│   ├── matches: Int (count regex matches)
│   ├── sentiment_score: Float (-1.0 a 1.0, si aplica)
│   ├── relevancia: Float (0.0-1.0, si NLP)
│   └── longitud_respuesta: Int (chars)
├── reglas_aplicadas: Lista[String] (qué reglas se ejecutaron)
├── confianza_resultado: Float (0.0-1.0)
├── nota: String (explicación fallida si FAILED)
└── auditoría: AuditoríaEntry

Invariantes:
- tipo_validación inmutable
- resultado ∈ {PASSED, FAILED, WARNING, SKIPPED}
- puntuación_validación ∈ [0.0, 1.0]
- confianza_resultado ∈ [0.0, 1.0]
- Si FAILED: nota siempre presente (explicar fallo)
```

**Objetos de Valor**:
- `TipoValidación` enum
- `ResultadoValidación` enum
- `DetallesValidación` (JSON estructura por tipo)
- `ConfianzaValidación` (0.0-1.0)

**Reglas Aplicadas**: REGLA-EVAL-03, REGLA-EVAL-04, REGLA-EVAL-09

---

### 4. AgregadoReporte

**Entidad Raíz**: `ReporteEvaluación`

```
ReporteEvaluación (Raíz)
├── id: UUID
├── id_evaluación: UUID
├── id_campaña: UUID
├── generada_en: DateTime
├── período: PeríodoReporte (DIARIO, SEMANAL, MENSUAL)
├── resumen_ejecutivo: String (párrafo 1-2)
├── métricas_agregadas: JSON
│   ├── total_screenings: Int
│   ├── total_evaluaciones: Int
│   ├── score_promedio: Float
│   ├── distribución_decisiones: {HIRE: %, REJECT: %, PENDING: %}
│   ├── tiempo_promedio_evaluación: Int (segundos)
│   └── tasa_acuerdo_evaluador: Float (% cuando >1 evaluador)
├── problemas_identificados: Lista[Problema]
│   ├── tipo: String (BAJA_CALIDAD_RESPUESTA, JAILBREAK_ATTEMPT, etc.)
│   ├── frecuencia: Int (count)
│   ├── recomendación: String (acción correctiva)
│   └── severidad: Severidad (BAJO, MEDIO, ALTO)
├── recomendaciones_rúbrica: Lista[String] (mejoras criterios)
├── datos_export: JSON (para reportes externos)
├── auditoría: AuditoríaEntry
└── estado: EstadoReporte (BORRADOR, PUBLICADO, ARCHIVADO)

Invariantes:
- Una evaluación = un reporte (1-to-1)
- período inmutable
- score_promedio ∈ [0.0, 10.0]
- Reporte generada post-evaluación (COMPLETADA)
```

**Objetos de Valor**:
- `PeríodoReporte` enum
- `MetricasAgregadas` (JSON estructurado)
- `Problema` (tipo, frecuencia, recomendación)
- `Severidad` enum
- `EstadoReporte` enum

**Reglas Aplicadas**: REGLA-EVAL-10

---

## 💡 8 Objetos de Valor (Resumen)

| Objeto de Valor | Propósito | Invariante |
|---|---|---|
| `EstadoRúbrica` | Estado rúbrica | ACTIVA, ARCHIVADA, SUSPENDIDA |
| `Criterio` | Campo evaluación | nombre, descripción, tipo |
| `ScoreCriterio` | Puntuación criterio | score ∈ [0.0, 10.0] |
| `Decisión` | Resultado evaluación | HIRE, REJECT, PENDING, ON_HOLD |
| `TipoValidación` | Método validar respuesta | KEYWORD, REGEX, SENTIMENT, RELEVANCE |
| `ResultadoValidación` | Resultado validación | PASSED, FAILED, WARNING, SKIPPED |
| `Cita` | Trozo chat relevante | relevancia ∈ [0.0, 1.0] |
| `Bandera` | Indicador especial | RED_FLAG, GREEN_FLAG, REVIEW_NEEDED |

---

## 🔄 Máquinas de Estados

### Ciclo de Vida de Rúbrica

```
┌──────────┐
│ ACTIVA   │
└────┬─────┘
     │ archivar_rúbrica()
     ▼
┌──────────────┐
│ ARCHIVADA    │  (ya no se pueden crear nuevas evaluaciones)
└──────────────┘
```

### Ciclo de Vida de Evaluación

```
┌──────────┐
│ BORRADOR │  (evaluador completando scores)
└────┬─────┘
     │ validar_puntuaciones()
     ▼
┌──────────────┐     ┌───────────┐
│ COMPLETADA   │────►│ RECHAZADA │  (si rechazada por validación)
└────┬─────────┘     └───────────┘
     │
     │ generar_reporte()
     ▼
┌──────────────┐
│ PUBLICADA    │  (inmutable, audited)
└──────────────┘
```

### Ciclo de Vida de ValidaciónRespuesta

```
┌──────────────────┐
│ Criterio leído   │
└────┬─────────────┘
     │ aplicar_validaciones()
     ▼
   ┌─┴─────────────────────────┐
   │                            │
   ▼                            ▼
PASSED                    FAILED/WARNING
```

---

## ✅ Relaciones Entre Agregados

```
Rúbrica (Unit 4)
  └── pertenece_a: Campaña (Unit 2, foreign key)
  └── tiene_muchos: Criterio (1-to-N)
  └── versión: (para audit trail, no UPDATE)

Evaluación (Unit 4)
  ├── pertenece_a: Screening (Unit 2, foreign key)
  ├── usa: Rúbrica (versión específica)
  ├── evaluada_por: Usuario (Unit 2 reclutador)
  ├── tiene_muchos: ScoreCriterio (1-to-N)
  ├── tiene_muchos: Cita (1-to-M)
  ├── tiene_muchos: Bandera (1-to-M)
  └── genera_uno: ReporteEvaluación (1-to-1)

ValidaciónRespuesta (Unit 4)
  ├── pertenece_a: Screening (Unit 2)
  └── valida: Criterio (Rúbrica)

ReporteEvaluación (Unit 4)
  ├── resume: Evaluación (1-to-1)
  └── pertenece_a: Campaña (Unit 2)
```

---

## 📊 Tamaños de Datos Estimados

| Agregado | Típico | Máximo | Ejemplo |
|----------|--------|--------|---------|
| Rúbrica (metadata) | 3KB | 8KB | 5 criterios + metadata |
| Criterio | 500B | 2KB | nombre + descripción + reglas |
| Evaluación (scores) | 5KB | 15KB | 5 criterios + citas + feedback |
| ValidaciónRespuesta | 2KB | 5KB | detalles validación |
| ReporteEvaluación | 10KB | 50KB | métricas agregadas + problemas |

---

## 🎯 Eventos Publicados por Unit 4

| Evento | Trigger | Consumidor |
|--------|---------|-----------|
| **RúbricaCreada** | Crear rúbrica | Unit 2 (logging) |
| **RúbricaVersionada** | Nueva versión | Unit 2 (audit trail) |
| **EvaluaciónIniciada** | Inicio scoring | Unit 2 (auditoría) |
| **EvaluaciónCompletada** | Scores finales | Unit 2 (notificación reclutador) |
| **DecisiónTomada** | Decision (HIRE/REJECT) | Unit 2 (notificación candidato), Unit 6 (compliance log) |
| **ValidaciónFallida** | Validation FAILED | Unit 2 (flag revisión manual) |
| **ReporteGenerado** | Reporte completada | Unit 2 (analytics), Unit 6 (compliance) |

---

## ✅ Criterios de Aceptación (Actividad 1)

- [x] 4 Agregados definidos con entidades raíz
- [x] 8 Objetos de Valor con invariantes
- [x] Máquinas de estado (Rúbrica, Evaluación, Validación)
- [x] Relaciones entre agregados y Unit 2
- [x] Eventos publicados identificados
- [x] Tamaños estimados documentados

---

**Generado**: 2026-05-27  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 1 - Entidades del Dominio  
**Estado**: ✅ COMPLETADA

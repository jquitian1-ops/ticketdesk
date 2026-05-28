# Unit 2: Fundamentos Backend — Actividad 1: Entidades del Dominio

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 1 - Diseño Funcional: Entidades del Dominio  
**Fecha**: 2026-05-27  

---

## 📋 Contexto Acotado: Fundamentos Backend

**Alcance**: Ciclo de vida de sesión, operaciones de candidato y reclutamiento, gestión de campañas, seguimiento de consentimiento  
**Patrón**: Diseño Dirigido por Dominio (DDD) con Agregados, Objetos de Valor e Invariantes  

---

## 🎯 8 Agregados del Dominio

### 1. AgregadoSesión

**Entidad Raíz**: `Sesión`

```
Sesión (Raíz)
├── id: UUID
├── id_candidato: UUID
├── id_campaña: UUID
├── estado: EstadoSesión (CREADA, ACTIVA, PAUSADA, COMPLETADA, ABANDONADA)
├── creada_en: DateTime
├── iniciada_en: DateTime | NULL
├── completada_en: DateTime | NULL
├── abandonada_en: DateTime | NULL
├── última_actividad_en: DateTime
├── metadatos: JSON (dispositivo, ip, ubicación)
└── registro_auditoría: Lista[EntradaAuditoria]

Invariantes:
- Sesión.estado: CREADA → ACTIVA → (PAUSADA → ACTIVA)* → COMPLETADA | ABANDONADA
- Solo se abandona si ACTIVA >5min de inactividad
- Una vez COMPLETADA/ABANDONADA: INMUTABLE
- creada_en ≤ iniciada_en ≤ completada_en (sin reversiones)
```

**Objetos de Valor**:
- `EstadoSesión` enum
- `MetadatosSesión` (tipo_dispositivo, navegador, so, ip, ubicación)
- `DuraciónSesión` (inicio, fin, segundos)

**Reglas Aplicadas**: REGLA-BACKEND-01, REGLA-BACKEND-08

---

### 2. AgregadoCandidato

**Entidad Raíz**: `Candidato`

```
Candidato (Raíz)
├── id: UUID
├── correo: DirecciónCorreo
├── nombre: String
├── apellido: String
├── teléfono: NúmeroTeléfono | NULL
├── url_cv: URLEmpresa | NULL
├── estado: EstadoCandidato (REGISTRADO, EVALUANDO, EVALUADO, APROBADO, RECHAZADO, ARCHIVADO)
├── creado_en: DateTime
├── actualizado_en: DateTime
├── puntuaciones: Lista[PuntuaciónEvaluación]
└── documentos: Lista[ReferenciaDocumento]

Invariantes:
- correo es único, validado
- estado no retrocede (APROBADO permanece APROBADO)
- Si estado = ARCHIVADO: inmutable
- Máximo 1 screening activo por campaña
```

**Objetos de Valor**:
- `DirecciónCorreo` (validación, normalización)
- `NúmeroTeléfono` (formato validado)
- `EstadoCandidato` enum
- `PuntuaciónEvaluación` (puntuación: 0-100, recomendación, fecha)

**Reglas Aplicadas**: REGLA-BACKEND-02, REGLA-BACKEND-03

---

### 3. AgregadoEvaluación

**Entidad Raíz**: `Evaluación`

```
Evaluación (Raíz)
├── id: UUID
├── id_sesión: UUID
├── id_campaña: UUID
├── id_screening: UUID
├── versión_rúbrica: Int
├── puntuación: Int (0-100)
├── recomendación: Recomendación (APROBADO, RECHAZADO, REVISAR)
├── confianza: Float (0.0-1.0)
├── puntuaciones_dimensión: Map[Dimensión → Int]
├── retroalimentación: JSON (estructurado)
├── citas: Lista[Cita] (evidencia)
├── puntuación_equidad: PuntuaciónEquidad
├── estado: EstadoEvaluación (PENDIENTE, EN_PROGRESO, COMPLETADA, FALLIDA)
├── creada_en: DateTime
├── completada_en: DateTime | NULL
└── evaluado_por: NombreSistema

Invariantes:
- puntuación ∈ [0, 100]
- recomendación: APROBADO si ≥75, RECHAZADO si <50, else REVISAR
- Una vez estado = COMPLETADA: INMUTABLE
- Máximo 1 evaluación por sesión
```

**Objetos de Valor**:
- `Puntuación` (0-100 con umbrales)
- `Recomendación` enum
- `Confianza` (0.0-1.0)
- `PuntuaciónDimensión` (nombre_habilidad, puntuación, peso)
- `Cita` (fragmento_texto, marca_tiempo, confianza_coincidencia)
- `PuntuaciónEquidad` (riesgo_sesgo_general, riesgo_por_dimensión, banderas)

**Reglas Aplicadas**: REGLA-BACKEND-09, REGLA-BACKEND-10

---

### 4. AgregadoScreening

**Entidad Raíz**: `Screening`

```
Screening (Raíz)
├── id: UUID
├── id_sesión: UUID (clave foránea a Sesión)
├── id_campaña: UUID
├── versión_rúbrica: Int
├── preguntas: Lista[Pregunta]
├── mensajes: Lista[Mensaje]
├── estado: EstadoScreening (INICIADO, EN_PROGRESO, COMPLETADO, FALLIDO, PAUSADO)
├── iniciado_en: DateTime
├── completado_en: DateTime | NULL
├── presupuesto_tokens: Int (máx 2000)
├── tokens_usados: Int
├── intentos_jailbreak: Int
├── contador_fuera_tema: Int
└── url_transcripción_s3: URLs3 | NULL

Invariantes:
- tokens_usados ≤ presupuesto_tokens (cumplimiento estricto)
- intentos_jailbreak capped en 3 (then FALLIDO)
- contador_fuera_tema capped en 3 (then auto-terminar)
- Una vez COMPLETADO/FALLIDO: INMUTABLE
- mensajes ordenados cronológicamente
```

**Objetos de Valor**:
- `EstadoScreening` enum
- `Pregunta` (id, texto, orden, requerido)
- `Mensaje` (id, rol, contenido, marca_tiempo, tokens, metadatos)
- `PresupuestoTokens` (actual, límite, restante)
- `IntentoJailbreak` (patrón_coincidido, nivel_riesgo, fecha)
- `ViolaciónFueraDelTema` (id_mensaje, tipo, fecha)

**Reglas Aplicadas**: REGLA-BACKEND-04 a REGLA-BACKEND-07

---

### 5. AgregadoCampaña

**Entidad Raíz**: `Campaña`

```
Campaña (Raíz)
├── id: UUID
├── nombre: String (único)
├── descripción: String
├── cargo_objetivo: String
├── contexto_laboral: String
├── rúbrica: VersióRúbrica
├── estado: EstadoCampaña (BORRADOR, PUBLICADA, PAUSADA, ARCHIVADA)
├── publicada_en: DateTime | NULL
├── archivada_en: DateTime | NULL
├── creada_por: IDUsuario
├── creada_en: DateTime
├── actualizada_en: DateTime
├── preguntas: Lista[Pregunta]
├── plantilla_consentimiento: DocumentoConsentimiento
└── plantillas_correo: Lista[PlantillaCorreo]

Invariantes:
- nombre único por organización
- rúbrica no se modifica después de PUBLICADA (versionado)
- BORRADOR → PUBLICADA → (PAUSADA ↔ PUBLICADA)* → ARCHIVADA
- Una vez ARCHIVADA: solo lectura
```

**Objetos de Valor**:
- `EstadoCampaña` enum
- `VersióRúbrica` (versión, criterios[], dimensiones[], pesos, creada_en)
- `Pregunta` (id, texto, orden, tipo, requerido)
- `DocumentoConsentimiento` (título, cuerpo, versión)
- `PlantillaCorreo` (nombre, asunto, cuerpo, variables)

**Reglas Aplicadas**: REGLA-BACKEND-11, REGLA-BACKEND-12

---

### 6. AgregadoConsentimiento

**Entidad Raíz**: `Consentimiento`

```
Consentimiento (Raíz)
├── id: UUID
├── id_candidato: UUID
├── id_campaña: UUID
├── tipo: TipoConsentimiento (PROCESAMIENTO, GRABACIÓN, ANALÍTICA)
├── estado: EstadoConsentimiento (PENDIENTE, DADO, REVOCADO, EXPIRADO)
├── dado_en: DateTime | NULL
├── revocado_en: DateTime | NULL
├── expira_en: DateTime | NULL
├── dirección_ip: String
├── user_agent: String
└── registro_auditoría: Lista[EntradaAuditoriaConsentimiento]

Invariantes:
- Un Consentimiento por (candidato, campaña, tipo)
- flujo de estado: PENDIENTE → DADO o REVOCADO → EXPIRADO
- revocado_en solo si estado = REVOCADO
- Revocación instantánea, sin demora de 24h
```

**Objetos de Valor**:
- `TipoConsentimiento` enum
- `EstadoConsentimiento` enum
- `EntradaAuditoriaConsentimiento` (acción, fecha, ip, user_agent)

**Reglas Aplicadas**: REGLA-BACKEND-02, REGLA-BACKEND-13

---

### 7. AgregadoEntradaEventoDominio

**Entidad Raíz**: `EntradaEvento`

```
EntradaEvento (Raíz)
├── id: UUID
├── tipo_evento: String (e.g., "SesiónIniciada", "EvaluaciónCompletada")
├── id_agregado: UUID
├── tipo_agregado: String (Sesión, Screening, Evaluación, etc.)
├── carga_útil: JSON
├── fecha: DateTime
├── publicada_en: DateTime | NULL
├── intentos_reintento: Int
├── estado: EstadoEvento (PENDIENTE, PUBLICADA, FALLIDA, ARCHIVADA)
└── mensaje_error: String | NULL

Invariantes:
- tipo_evento es constante conocida
- fecha ≤ publicada_en
- flujo de estado: PENDIENTE → PUBLICADA o FALLIDA → ARCHIVADA
- FALLIDA con intentos < 5 se reintenta
```

**Objetos de Valor**:
- `TipoEvento` enum
- `CargaÚtilEvento` (JSON object)
- `EstadoEvento` enum
- `MarcaTemporalEvento` (con zona UTC)

**Reglas Aplicadas**: REGLA-BACKEND-15

---

### 8. AgregadoEntradaMemoria

**Entidad Raíz**: `EntradaMemoria`

```
EntradaMemoria (Raíz)
├── id: UUID (clave)
├── tipo_entidad: String (e.g., "Rúbrica", "PreguntasCampaña")
├── id_entidad: UUID
├── valor_json: JSON
├── expira_en: DateTime
├── creada_en: DateTime
├── actualizada_en: DateTime
├── versión: Int
└── ttl: Int (segundos, default 3600)

Invariantes:
- Memoria es efímera, expiración forzada por Redis
- versión incrementa en cada actualización
- TTL default = 3600s (1 hora), personalizable
```

**Objetos de Valor**:
- `ClaveMemoria` (tipo_entidad + id_entidad = clave única)
- `TTLMemoria` (segundos, min 60, max 86400)
- `ValorMemoria` (serializable a JSON)

**Reglas Aplicadas**: REGLA-BACKEND-14

---

## 💡 10 Objetos de Valor (Resumen)

| Objeto de Valor | Propósito | Invariante |
|---|---|---|
| `EstadoSesión` | Estado de sesión | Estados ordenados: CREADA → ACTIVA → COMPLETADA\|ABANDONADA |
| `MetadatosSesión` | Dispositivo + ubicación | tipo_dispositivo ∈ {móvil, tablet, escritorio} |
| `DirecciónCorreo` | Correo candidato | RFC 5322 compliant, único en sistema |
| `EstadoCandidato` | Ciclo de vida candidato | Progresión monótona (sin retroceso) |
| `EstadoScreening` | Estado screening | INICIADO → COMPLETADO, FALLIDO o PAUSADO |
| `Mensaje` | Mensaje chat | Ordenado por fecha, inmutable una creada |
| `PresupuestoTokens` | Seguimiento tokens | restante = límite - usado (no negativo) |
| `Recomendación` | Recomendación eval | APROBADO \| RECHAZADO \| REVISAR (basado puntuación) |
| `Cita` | Referencia evidencia | confianza_coincidencia ≥ 0.7 |
| `PuntuaciónEquidad` | Detección sesgo | banderas riesgo por dimensión |

---

## 🔄 Máquinas de Estados

### Ciclo de Vida de Sesión

```
┌───────┐
│ CREADA│
└───┬───┘
    │ iniciar()
    ↓
┌──────────┐    pausar()    ┌────────┐
│  ACTIVA  ├──────────────→ │ PAUSADA│
└──────────┘                └───┬────┘
    ↑                           │
    └──────────── reanudar()────┘
    │
    │ (>5min inactiva)
    │ completar() o abandonar()
    ↓
┌────────────┐
│ COMPLETADA │
│     o      │
│ ABANDONADA │
└────────────┘
```

### Ciclo de Vida de Evaluación

```
┌─────────┐
│PENDIENTE│
└────┬────┘
     │ iniciar_evaluación()
     ↓
┌──────────────┐
│EN_PROGRESO   │ (Procesamiento Claude API)
└────┬─────────┘
     │ (éxito)
     ↓
┌──────────┐
│COMPLETADA│
└──────────┘
     │ (fallo)
     └──────→ ┌────────┐
              │ FALLIDA│
              └────────┘
```

---

## ✅ Criterios de Aceptación (Actividad 1)

- [x] 8 Agregados definidos con entidades raíz, objetos de valor, invariantes
- [x] 10 Objetos de Valor documentados con reglas de validación
- [x] Máquinas de estados para Sesión, Screening, Evaluación
- [x] Relaciones entre agregados (pertenece_a, tiene_muchos)
- [x] Responsabilidades de publicación de eventos asignadas
- [x] Todos los agregados inmutables después de finalización
- [x] Reglas de consistencia entre agregados documentadas

---

**Generado**: 2026-05-27  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 1 - Entidades del Dominio  
**Estado**: ✅ COMPLETADA

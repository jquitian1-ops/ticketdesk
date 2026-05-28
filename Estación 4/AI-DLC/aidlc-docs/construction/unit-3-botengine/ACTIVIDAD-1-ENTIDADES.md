# Unit 3: Motor Bot (BotEngine) — Actividad 1: Entidades del Dominio

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 3 - Motor Bot (BotEngine - Integración Claude API + Detección Jailbreak)  
**Actividad**: 1 - Diseño Funcional: Entidades del Dominio  
**Fecha**: 2026-05-27  

---

## 📋 Contexto Acotado: Motor de Conversación Screening

**Alcance**: Orquestación conversaciones con Claude API, detección amenazas seguridad, gestión token budget, almacenamiento transcripciones  
**Patrón**: Domain-Driven Design con Agregados, Objetos de Valor e Invariantes  

---

## 🎯 4 Agregados del Dominio

### 1. AgregadoConversación

**Entidad Raíz**: `Conversación`

```
Conversación (Raíz)
├── id: UUID
├── id_sesión: UUID (foreign key a Sesión Unit 2)
├── id_campaña: UUID
├── estado: EstadoConversación (INICIADA, EN_PROGRESO, COMPLETADA, FALLIDA)
├── iniciad_en: DateTime
├── completada_en: DateTime | NULL
├── prompt_sistema: String (instrucción Claude, rol + contexto)
├── versión_rúbrica: Int (para trazabilidad)
├── mensajes: Lista[Mensaje] (ordenados cronológicamente)
├── presupuesto_tokens: Int (default 2000)
├── tokens_usados: Int
├── idioma_original: String (ISO 639-1, e.g., "es", "pt")
├── intentos_jailbreak: Int (0-3)
├── contador_fuera_tema: Int (0-3)
├── última_actividad_en: DateTime
└── metadatos: JSON (device, browser, location)

Invariantes:
- Conversación.estado: INICIADA → EN_PROGRESO → COMPLETADA | FALLIDA
- tokens_usados ≤ presupuesto_tokens (cumplimiento estricto)
- intentos_jailbreak y contador_fuera_tema ≤ 3 (auto-terminate)
- Una vez COMPLETADA/FALLIDA: INMUTABLE (read-only)
- mensajes ordenados por marca_tiempo ASC
- Una conversación por sesión (no múltiples)
```

**Objetos de Valor**:
- `EstadoConversación` enum
- `PromptSistema` (validado, escapado, sin inyección)
- `IdiomaOriginal` (ISO 639-1 validado)
- `PresupuestoTokens` (límite, usado, restante)
- `IntentoJailbreak` (patrón coincidido, nivel_riesgo, fecha)
- `ViolaciónFueraDelTema` (tipo, descripción, fecha)

**Reglas Aplicadas**: REGLA-BOT-01 a REGLA-BOT-10

---

### 2. AgregadoMensaje

**Entidad Raíz**: `Mensaje`

```
Mensaje (Raíz)
├── id: UUID
├── id_conversación: UUID
├── rol: RolMensaje (USUARIO, ASISTENTE, SISTEMA)
├── contenido: String (original, nunca modificado)
├── contenido_traducido: String | NULL (si idioma != inglés)
├── marca_tiempo: DateTime (inmutable)
├── número_secuencia: Int (orden en conversación)
├── tokens_usados: Int (estimados + reales de Claude API)
├── razón_parada: RazónParada | NULL (end_turn, max_tokens, stop_sequence)
├── es_eliminado: Boolean (soft delete flag)
├── metadatos: JSON (language_detected, length, etc.)
└── auditoría_creación: AuditoríaEntry (usuario, ip, timestamp)

Invariantes:
- Mensaje.id único por conversación
- Mensaje.marca_tiempo ≤ ahora (no futuros)
- Mensaje.contenido INMUTABLE (no UPDATE)
- Número_secuencia es único + ordenado (1, 2, 3, ...)
- Tokens_usados >= 0 (no negativos)
- Solo soft-delete permitido (is_eliminado=true, no hard delete)
- RolMensaje ∈ {USUARIO, ASISTENTE, SISTEMA}
```

**Objetos de Valor**:
- `RolMensaje` enum
- `ContenidoMensaje` (string, validated UTF-8, max 5000 chars)
- `NumeroSecuencia` (1-based, ordenado)
- `ConteoTokens` (estimados, reales)
- `RazónParada` (end_turn, max_tokens, stop_sequence)
- `TiempoMensaje` (DateTime, marca_tiempo)

**Reglas Aplicadas**: REGLA-BOT-01, REGLA-BOT-04

---

### 3. AgregadoDetecciónJailbreak

**Entidad Raíz**: `IntentoJailbreak`

```
IntentoJailbreak (Raíz)
├── id: UUID
├── id_conversación: UUID
├── id_mensaje: UUID (del usuario que intentó jailbreak)
├── detectado_en: DateTime
├── nivel_riesgo: NivelRiesgo (BAJO, MEDIO, ALTO, CRÍTICO)
├── patrón_coincidido: String (e.g., "PromptInjection", "Base64Encoding")
├── contenido_original: String (para análisis post)
├── patrones_detectados: Lista[String] (qué patrones regex coincidieron)
├── confianza: Float (0.0-1.0, qué tan seguro está detección)
├── acción_tomada: AcciónJailbreak (CONTINUAR, ADVERTIR, BLOQUEAR, TERMINAR)
├── usuario_notificado: Boolean
└── auditoría: AuditoríaEntry

Invariantes:
- Un IntentoJailbreak por mensaje sospechoso (no múltiples)
- nivel_riesgo ∈ {BAJO, MEDIO, ALTO, CRÍTICO}
- confianza ∈ [0.0, 1.0]
- CRÍTICO → auto-termina conversación
- 3+ intentos ALTO/MEDIO → auto-termina conversación
- Registro immutable (append-only auditoría)
```

**Objetos de Valor**:
- `NivelRiesgo` enum
- `PatrónJailbreak` (regex pattern + descripción)
- `ConfianzaDetección` (0.0-1.0)
- `AcciónJailbreak` enum
- `PatronesCoincididos` (lista de strings)

**Reglas Aplicadas**: REGLA-BOT-02, REGLA-BOT-10

---

### 4. AgregadoTranscripción

**Entidad Raíz**: `Transcripción`

```
Transcripción (Raíz)
├── id: UUID
├── id_sesión: UUID
├── id_conversación: UUID
├── url_s3_audio: URLEmpresa | NULL (para futuro, audio transcripción)
├── url_s3_texto: URLEmpresa (JSON con todos mensajes)
├── idioma_original: String (ISO 639-1)
├── creada_en: DateTime
├── actualizada_en: DateTime
├── duración_segundos: Int (duración conversación)
├── cantidad_mensajes: Int
├── tokens_totales: Int
├── metadata: JSON
│   ├── versión_claude: String (e.g., "claude-3-5-sonnet")
│   ├── modelo_usado: String
│   └── jailbreak_attempts: Int
├── encriptación: String ("AES-256-KMS")
├── url_firmada: URLEmpresa (expira 24h)
├── url_firmada_expira_en: DateTime
└── estado: EstadoTranscripción (ACTIVA, ARCHIVADA, ELIMINADA)

Invariantes:
- Una transcripción por conversación (1-to-1)
- url_s3_texto es INMUTABLE (una vez creada)
- URLs firmadas expiran 24h automáticamente
- Encriptación KMS requerida
- Estado: ACTIVA → ARCHIVADA → ELIMINADA (7 años máximo)
```

**Objetos de Valor**:
- `URLEmpresa` (S3 signed URL con validación)
- `IdiomaTranscripción` (ISO 639-1)
- `DuraciónConversación` (segundos)
- `MetadataTranscripción` (JSON estructura)
- `EstadoTranscripción` enum
- `URLFirmadaExpiry` (DateTime)

**Reglas Aplicadas**: REGLA-BOT-06, REGLA-BOT-09

---

## 💡 8 Objetos de Valor (Resumen)

| Objeto de Valor | Propósito | Invariante |
|---|---|---|
| `EstadoConversación` | Estado conversación | INICIADA → EN_PROGRESO → COMPLETADA\|FALLIDA |
| `RolMensaje` | Actor en conversación | USUARIO \| ASISTENTE \| SISTEMA |
| `NivelRiesgo` | Severidad jailbreak | BAJO < MEDIO < ALTO < CRÍTICO |
| `PresupuestoTokens` | Límite tokens | usado ≤ límite (no negativo) |
| `ConteoTokens` | Tokens mensaje | >= 0 (estimados + reales) |
| `PatrónJailbreak` | Patrón regex | Nombres constantes (PromptInjection, etc.) |
| `URLEmpresa` | URL S3 firmada | Expira 24h, encriptada KMS |
| `MetadataTranscripción` | JSON metadata | Estructura validada (versión_claude, etc.) |

---

## 🔄 Máquinas de Estados

### Ciclo de Vida de Conversación

```
┌──────────┐
│ INICIADA │
└────┬─────┘
     │ primer_mensaje_usuario()
     ↓
┌──────────────┐
│ EN_PROGRESO  │  (intercambio mensajes)
└────┬─────────┘
     │ (jailbreak_attempts >= 3 O contador_fuera_tema >= 3)
     │
     ├─→ FALLIDA (auto-terminate)
     │
     │ (todas_preguntas_respondidas O timeout_30min)
     │
     └─→ COMPLETADA (immutable)
```

### Ciclo de Vida de IntentoJailbreak

```
┌──────────────────────────────┐
│ Mensaje usuario evaluado     │
└────┬─────────────────────────┘
     │ detectar_jailbreak()
     ↓
     ├─ Nivel BAJO
     │  └─ Acción: CONTINUAR
     │
     ├─ Nivel MEDIO
     │  └─ Acción: ADVERTIR + incrementar contador
     │
     ├─ Nivel ALTO
     │  └─ Acción: BLOQUEAR RESPUESTA + incrementar contador
     │     Si contador >= 3 → Conversación.estado = FALLIDA
     │
     └─ Nivel CRÍTICO
        └─ Acción: TERMINAR INMEDIATO
           Conversación.estado = FALLIDA
```

---

## ✅ Relaciones Entre Agregados

```
Conversación (Unit 3)
  ├── pertenece_a: Sesión (Unit 2, foreign key)
  ├── pertenece_a: Campaña (Unit 2, foreign key)
  ├── tiene_muchos: Mensaje (1-to-N)
  ├── tiene_muchos: IntentoJailbreak (0-to-M)
  └── tiene_uno: Transcripción (1-to-1, creada al completar)

Mensaje
  ├── pertenece_a: Conversación
  └── referenciado_por: IntentoJailbreak (si es usuario + jailbreak)

IntentoJailbreak
  ├── pertenece_a: Conversación
  └── referencias: Mensaje (id_mensaje de usuario)

Transcripción
  ├── pertenece_a: Sesión (Unit 2)
  └── referencia: Conversación (después de COMPLETADA)
```

---

## 📊 Tamaños de Datos Estimados

| Agregado | Típico | Máximo | Ejemplo |
|----------|--------|--------|---------|
| Conversación (metadata) | 2KB | 5KB | headers, timestamps |
| Mensaje (promedio 5000 chars) | 8KB | 15KB | contenido + tokens |
| IntentoJailbreak | 1KB | 2KB | detección metadata |
| Transcripción (JSON 15 mensajes) | 150KB | 500KB | conversación completa |

---

## 🎯 Eventos Publicados por Unit 3

| Evento | Trigger | Consumidor |
|--------|---------|-----------|
| **ConversaciónIniciada** | Crear conversación | Unit 5 (UI), Unit 2 (logging) |
| **MensajeIntercambiado** | Usuario/Claude mensaje | Unit 2 (auditoría), Unit 5 (UI streaming) |
| **JailbreakDetectado** | Jailbreak attempt | Unit 2 (auditoría), Unit 6 (compliance) |
| **FueraDelTemaDetectado** | Out-of-scope message | Unit 2 (auditoría) |
| **ConversaciónCompletada** | Screening terminado | Unit 4 (trigger evaluación), Unit 5 (UI) |
| **ConversaciónFallida** | Error crítico / 3 jailbreaks | Unit 5 (UI), Unit 2 (cleanup) |

---

## ✅ Criterios de Aceptación (Actividad 1)

- [x] 4 Agregados definidos con entidades raíz
- [x] 8 Objetos de Valor con invariantes
- [x] Máquinas de estado (Conversación, IntentoJailbreak)
- [x] Relaciones entre agregados y Unit 2
- [x] Eventos publicados identificados
- [x] Tamaños estimados documentados
- [x] Todos agregados inmutables después completación

---

**Generado**: 2026-05-27  
**Unit**: 3 - Motor Bot (BotEngine)  
**Actividad**: 1 - Entidades del Dominio  
**Estado**: ✅ COMPLETADA

# Unit 5: Frontend (Next.js) — Actividad 1: Entidades del Dominio

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 5 - Frontend (Next.js 14 + React 19)  
**Actividad**: 1 - Diseño Funcional: Entidades del Dominio + Componentes  
**Fecha**: 2026-05-27  

---

## 📋 Contexto Acotado: Interfaz de Usuario Screening + Reclutamiento

**Alcance**: UI para candidatos (chat screening) y reclutadores (dashboard evaluación + gestión campañas)  
**Patrón**: Component-Driven Design con State Management (Zustand) + Server State (React Query)  

---

## 🎯 4 Agregados del Dominio (Frontend)

### 1. AgregadoEstadoSesión (Client-side State)

**Entidad Raíz**: `EstadoSesión`

```
EstadoSesión (Raíz)
├── id_sesión: UUID
├── id_candidato: UUID
├── estado_sesión: EstadoSesión (CREADA, ACTIVA, PAUSADA, COMPLETADA)
├── consentimientos_dados: Set[TipoConsentimiento] (PROCESAMIENTO, GRABACIÓN, ANALÍTICA)
├── timestamp_creación: DateTime
├── timestamp_última_actividad: DateTime
├── dispositivo_info: DispositivoInfo
│   ├── tipo: String (mobile, tablet, desktop)
│   ├── navegador: String
│   └── ubicación: Location | NULL
├── errores: Lista[MensajeError] (para mostrar notificaciones)
└── metadatos: JSON (otras UI state flags)

Invariantes:
- id_sesión único en cliente
- consentimientos_dados: ⊆ {PROCESAMIENTO, GRABACIÓN, ANALÍTICA}
- timestamp_última_actividad actualizarse en cada interacción
- errores lista < 10 (limpiar automáticamente)
- EstadoSesión solo lectura después COMPLETADA
```

**Objetos de Valor**:
- `EstadoSesión` enum (CREADA, ACTIVA, PAUSADA, COMPLETADA)
- `TipoConsentimiento` enum
- `DispositivoInfo` (tipo, navegador, ubicación)
- `MensajeError` (código, descripción, timestamp)

---

### 2. AgregadoHistorialChat (Client-side State + Server State)

**Entidad Raíz**: `HistorialChat`

```
HistorialChat (Raíz)
├── id_conversación: UUID
├── mensajes: Lista[MensajeUI] (usuario + asistente)
│   ├── id: UUID
│   ├── rol: RolMensaje (USUARIO, ASISTENTE)
│   ├── contenido: String
│   ├── marca_tiempo: DateTime
│   ├── estado_renderizado: EstadoRenderizado (PENDIENTE, RENDERIZANDO, COMPLETO, ERROR)
│   ├── tokens_usados: Int
│   └── metadatos_ui: JSON
├── está_escribiendo: Boolean (spinner)
├── error_último_mensaje: MensajeError | NULL
├── tokens_usados_total: Int
├── presupuesto_tokens_visual: PresupuestoTokensUI
│   ├── usado: Int
│   ├── límite: Int
│   ├── porcentaje: Float (0.0-1.0)
│   └── color_aviso: String (verde, amarillo, rojo)
└── scroll_estado: ScrollEstado (top, middle, bottom)

Invariantes:
- mensajes ordenados cronológicamente
- está_escribiendo es Boolean (no puede haber dos simultáneamente)
- tokens_usados_total = suma(mensajes.tokens_usados)
- tokens_usados_total ≤ presupuesto_tokens (con aviso visual)
- scroll_estado sync con viewport (auto-scroll to bottom on new message)
```

**Objetos de Valor**:
- `MensajeUI` (id, rol, contenido, estado_renderizado)
- `RolMensaje` enum
- `EstadoRenderizado` enum (PENDIENTE, RENDERIZANDO, COMPLETO, ERROR)
- `PresupuestoTokensUI` (usado, límite, porcentaje, color)
- `ScrollEstado` enum
- `MensajeError` (para mostrar en UI)

---

### 3. AgregadoEstadoReclutador (Client-side + Server State)

**Entidad Raíz**: `EstadoReclutador`

```
EstadoReclutador (Raíz)
├── id_usuario: UUID (reclutador)
├── rol: RolUsuario (RECRUITER, ADMIN)
├── campañas_acceso: Lista[UUID] (qué campañas puede ver)
├── filtro_actual: FiltroEvaluación
│   ├── estado: EstadoEvaluación (COMPLETADA, REVISIÓN, APROBADA, RECHAZADA)
│   ├── puntuación_mín: Int (0-100)
│   ├── búsqueda_texto: String
│   └── ordenar_por: String (puntuación DESC, fecha ASC, etc.)
├── cola_evaluación: ListaEvaluaciones (paginada)
│   ├── total_count: Int
│   ├── página_actual: Int
│   ├── página_tamaño: Int
│   └── evaluaciones: Lista[EvaluaciónUI]
├── evaluación_seleccionada: EvaluaciónUI | NULL
├── notas_editor: String (editadas en detail panel)
├── decisión_pendiente: Decision | NULL (PASS/FAIL/REVIEW)
└── sincronizado_servidor: Boolean (dirty flag)

Invariantes:
- rol determina permisos (ADMIN > RECRUITER)
- página_actual >= 1
- página_tamaño ∈ [10, 50]
- evaluación_seleccionada ∈ cola_evaluación OR NULL
- notas_editor max 5000 caracteres
- sincronizado_servidor = false si cambios no guardados
```

**Objetos de Valor**:
- `RolUsuario` enum
- `FiltroEvaluación` (campos filtro)
- `ListaEvaluaciones` (paginación)
- `EvaluaciónUI` (puntuación, recomendación, citas)
- `Decision` enum (PASS, FAIL, REVIEW)

---

### 4. AgregadoGestorCampañas (Server-driven State)

**Entidad Raíz**: `EstadoGestorCampañas`

```
EstadoGestorCampañas (Raíz)
├── campañas: Lista[CampaignUI]
│   ├── id: UUID
│   ├── nombre: String
│   ├── estado: EstadoCampaiga (BORRADOR, PUBLICADA, PAUSADA, ARCHIVADA)
│   ├── cargo_objetivo: String
│   ├── creada_en: DateTime
│   ├── cantidad_evaluaciones: Int
│   ├── cantidad_aprobadas: Int
│   └── progreso: Float (0.0-1.0)
├── campaña_editada: CampaignEditUI | NULL
│   ├── formulario: FormularioCampaña
│   │   ├── nombre: String
│   │   ├── descripción: String
│   │   ├── cargo_objetivo: String
│   │   └── rúbrica: RúbricaEditable
│   ├── errors_validación: Lista[FieldError]
│   └── enviando: Boolean
├── rúbrica_preview: RúbricaUI | NULL
├── modal_publicar: ModalEstado (CERRADO, CONFIRMACIÓN, ÉXITO)
└── filtro_campañas: FiltroCampaignList (estado, búsqueda)

Invariantes:
- campaña_editada = NULL si no editando
- errors_validación actualiza en tiempo real
- enviando = true mientras POST /api/campañas
- modal_publicar solo uno abierto a la vez
- rúbrica_preview sincronizada con formulario
```

**Objetos de Valor**:
- `CampaignUI` (datos campaña)
- `CampaignEditUI` (form state)
- `FormularioCampaña` (campos form)
- `RúbricaEditable` (dimensiones, pesos)
- `RúbricaUI` (preview)
- `FieldError` (campo, mensaje)
- `ModalEstado` enum
- `FiltroCampaignList` (filtros)

---

## 💡 10 Objetos de Valor (Resumen)

| Objeto de Valor | Propósito | Ubicación |
|---|---|---|
| `EstadoSesión` enum | Estado conversación en cliente | Zustand store |
| `MensajeUI` | Mensaje en chat con meta UI | Zustand store |
| `PresupuestoTokensUI` | Visualización progreso tokens | Computed state |
| `FiltroEvaluación` | Filtros queue reclutador | Zustand store |
| `EvaluaciónUI` | Evaluación con presentación | React Query cache |
| `RolUsuario` enum | Permisos reclutador | JWT claim + Zustand |
| `CampaignUI` | Campaña vista reclutador | React Query cache |
| `FormularioCampaña` | Form state campaña | Zustand store |
| `RúbricaUI` | Rúbrica presentación | Zustand store |
| `FieldError` | Error validación form | Zustand store |

---

## 🎨 4 Componentes Principales (C4 Level 3)

### 1. CandidateInterface

```
CandidateInterface/
├── ChatWindow.tsx
│   ├─ Header (timer, pregunta X de Y)
│   ├─ MessageList (scroll, streaming rendering)
│   └─ MessageInput (textarea, enviar button)
├── ConsentForm.tsx
│   ├─ Checkboxes (3 tipos)
│   ├─ Legal text
│   └─ Agree button
├── SessionStatusBar.tsx
│   ├─ Estado sesión badge
│   ├─ Tokens usados (barra progreso)
│   └─ Tiempo transcurrido
└── ErrorBoundary.tsx (global error handling)

Props/State:
  - useSessionStore() → estado sesión
  - useChatHistory() → React Query hook (mensajes)
  - useWebSocket() → streaming tokens SSE
  - onMessageSend() → callback API
```

**Responsabilidades**:
- Mostrar formulario consentimiento (requiere 3 checks)
- Renderizar chat (usuario + bot en tiempo real)
- Mostrar progreso tokens (aviso cuando >80%)
- Manejo de errores (retry, timeout)
- Scroll automático a último mensaje

---

### 2. RecruiterDashboard

```
RecruiterDashboard/
├── EvaluationQueue.tsx
│   ├─ FilterBar (estado, puntuación, búsqueda)
│   ├─ CandidateList (tabla, infinite scroll)
│   │   ├─ StatusBadge (COMPLETADA, REVIEW, APROBADA)
│   │   ├─ ScoreBadge (0-100 con color)
│   │   └─ QuickAction (click → detail panel)
│   └─ Pagination (página actual, tamaño)
├── EvaluationDetailPanel.tsx
│   ├─ CandidateInfo (email, prueba realizada en, duración)
│   ├─ EvaluationScore (display puntuación)
│   ├─ Recomendación (PASS/FAIL/REVIEW badge)
│   ├─ EvidenceCitations.tsx
│   │   └─ Transcript viewer (con highlights)
│   ├─ RecruiterNotes.tsx
│   │   └─ Textarea (auto-save on blur)
│   └─ DecisionButtons (PASS, FAIL, REVIEW, guardar)
└── RealTimeUpdates (polling 5s o WebSocket)

Props/State:
  - useRecruiterStore() → filtro, evaluación seleccionada
  - useEvaluationQueue() → React Query (paginación)
  - useSaveNotes() → mutation POST /api/evaluaciones/{id}/notas
```

**Responsabilidades**:
- Mostrar queue evaluaciones pendientes
- Filtrar/buscar (estado, puntuación mín)
- Infinit scroll (cargar más al bajar)
- Detail panel: score + transcripción + notas
- Decision buttons (PASS/FAIL/REVIEW)
- Real-time updates (status cambios mientras mira)

---

### 3. CampaignManager

```
CampaignManager/
├── CampaignList.tsx
│   ├─ Table (nombre, estado, evaluaciones, progreso)
│   ├─ StatusBadge (BORRADOR, PUBLICADA, PAUSADA, ARCHIVADA)
│   ├─ Action buttons (editar, publicar, archivar)
│   └─ CreateButton → modal
├── CampaignForm.tsx (modal)
│   ├─ FormInput (nombre, descripción)
│   ├─ FormInput (cargo_objetivo, contexto)
│   ├─ RúbricaEditor.tsx
│   │   ├─ AddDimension button
│   │   ├─ Dimension rows (nombre, peso, criterios)
│   │   └─ PreviewRubric (side-by-side)
│   ├─ FileUpload (rubric.json)
│   ├─ ValidationErrors (lista roja)
│   └─ Buttons (guardar, cancelar)
└── PublishModal.tsx
    ├─ Confirmación (¿estás seguro?)
    ├─ Preview campaña
    └─ Buttons (publicar, cancelar)

Props/State:
  - useCampaignForm() → Zustand (form state)
  - useCreateCampaign() → mutation POST /api/campañas
  - useValidateCampaign() → real-time validation
```

**Responsabilidades**:
- Listar campañas (tabla paginada)
- Crear/editar campaña (form modal)
- Editar rúbrica (inline editor)
- Validación en tiempo real
- Publicar campaña (confirmación)
- Archivar campaña (confirmación)

---

### 4. CommonUI

```
CommonUI/
├── Header.tsx
│   ├─ Logo + nombre app
│   ├─ Navigation (recruiter: Dashboard | Admin: Campaigns)
│   ├─ UserMenu (logout, perfil)
│   └─ Notification badge
├── Navigation.tsx (NavBar)
│   ├─ Links: /screening, /dashboard, /campaigns
│   └─ Active link highlight
├── ErrorBoundary.tsx
│   ├─ Fallback UI (error message)
│   └─ Retry button
├── Layout.tsx (wrapper)
│   ├─ Header
│   ├─ Navigation
│   ├─ Main content (children)
│   └─ Footer
├── Loading.tsx (spinner)
├── Pagination.tsx
│   ├─ Prev/Next buttons
│   └─ Page X of Y
└── Badge.tsx (status badges)
    ├─ Variantes: success, warning, danger
    └─ Color mapping

Props/State:
  - useAuth() → JWT token, rol usuario
  - useNotifications() → toast messages
```

**Responsabilidades**:
- Layout global (header, nav, footer)
- Autenticación UI (logout, perfil)
- Error handling (boundary)
- Loading states (spinners)
- Notificaciones (toast, snackbar)

---

## 🔄 Flujos de Estado (State Management)

### Cliente (Zustand Stores)

```
Stores:
├── authStore
│   ├─ usuario (id, email, rol)
│   ├─ token (JWT)
│   ├─ setUser(), logout()
│   └─ hasPermission(role)
├── sessionStore
│   ├─ id_sesión, estado, consentimientos
│   ├─ setSessionState(), completeSession()
│   └─ isConsentComplete()
├── chatStore
│   ├─ mensajes[], está_escribiendo
│   ├─ addMessage(), setLoading()
│   └─ getMessages()
├── recruiterStore
│   ├─ filtro, evaluación_seleccionada, cola
│   ├─ setFiltro(), selectEvaluation()
│   └─ getFilteredQueue()
└── campaignStore
    ├─ formData, rúbrica, errors
    ├─ setFormField(), addDimension()
    └─ validateForm()
```

### Servidor (React Query)

```
Hooks:
├── useSessionQuery(id_sesión)
│   └─ GET /api/sesiones/{id}
├── useScreeningMessages(id_screening)
│   └─ GET /api/screenings/{id}/mensajes (subscripciones SSE)
├── useEvaluationQueue(filtro, página)
│   └─ GET /api/evaluaciones?estado=...&página=X
├── useCampaignsList()
│   └─ GET /api/campañas
├── useSaveNotes(id_evaluación)
│   └─ POST /api/evaluaciones/{id}/notas (mutation)
└── usePublishCampaign(id_campaña)
    └─ POST /api/campañas/{id}/publicar
```

---

## 🎯 Integración con Backend (Unit 2)

| API Endpoint | Método | Componente | Parámetros |
|---|---|---|---|
| `/api/sesiones` | POST | CandidateInterface | { id_candidato, id_campaña } |
| `/api/sesiones/{id}/consentimiento` | POST | ConsentForm | { tipos: [] } |
| `/api/screenings/{id}/mensajes` | POST | ChatWindow | { contenido, rol } |
| `/api/screenings/{id}/mensajes` | GET | MessageList | SSE streaming |
| `/api/evaluaciones?estado=REVIEW` | GET | EvaluationQueue | filtro, página |
| `/api/evaluaciones/{id}` | GET | DetailPanel | - |
| `/api/evaluaciones/{id}/notas` | POST | RecruiterNotes | { notas } |
| `/api/campañas` | GET | CampaignList | - |
| `/api/campañas` | POST | CampaignForm | form data |
| `/api/campañas/{id}/publicar` | POST | PublishModal | - |
| `/api/auth/login` | POST | LoginPage | { email, password } |
| `/api/auth/refresh` | POST | (middleware) | refresh_token |

---

## 📊 Estado por Página

| Página | URL | Estado Zustand | Estado React Query |
|--------|-----|---|---|
| Consentimiento | `/screening/:id/consent` | sessionStore | useSessionQuery |
| Chat | `/screening/:id/chat` | chatStore | useScreeningMessages (SSE) |
| Dashboard | `/recruiter/dashboard` | recruiterStore | useEvaluationQueue (polling) |
| Detail | `/recruiter/evaluation/:id` | recruiterStore | useEvaluationQuery |
| Campañas | `/recruiter/campaigns` | campaignStore | useCampaignsList |
| Campaign Edit | `/recruiter/campaigns/edit/:id` | campaignStore | useCampaignQuery |

---

## ✅ Criterios de Aceptación (Actividad 1)

- [x] 4 Agregados definidos (EstadoSesión, HistorialChat, EstadoReclutador, GestorCampañas)
- [x] 10 Objetos de Valor documentados
- [x] 4 Componentes principales (Candidate, Recruiter, Campaign, Common)
- [x] State management (Zustand + React Query)
- [x] Integración endpoints backend mapeada
- [x] Flujos de datos cliente-servidor
- [x] Responsive design (mobile-first)

---

**Generado**: 2026-05-27  
**Unit**: 5 - Frontend (Next.js)  
**Actividad**: 1 - Entidades del Dominio  
**Estado**: ✅ COMPLETADA

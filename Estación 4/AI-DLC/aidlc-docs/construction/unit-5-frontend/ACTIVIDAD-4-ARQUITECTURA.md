# Unit 5: Frontend (Next.js) — Actividad 4: Arquitectura de Componentes

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 5 - Frontend (Next.js 14 + React 19)  
**Actividad**: 4 - Diseño Infraestructura: Componentes, Flujos, Despliegue  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**Arquitectura C4 Level 3** para Frontend con componentes React, flujos estado, integración API, y despliegue Vercel.

---

## 🏗️ C4 Level 1: Sistema Frontend

```
┌─────────────────────────────────────────┐
│      TicketDesk Enterprise v1.0         │
├─────────────────────────────────────────┤
│ Unit 2    │ Unit 3      │ Unit 5        │
│ Backend   │ BotEngine   │ Frontend      │
│ FastAPI   │ FastAPI     │ (Foco)        │
└─────────────────────────────────────────┘
```

---

## 🏗️ C4 Level 2: Contenedores Frontend

```
┌────────────────────────────────────────────────────────────┐
│            Vercel CDN + Next.js Runtime                    │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │      App Router (Next.js 14)                        │  │
│  │  /                                                   │  │
│  │  ├── /login          (Auth page)                     │  │
│  │  ├── /screening      (Candidate interface)           │  │
│  │  │   └── [id]        (SSE Stream)                    │  │
│  │  ├── /recruiter      (Dashboard)                     │  │
│  │  │   ├── /queue      (Evaluations pending)           │  │
│  │  │   ├── /completed  (Completed evaluations)         │  │
│  │  │   └── /analytics  (Campaign stats)                │  │
│  │  └── /campaigns      (Campaign management)           │  │
│  └─────────────────────────────────────────────────────┘  │
│              △                   △                         │
│              │                   │                         │
│  ┌───────────┴───────────┐  ┌────┴──────────────────────┐ │
│  │  Zustand Store        │  │  React Query Cache        │ │
│  │  (Global State)       │  │  (Server State)           │ │
│  │  • sessionId          │  │  • evaluations            │ │
│  │  • candidateId        │  │  • campaigns              │ │
│  │  • messages           │  │  • queue items            │ │
│  │  • jailbreakWarning   │  │  • user profile           │ │
│  └───────────┬───────────┘  └────┬──────────────────────┘ │
│              │                   │                         │
│              └───────────┬───────┘                         │
│                          ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │      API Client (Axios interceptors)                  │ │
│  │  • JWT in httpOnly (ADR-UNIT5-003)                    │ │
│  │  • CSRF token header (NFR-UNIT5-004)                  │ │
│  │  • Retry logic (exponential backoff)                  │ │
│  │  • Error handling + Sentry reporting                  │ │
│  └───────────────────────────────────────────────────────┘ │
│              △                  △                          │
│              │                  │                          │
│  ┌──────────┴─────────┐  ┌─────┴──────────────────────┐  │
│  │  Unit 2 Backend    │  │  Unit 3 BotEngine         │  │
│  │  (FastAPI)         │  │  (FastAPI + SSE)          │  │
│  │  • Auth            │  │  • /stream (ADR-UNIT5-002)│  │
│  │  • Evaluations     │  │  • /mensajes              │  │
│  │  • Campaigns       │  │  • Token budget           │  │
│  └────────────────────┘  └──────────────────────────┘  │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 🏗️ C4 Level 3: Componentes React

```
┌─ CandidateInterface (Screening) ────────────────────────┐
│                                                          │
│  Layout                                                 │
│  ├─ Header                                              │
│  │  └─ SessionTimer (30 min inactividad)                │
│  │                                                       │
│  ├─ ChatContainer                                       │
│  │  ├─ MessageList                                      │
│  │  │  └─ MessageBubble[] (USUARIO, ASISTENTE)          │
│  │  ├─ JailbreakWarning (si nivel_riesgo > BAJO)       │
│  │  └─ InputBox                                         │
│  │     └─ SubmitButton (disabled si streaming)          │
│  │                                                       │
│  └─ Footer                                              │
│     └─ ProgressBar (tokens_usados / presupuesto)       │
│                                                          │
│  Hooks:                                                 │
│  • useMessageStream() → SSE (ADR-UNIT5-002)            │
│  • useScreeningStore() → Zustand (ADR-UNIT5-001)       │
│  • useEvaluationQueue() → React Query                  │
└──────────────────────────────────────────────────────┘

┌─ RecruiterDashboard (Evaluación) ──────────────────────┐
│                                                          │
│  Layout                                                 │
│  ├─ Sidebar                                             │
│  │  └─ Navigation (Queue, Completed, Analytics)         │
│  │                                                       │
│  ├─ Queue Page                                          │
│  │  ├─ FilterBar (campaign, candidate_skill)            │
│  │  ├─ CandidateTable                                   │
│  │  │  └─ Row (avatar, name, skill, score, actions)     │
│  │  └─ PaginationControls                               │
│  │                                                       │
│  ├─ EvaluationModal                                     │
│  │  ├─ ChatReplay (historial screening)                 │
│  │  ├─ ScoringWidget                                    │
│  │  │  └─ RubricFields[] (textarea + slider)            │
│  │  ├─ DecisionButtons (Hire, Reject, Revisit)          │
│  │  └─ CitationExtractor (trozos relevantes)            │
│  │                                                       │
│  └─ Analytics Page                                      │
│     ├─ CampaignCard[] (KPIs)                            │
│     ├─ ChartThroughput (tokens/hour)                    │
│     └─ ChartAccuracy (evaluaciones completadas)         │
│                                                          │
│  Hooks:                                                 │
│  • useEvaluationQueue() → React Query + Zustand        │
│  • useScreeningReplay() → Socket.io (future)           │
└──────────────────────────────────────────────────────┘

┌─ CampaignManager (CRUD) ───────────────────────────────┐
│                                                          │
│  Layout                                                 │
│  ├─ CampaignList                                        │
│  │  └─ CampaignCard[] (name, status, progress)          │
│  │     └─ EditButton → CampaignForm                     │
│  │                                                       │
│  └─ CampaignForm (Create/Edit)                          │
│     ├─ BasicInfo (name, description)                    │
│     ├─ PromptEditor (sistema prompt)                    │
│     │  └─ PromptPreview (preview tiempo real)           │
│     ├─ RubricEditor (campos evaluación)                 │
│     │  └─ RubricPreview                                 │
│     └─ SubmitButtons (Save, Cancel, Delete)             │
│                                                          │
│  Hooks:                                                 │
│  • useCampaignForm() → React Hook Form + Zod            │
│  • useCampaignMutation() → React Query                  │
└──────────────────────────────────────────────────────┘

┌─ CommonUI (Componentes Reutilizables) ─────────────────┐
│                                                          │
│  Desde shadcn/ui (ADR-UNIT5-004):                       │
│  • Button, Input, Textarea                              │
│  • Dialog, Sheet, Popover                               │
│  • Table, Select, Checkbox                              │
│  • Card, Tabs, Badge                                    │
│  • Alert, Toast                                         │
│  • Spinner, Skeleton                                    │
│  • Avatar                                               │
│                                                          │
│  Custom wrappers:                                       │
│  • FormField (React Hook Form + Zod)                    │
│  • AuthGuard (middleware protección rutas)              │
│  • LoadingOverlay (skeleton + disabled state)           │
└──────────────────────────────────────────────────────┘
```

---

## 🔄 Flujos Principales

### 1. Screening Flujo Candidato

```
┌─ Candidato accede /screening/{id} ──────────────────┐
│                                                       │
│  1. Validar token JWT (httpOnly cookie)             │
│  2. Obtener sesión metadata (React Query)           │
│  3. Conectar SSE stream                             │
│  4. Renderizar ChatInterface                        │
│                                                       │
│  Usuario escribe mensaje                             │
│         │                                             │
│         ▼                                             │
│  ┌─────────────────────────────────────────────┐    │
│  │ InputBox → SubmitButton.click()             │    │
│  │ • Validar contenido no vacío                 │    │
│  │ • Deshabilitar inputs (disabled=true)        │    │
│  │ • POST /api/screenings/{id}/mensajes         │    │
│  │ • Body: {"contenido": "..."}                 │    │
│  └─────────────────────────────────────────────┘    │
│         │                                             │
│         ▼                                             │
│  ┌─────────────────────────────────────────────┐    │
│  │ BotEngine Unit 3                            │    │
│  │ • Detectar jailbreak (<50ms)                 │    │
│  │ • Llamar Claude API (streaming)              │    │
│  │ • Guardar mensaje BD                         │    │
│  │ • Emit SSE tokens (<100ms cada)              │    │
│  └─────────────────────────────────────────────┘    │
│         │                                             │
│         ▼                                             │
│  ┌─────────────────────────────────────────────┐    │
│  │ useMessageStream Hook (Frontend)             │    │
│  │ • Escuchar SSE eventos                       │    │
│  │ • Acumular tokens en estado Zustand          │    │
│  │ • Mostrar en tiempo real (no bloquea)        │    │
│  │ • Detectar jailbreak_warning → mostrar UI    │    │
│  └─────────────────────────────────────────────┘    │
│         │                                             │
│         ▼                                             │
│  ┌─────────────────────────────────────────────┐    │
│  │ MessageList re-render (React 19)             │    │
│  │ • Agregar MessageBubble bot                  │    │
│  │ • Auto-scroll a último mensaje                │    │
│  │ • Limpiar input para siguiente mensaje        │    │
│  │ • Actualizar token progress bar               │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  Si presupuesto tokens agotado:                      │
│  • Deshabilitar InputBox                             │
│  • Mostrar "Evaluación completada"                   │
│  • Trigger Event: ScreeningCompleted                 │
│                                                       │
└───────────────────────────────────────────────────┘
```

### 2. Evaluación Flujo Reclutador

```
┌─ Reclutador accede /recruiter/queue ────────────────┐
│                                                       │
│  1. Obtener JWT (httpOnly)                          │
│  2. useEvaluationQueue() → React Query              │
│     GET /api/screenings?estado=COMPLETADA           │
│  3. Mostrar tabla candidatos (paginada)             │
│                                                       │
│  Reclutador hace click en candidato                  │
│         │                                             │
│         ▼                                             │
│  ┌─────────────────────────────────────────────┐    │
│  │ EvaluationModal abre                         │    │
│  │ • GET /api/screenings/{id}/messages         │    │
│  │ • Cargar historial completo                  │    │
│  │ • Renderizar ChatReplay (solo lectura)       │    │
│  └─────────────────────────────────────────────┘    │
│         │                                             │
│         ▼                                             │
│  Reclutador evalúa con rúbrica                      │
│  • Llenar campos texto (feedback)                    │
│  • Ajustar sliders (puntuación)                      │
│  • Revisar citaciones automáticas                    │
│         │                                             │
│         ▼                                             │
│  ┌─────────────────────────────────────────────┐    │
│  │ DecisionButtons                              │    │
│  │ • "Contratar" → calificación HIRE             │    │
│  │ • "Rechazar" → REJECT                         │    │
│  │ • "Revisar después" → PENDING                 │    │
│  │ POST /api/screenings/{id}/evaluation         │    │
│  │ Body: {rubric_scores, decision, feedback}    │    │
│  └─────────────────────────────────────────────┘    │
│         │                                             │
│         ▼                                             │
│  Backend Unit 2:                                    │
│  • Guardar evaluación en BD                         │
│  • Publicar evento EvaluationCompleted              │
│  • Decrement queue counter                          │
│         │                                             │
│         ▼                                             │
│  Frontend React Query:                              │
│  • Invalidar cache useEvaluationQueue()              │
│  • Refetch lista (muestra siguiente candidato)      │
│  • Toast: "Evaluación guardada"                     │
│                                                       │
└───────────────────────────────────────────────────┘
```

---

## 🗂️ Estructura Directorios

```
frontend/
├── app/
│   ├── (auth)/
│   │   └── login/
│   │       ├── page.tsx
│   │       └── LoginForm.tsx
│   │
│   ├── (candidate)/
│   │   └── screening/
│   │       ├── [id]/
│   │       │   ├── page.tsx
│   │       │   ├── ChatInterface.tsx
│   │       │   ├── MessageList.tsx
│   │       │   ├── MessageBubble.tsx
│   │       │   ├── InputBox.tsx
│   │       │   └── JailbreakWarning.tsx
│   │       └── layout.tsx
│   │
│   ├── (recruiter)/
│   │   ├── layout.tsx
│   │   ├── queue/
│   │   │   ├── page.tsx
│   │   │   ├── CandidateTable.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   └── EvaluationModal.tsx
│   │   ├── analytics/
│   │   │   ├── page.tsx
│   │   │   ├── KPICards.tsx
│   │   │   └── Charts.tsx
│   │   └── completed/
│   │       └── page.tsx
│   │
│   ├── campaigns/
│   │   ├── page.tsx
│   │   ├── CampaignList.tsx
│   │   ├── CampaignCard.tsx
│   │   └── CampaignForm.tsx
│   │
│   ├── layout.tsx (root)
│   └── page.tsx
│
├── hooks/
│   ├── useMessageStream.ts       (SSE, ADR-UNIT5-002)
│   ├── useScreeningStore.ts      (Zustand, ADR-UNIT5-001)
│   ├── useEvaluationQueue.ts     (React Query)
│   ├── useCampaignForm.ts        (React Hook Form)
│   └── useAuth.ts                (JWT, ADR-UNIT5-003)
│
├── stores/
│   ├── screeningStore.ts         (Zustand)
│   └── recruiterStore.ts         (Zustand)
│
├── lib/
│   ├── api/
│   │   ├── client.ts             (Axios + interceptors)
│   │   ├── screening.ts          (endpoints)
│   │   ├── evaluation.ts         (endpoints)
│   │   └── campaigns.ts          (endpoints)
│   │
│   ├── utils/
│   │   ├── auth.ts               (JWT, cookies)
│   │   ├── validators.ts         (Zod schemas)
│   │   └── formatters.ts         (date, currency)
│   │
│   └── config.ts                 (env vars)
│
├── components/
│   ├── ui/                       (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   │
│   ├── common/
│   │   ├── AuthGuard.tsx          (middleware)
│   │   ├── LoadingOverlay.tsx      (skeleton)
│   │   └── ErrorBoundary.tsx       (Sentry)
│   │
│   └── sections/
│       ├── Header.tsx
│       ├── Footer.tsx
│       └── Sidebar.tsx
│
├── middleware.ts                 (Auth, CSRF)
├── next.config.js                (optimizaciones)
├── tailwind.config.js
└── tsconfig.json
```

---

## 💾 Estado Zustand (screeningStore.ts)

```typescript
// stores/screeningStore.ts
import create from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface ScreeningState {
  // Metadata
  sessionId: UUID;
  candidateId: UUID;
  campaignId: UUID;
  
  // Chat state
  messages: Message[];
  isStreaming: boolean;
  currentMessage: string;
  
  // Tracking
  jailbreakWarning: RiskLevel | null;
  tokensBudget: { used: number; remaining: number };
  evaluationStatus: EvaluationStatus;
  
  // Actions
  setSessionId: (id: UUID) => void;
  addMessage: (message: Message) => void;
  setStreaming: (streaming: boolean) => void;
  updateCurrentMessage: (text: string) => void;
  setJailbreakWarning: (level: RiskLevel | null) => void;
  updateTokens: (used: number, remaining: number) => void;
  completeEvaluation: (status: EvaluationStatus) => void;
  reset: () => void;
}

export const useScreeningStore = create<ScreeningState>()(
  devtools(
    persist(
      (set) => ({
        sessionId: '',
        candidateId: '',
        campaignId: '',
        messages: [],
        isStreaming: false,
        currentMessage: '',
        jailbreakWarning: null,
        tokensBudget: { used: 0, remaining: 2000 },
        evaluationStatus: 'INITIATED',
        
        setSessionId: (id) => set({ sessionId: id }),
        
        addMessage: (message) => set((state) => ({
          messages: [...state.messages, message],
          currentMessage: ''
        })),
        
        setStreaming: (streaming) => set({ isStreaming: streaming }),
        
        updateCurrentMessage: (text) => set({ currentMessage: text }),
        
        setJailbreakWarning: (level) => set({ jailbreakWarning: level }),
        
        updateTokens: (used, remaining) => set({
          tokensBudget: { used, remaining }
        }),
        
        completeEvaluation: (status) => set({
          evaluationStatus: status
        }),
        
        reset: () => set({
          messages: [],
          isStreaming: false,
          currentMessage: '',
          jailbreakWarning: null,
          tokensBudget: { used: 0, remaining: 2000 },
          evaluationStatus: 'INITIATED'
        })
      }),
      {
        name: 'screening-store',
        partialize: (state) => ({
          messages: state.messages,  // Persistir solo mensajes
          tokensBudget: state.tokensBudget
        })
      }
    ),
    { name: 'ScreeningStore' }
  )
);
```

---

## 🌐 API Client (lib/api/client.ts)

```typescript
// lib/api/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';
import * as Sentry from '@sentry/react';
import { getCookie } from 'cookies-next';

interface ApiErrorResponse {
  detail: string;
  status: number;
}

class ApiClient {
  private instance: AxiosInstance;
  
  constructor() {
    this.instance = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Request interceptor: agregar JWT + CSRF
    this.instance.interceptors.request.use((config) => {
      const csrfToken = getCookie('csrf_token') || '';
      config.headers['X-CSRF-Token'] = csrfToken;
      
      // JWT en httpOnly (automáticamente incluido)
      config.withCredentials = true;
      
      return config;
    });
    
    // Response interceptor: retry + refresh token
    this.instance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiErrorResponse>) => {
        const config = error.config;
        
        if (error.response?.status === 401 && config) {
          // Refresh token
          try {
            await this.refreshToken();
            return this.instance(config);
          } catch (refreshError) {
            // Redirect a login
            window.location.href = '/login';
          }
        }
        
        // Retry logic para 5xx errors
        if (config && !config.headers['X-Retry']) {
          config.headers['X-Retry'] = '0';
        }
        
        const retryCount = parseInt(
          (config?.headers['X-Retry'] as string) || '0'
        );
        
        if (error.response?.status && error.response.status >= 500 && retryCount < 3) {
          config!.headers['X-Retry'] = String(retryCount + 1);
          
          const delay = 1000 * Math.pow(2, retryCount);
          await new Promise((resolve) => setTimeout(resolve, delay));
          
          return this.instance(config!);
        }
        
        // Report a Sentry
        Sentry.captureException(error, {
          tags: {
            endpoint: config?.url,
            status: error.response?.status,
          },
        });
        
        return Promise.reject(error);
      }
    );
  }
  
  private async refreshToken(): Promise<void> {
    await this.instance.post('/api/auth/refresh');
  }
  
  get<T>(url: string) {
    return this.instance.get<T>(url);
  }
  
  post<T>(url: string, data?: any) {
    return this.instance.post<T>(url, data);
  }
  
  put<T>(url: string, data?: any) {
    return this.instance.put<T>(url, data);
  }
  
  delete<T>(url: string) {
    return this.instance.delete<T>(url);
  }
}

export const apiClient = new ApiClient();
```

---

## ☁️ Despliegue Vercel

```yaml
# vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  
  "env": {
    "NEXT_PUBLIC_API_URL": {
      "value": "https://api.ticketdesk.com"
    },
    "NEXT_PUBLIC_SENTRY_DSN": {
      "value": "@sentry/dsn"
    }
  },
  
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Content-Security-Policy",
          "value": "script-src 'self' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ],
  
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "$NEXT_PUBLIC_API_URL/api/:path*"
    }
  ]
}
```

---

## ✅ Criterios de Aceptación (Actividad 4)

- [x] C4 Level 3 arquitectura completa
- [x] 4 Main components documentados (Candidate, Recruiter, Campaign, CommonUI)
- [x] Flujos principales (Screening, Evaluation)
- [x] Zustand store con persistencia
- [x] API client con retry + refresh logic
- [x] Integración SSE (ADR-UNIT5-002)
- [x] Integración JWT httpOnly (ADR-UNIT5-003)
- [x] Despliegue Vercel documentado
- [x] Security headers (CSP, X-Frame-Options)

---

**Generado**: 2026-05-27  
**Unit**: 5 - Frontend (Next.js)  
**Actividad**: 4 - Infraestructura y Arquitectura  
**Estado**: ✅ COMPLETADA

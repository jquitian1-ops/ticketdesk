# Unit 5: Frontend — Plan de Ejecución

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction  
**Unit**: 5 - Frontend (Next.js 14 + React UI)  
**Duración Estimada**: Semanas 3-5 (2-3 semanas)  
**Team**: 2 Frontend Engineers  
**Bloqueador**: Unit 1 ✅ (infrastructure for deployment)  
**Bloquea**: Unit 6 (dashboard for HITL)  
**Status**: ⏳ Can start in parallel with Unit 2

---

## 📋 Objetivo Unit 5

Construir la **interfaz web completa** para candidatos y reclutadores:

1. ✅ CandidateInterface (chat screening UI)
2. ✅ Consent form + legal disclaimers
3. ✅ RecruiterDashboard (evaluation queue)
4. ✅ Candidate detail panel (feedback + score)
5. ✅ CampaignManager (CRUD campaigns)
6. ✅ Real-time updates (polling + WebSocket)
7. ✅ Authentication + routing
8. ✅ Responsive design (mobile-first)

**Métricas de éxito**:
- React Query + Zustand state management
- >80% test coverage
- Mobile-responsive
- Chat streaming UX (real-time tokens)
- 10+ integration tests

---

## 🎯 5 Actividades de Unit 5

### Actividad 1: Diseño Funcional (3 horas)

**4 Components (C4 Level 3)**:

1. **CandidateInterface**:
   - Chat window (messages, streaming responses)
   - Consent form (checkbox, legal text)
   - Session status (timer, question count)
   - Error handling (retry, timeout messages)

2. **RecruiterDashboard**:
   - Queue of candidates (infinite scroll)
   - Filter/search by campaign
   - Status badges (COMPLETED, PENDING, REVIEW)
   - Click to view detail panel

3. **CandidateDetailPanel**:
   - Evaluation score + recommendation
   - Evidence citations (quoted transcript)
   - Recruiter notes (textarea)
   - Decision buttons (PASS, FAIL, REVIEW)
   - Transcript + audio player

4. **CampaignManager**:
   - List campaigns (table)
   - Create/edit campaign (form)
   - Upload rubric (JSON or markdown)
   - Publish/archive campaign

**User Flows** (5 E2E):
1. **Candidate Consent Flow** → agree → enter chat
2. **Chat Screening** → message → stream response → complete
3. **Recruiter Review** → see queue → click candidate → read eval → decide
4. **Campaign Creation** → fill form → upload rubric → publish
5. **Real-time Updates** → recruiter receives notification of completion

---

### Actividad 2: NFR Requirements (2 horas)

**6 NFRs**:
1. **Performance**: Page load <2s, chat response <1s
2. **Usability**: Mobile-first responsive design
3. **Accessibility**: WCAG 2.1 AA compliant (contrast, keyboard nav)
4. **Reliability**: Handle offline gracefully (IndexedDB cache)
5. **Security**: CSRF tokens, XSS prevention, auth validation
6. **Observability**: Error tracking (Sentry), analytics (Mixpanel)

---

### Actividad 3: NFR Design (2 horas)

**4 ADRs**:
1. **ADR-UNIT5-001**: State Management (Zustand vs Redux vs Context)
2. **ADR-UNIT5-002**: Real-time Updates (polling vs WebSocket)
3. **ADR-UNIT5-003**: Authentication (JWT + refresh token rotation)
4. **ADR-UNIT5-004**: Component Library (shadcn/ui vs Chakra vs custom)

---

### Actividad 4: Infrastructure Design (2 horas)

**Tech Stack**:
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **State**: Zustand + React Query
- **HTTP**: Axios + React Query
- **Forms**: React Hook Form + Zod
- **Testing**: Jest + React Testing Library
- **Deployment**: Vercel (or ECS with docker build)

**Component Structure**:
```
app/
├── (auth)/                    # Auth pages
│   ├── login/page.tsx
│   └── layout.tsx
├── (candidate)/               # Candidate pages
│   ├── screening/[id]/page.tsx
│   └── consent/[id]/page.tsx
├── (recruiter)/               # Recruiter pages
│   ├── dashboard/page.tsx
│   ├── candidate/[id]/page.tsx
│   └── campaigns/page.tsx
└── layout.tsx                 # Root layout

components/
├── CandidateInterface/        # Chat UI
│   ├── ChatWindow.tsx
│   ├── MessageList.tsx
│   └── MessageInput.tsx
├── RecruiterDashboard/        # Queue
│   ├── CandidateQueue.tsx
│   └── CandidateDetail.tsx
├── CampaignManager/           # Campaign CRUD
│   ├── CampaignForm.tsx
│   └── CampaignList.tsx
└── Common/                    # Shared
    ├── Header.tsx
    ├── Navigation.tsx
    └── ErrorBoundary.tsx

hooks/
├── useAuth.ts                 # Auth context
├── useCandidateQueue.ts       # React Query hook
└── useWebSocket.ts            # Real-time updates

services/
├── api.ts                     # Axios instance
├── candidate.ts               # Candidate API
├── recruiter.ts               # Recruiter API
└── auth.ts                    # Auth API

store/
├── auth.store.ts              # Zustand auth
├── ui.store.ts                # UI state
└── campaign.store.ts          # Campaign state

__tests__/
├── CandidateInterface.test.tsx
├── RecruiterDashboard.test.tsx
└── integration/
    ├── screening-flow.test.tsx
    └── campaign-creation.test.tsx
```

---

### Actividad 5: Code Generation + Tests (4 horas)

**Priority Components**:
1. **CandidateInterface** (streaming chat)
   - Token-by-token rendering (WebSocket + SSE fallback)
   - Spinner while streaming
   - Error recovery (retry button)

2. **RecruiterDashboard** (queue)
   - Infinite scroll (pagination)
   - Real-time status updates (polling 5s)
   - Filter/search (React Query cache)

3. **CandidateDetailPanel** (evaluation view)
   - Evaluation score display
   - Citations (highlighted in transcript)
   - Recruiter notes (textarea, save on blur)
   - Decision buttons (PASS/FAIL/REVIEW)

4. **CampaignManager** (admin)
   - Form validation (Zod)
   - File upload (rubric.json)
   - Preview rubric
   - Publish/archive

**Tests** (15+ total):
- Unit: Component rendering, state updates, event handlers
- Integration: API calls, state sync, real-time updates
- E2E: Full screening flow, dashboard interaction

**Key Tech Patterns**:
- React Query for server state
- Zustand for client state
- React Hook Form for forms
- Tailwind for styling
- Zod for validation

---

## 📊 Team (2 Frontend Engineers)

**Split**:
- **Engineer 1**: CandidateInterface + chat streaming
- **Engineer 2**: RecruiterDashboard + CampaignManager
- **Sync**: Layout, navigation, auth flow

**Timeline**:
- **Week 3 (4d)**: Design + component structure
- **Week 4 (3d)**: Core components + API integration
- **Week 5 (3d)**: Real-time features + testing

---

**Generado**: 2026-05-27  
**Unit**: 5 - Frontend  
**Status**: ⏳ Can start immediately (no Unit 2 blocker)


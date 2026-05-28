# Unit 5: Frontend (Next.js) — Actividad 3: Decisiones de Arquitectura (ADR)

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 5 - Frontend (Next.js 14 + React 19)  
**Actividad**: 3 - Diseño NFR: Architecture Decision Records (ADR)  
**Fecha**: 2026-05-27  

---

## 🎯 ADR-UNIT5-001: Gestión de Estado (Zustand vs Redux vs Context API)

**Título**: Elegir framework gestión estado global frontend

**Estado**: ✅ ACEPTADA

### Contexto

Necesita gestionar estado global para:
- Sesión activa (candidato, evaluación en progreso)
- Historial chat bidireccional
- Estado formularios multipasos
- Cache evaluaciones
- Interacción con Unit 3 (BotEngine)

Opciones:
- **Zustand**: Ligero, simple, TS-first
- **Redux Toolkit**: Maduro, devtools robustos, boilerplate
- **Context API**: Nativo React, sin dependencias

### Opciones Evaluadas

**Opción 1: Zustand** ✅ ELEGIDA
- ✅ Bundle size ~2KB (vs Redux ~40KB)
- ✅ API simplista (no boilerplate)
- ✅ DevTools integrado
- ✅ SSR-compatible (Next.js App Router)
- ✅ Acciones síncronas + asincrónicas
- ❌ Comunidad menor que Redux

**Opción 2: Redux Toolkit**
- ✅ Ecosistema maduro (redux-persist, redux-saga)
- ✅ Time-travel debugging
- ❌ 40KB bundle (impacto Web Vitals)
- ❌ Curva aprendizaje (slice, thunk, middleware)
- ❌ Boilerplate excesivo

**Opción 3: Context API + useReducer**
- ✅ Cero dependencias
- ❌ Causa re-renders innecesarios (descender props)
- ❌ Sin devtools
- ❌ Performance degradación con N subscribers

### Decisión

**✅ Zustand para estado global**

### Consecuencias

```typescript
// stores/screeningStore.ts
import create from 'zustand';

interface ScreeningState {
  sessionId: UUID;
  candidateId: UUID;
  messages: Message[];
  evaluationStatus: EvaluationStatus;
  isStreaming: boolean;
  jailbreakWarning: boolean | null;
  
  // Acciones
  addMessage: (message: Message) => void;
  setStreaming: (isStreaming: boolean) => void;
  detectJailbreak: (level: RiskLevel) => void;
  completeEvaluation: (result: EvaluationResult) => void;
  resetState: () => void;
}

export const useScreeningStore = create<ScreeningState>((set) => ({
  sessionId: '',
  candidateId: '',
  messages: [],
  evaluationStatus: 'IN_PROGRESS',
  isStreaming: false,
  jailbreakWarning: null,
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  setStreaming: (isStreaming) => set({ isStreaming }),
  
  detectJailbreak: (level) => set({
    jailbreakWarning: level >= 'ALTO'
  }),
  
  completeEvaluation: (result) => set({
    evaluationStatus: 'COMPLETED',
    // trigger Unit 4 evaluation
  }),
  
  resetState: () => set({
    messages: [],
    evaluationStatus: 'INITIATED',
    jailbreakWarning: null
  })
}));

// Uso en componentes
function ChatInterface() {
  const { messages, addMessage, isStreaming } = useScreeningStore();
  
  return (
    <div>
      {messages.map((msg) => (
        <Message key={msg.id} content={msg.content} />
      ))}
    </div>
  );
}
```

---

## 🎯 ADR-UNIT5-002: Actualizaciones Tiempo Real (Polling vs WebSocket vs SSE)

**Título**: Elegir mecanismo recibir tokens Claude en tiempo real desde BotEngine

**Estado**: ✅ ACEPTADA

### Contexto

Unit 3 (BotEngine) emite tokens Claude mediante SSE. Frontend debe:
- Mostrar respuesta bot en tiempo real (streaming)
- Manejar interrupciones de conexión
- Detectar jailbreak warnings (Unit 3 → Unit 5)
- Sincronizar chat history en background

### Opciones

**Opción 1: Server-Sent Events (SSE)** ✅ ELEGIDA
- ✅ Nativo navegador (EventSource API)
- ✅ Simplifica integración con Unit 3 ADR-UNIT3-001
- ✅ Bajo latency tokens (<100ms)
- ✅ Auto-reconnect con exponential backoff
- ✅ Menor overhead que WebSocket

**Opción 2: WebSocket**
- ✅ Bidireccional (útil para futuros features)
- ❌ Mayor complejidad (heartbeat, reconnect)
- ❌ Overhead HTTP upgrade

**Opción 3: Polling**
- ✅ Simple de implementar
- ❌ Latencia 500ms+ (mala UX)
- ❌ Carga servidor

### Decisión

**✅ Server-Sent Events (SSE) + React Query para sync background**

### Consecuencias

```typescript
// hooks/useMessageStream.ts
import { useEffect, useRef } from 'react';
import { useScreeningStore } from '@/stores/screeningStore';

export function useMessageStream(screeningId: UUID) {
  const { addMessage, setStreaming, detectJailbreak } = useScreeningStore();
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    setStreaming(true);
    let reconnectAttempts = 0;
    const MAX_RETRIES = 5;
    const BASE_DELAY = 1000;

    const connect = () => {
      const eventSource = new EventSource(
        `/api/screenings/${screeningId}/mensajes/stream`
      );

      eventSource.onmessage = (event) => {
        try {
          const { token, type, jailbreak_level } = JSON.parse(event.data);
          
          if (type === 'token') {
            addMessage({ role: 'assistant', content: token });
            reconnectAttempts = 0; // Reset on success
          }
          
          if (type === 'jailbreak_warning') {
            detectJailbreak(jailbreak_level);
          }
        } catch (e) {
          console.error('Parse error:', e);
        }
      };

      eventSource.onerror = (error) => {
        eventSource.close();
        setStreaming(false);
        
        if (reconnectAttempts < MAX_RETRIES) {
          const delay = BASE_DELAY * Math.pow(2, reconnectAttempts);
          setTimeout(connect, delay);
          reconnectAttempts++;
        }
      };

      eventSourceRef.current = eventSource;
    };

    connect();

    return () => {
      eventSourceRef.current?.close();
      setStreaming(false);
    };
  }, [screeningId]);
}

// Componente
function ChatWindow() {
  const screeningId = useParams().id;
  useMessageStream(screeningId);
  
  const { messages } = useScreeningStore();
  
  return (
    <div className="chat-container">
      {messages.map((msg) => (
        <ChatBubble key={msg.id} message={msg} />
      ))}
    </div>
  );
}
```

---

## 🎯 ADR-UNIT5-003: Autenticación (localStorage vs httpOnly vs OAuth2)

**Título**: Elegir método almacenar y transmitir JWT entre frontend y backend

**Estado**: ✅ ACEPTADA

### Contexto

Necesita autenticar usuarios con backend (Unit 2):
- JWT generado por backend (RS256 ADR-BACKEND-001)
- Persistencia entre sesiones (refresh token)
- Protección contra XSS + CSRF
- Compatible con mobile + desktop

### Opciones

**Opción 1: JWT en httpOnly Cookie + CSRF Token** ✅ ELEGIDA
- ✅ Inmune XSS (no accesible JavaScript)
- ✅ Auto-enviado cada request (transparente)
- ✅ CSRF token en form headers
- ✅ SameSite=Strict nativo navegador

**Opción 2: localStorage**
- ❌ Vulnerable XSS (acceso JavaScript)
- ❌ Requires manual header injection
- ✅ Funciona en algunos SPA patterns

**Opción 3: OAuth2 con tercero**
- ✅ Delega seguridad a Google/Microsoft
- ❌ Complejidad OIDC/redirect flows
- ❌ Dependencia externa (SLA)

### Decisión

**✅ JWT en httpOnly Cookie + CSRF Token + Refresh Token**

### Consecuencias

```typescript
// middleware.ts (Next.js)
import { NextRequest, NextResponse } from 'next/server';

export async function middleware(request: NextRequest) {
  // JWT automáticamente incluido en cookie
  const token = request.cookies.get('auth_token')?.value;
  
  if (!token && !request.nextUrl.pathname.startsWith('/login')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // Validar CSRF token para POST/PUT/DELETE
  if (['POST', 'PUT', 'DELETE'].includes(request.method)) {
    const csrfToken = request.headers.get('x-csrf-token');
    const sessionCsrf = request.cookies.get('csrf_token')?.value;
    
    if (csrfToken !== sessionCsrf) {
      return NextResponse.json(
        { error: 'CSRF token invalid' },
        { status: 403 }
      );
    }
  }
  
  return NextResponse.next();
}

// API client con refresh automático
class ApiClient {
  private static instance: ApiClient;
  
  static getInstance() {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }
  
  async request<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(url, {
      ...options,
      credentials: 'include', // Incluir cookie httpOnly
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': this.getCsrfToken(),
        ...options.headers,
      },
    });
    
    // Si 401, refresh token
    if (response.status === 401) {
      await this.refreshToken();
      return this.request<T>(url, options); // Reintentar
    }
    
    return response.json();
  }
  
  private async refreshToken() {
    await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
  }
  
  private getCsrfToken(): string {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta?.getAttribute('content') || '';
  }
}

export const apiClient = ApiClient.getInstance();
```

---

## 🎯 ADR-UNIT5-004: Librería de Componentes (shadcn/ui vs Chakra UI vs Custom)

**Título**: Elegir componentes base para recrutadores + interfaz candidato

**Estado**: ✅ ACEPTADA

### Contexto

Necesita componentes reutilizables para:
- Dashboard reclutador (tablas, modales, gráficos)
- Interfaz chat candidato (responsive, accessible)
- Formularios dinámicos (validación, layout)
- Temas oscuro/claro (WCAG AA)

### Opciones

**Opción 1: shadcn/ui** ✅ ELEGIDA
- ✅ Copy-paste (no dependencia npm)
- ✅ 100% customizable (Tailwind)
- ✅ Unstyled headless + Radix
- ✅ A11y built-in (WCAG AA)
- ✅ Bundle size control (solo usa lo que copia)

**Opción 2: Chakra UI**
- ✅ Props API intuitiva
- ✅ Excelente docs
- ❌ Tight coupling (difícil customizar)
- ❌ CSS-in-JS overhead

**Opción 3: Custom Components**
- ✅ 100% control
- ❌ +40% tiempo desarrollo
- ❌ A11y bugs probables
- ❌ Difícil mantener

### Decisión

**✅ shadcn/ui + Tailwind CSS + Radix UI para accesibilidad**

### Consecuencias

```typescript
// components/ui/Button.tsx (copiado de shadcn)
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md text-sm font-medium",
        {
          "default": "bg-blue-600 text-white hover:bg-blue-700",
          "destructive": "bg-red-600 text-white hover:bg-red-700",
          "outline": "border border-gray-300 hover:bg-gray-50",
        }[variant],
        {
          "default": "h-10 px-4 py-2",
          "sm": "h-9 px-3",
          "lg": "h-12 px-8",
          "icon": "h-10 w-10",
        }[size],
        className
      )}
      ref={ref}
      {...props}
    />
  )
);

Button.displayName = "Button";

export { Button };

// Uso en RecruiterDashboard
function EvaluationActions() {
  return (
    <div className="flex gap-2">
      <Button variant="default">Evaluar</Button>
      <Button variant="outline">Descartar</Button>
      <Button variant="destructive">Bloquear</Button>
    </div>
  );
}
```

---

## 📊 Matriz ADRs

| ADR | Decisión | Alternativa | Razón |
|---|---|---|---|
| ADR-UNIT5-001 | Zustand | Redux | Bundle size + API simplicidad |
| ADR-UNIT5-002 | SSE | WebSocket | Integración con Unit 3, bajo latency |
| ADR-UNIT5-003 | httpOnly + CSRF | localStorage | Seguridad XSS nativa |
| ADR-UNIT5-004 | shadcn/ui | Chakra | Customización + A11y control |

---

## ✅ Criterios de Aceptación (Actividad 3)

- [x] 4 ADRs documentados (formato CODC)
- [x] Opciones evaluadas objetivamente
- [x] Decisiones con consecuencias documentadas
- [x] Implementación código en TypeScript/React
- [x] Integración con Units 2 y 3 mapeada

---

**Generado**: 2026-05-27  
**Unit**: 5 - Frontend (Next.js)  
**Actividad**: 3 - Decisiones Arquitectura  
**Estado**: ✅ COMPLETADA

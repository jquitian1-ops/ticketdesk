# Unit 5: Frontend (Next.js) — Actividad 5: Código e Implementación

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 5 - Frontend (Next.js 14 + React 19)  
**Actividad**: 5 - Implementación: Código + Tests  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**Componentes React** para candidato y reclutador. Incluye hooks personalizados, servicios API, y tests end-to-end.

---

## 🎯 Componente: ChatInterface (Screening Candidato)

```typescript
// app/(candidate)/screening/[id]/ChatInterface.tsx
'use client';

import { useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { useScreeningStore } from '@/stores/screeningStore';
import { useMessageStream } from '@/hooks/useMessageStream';
import { MessageList } from './MessageList';
import { InputBox } from './InputBox';
import { JailbreakWarning } from './JailbreakWarning';
import { SessionTimer } from '@/components/common/SessionTimer';
import { ProgressBar } from '@/components/ui/progress';

export function ChatInterface() {
  const params = useParams();
  const screeningId = params.id as string;
  
  // Global state
  const {
    messages,
    isStreaming,
    jailbreakWarning,
    tokensBudget,
    evaluationStatus,
  } = useScreeningStore();
  
  // SSE streaming hook (ADR-UNIT5-002)
  useMessageStream(screeningId);
  
  // Auto-scroll a último mensaje
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const canContinue = evaluationStatus === 'IN_PROGRESS' && !isStreaming;
  const tokenPercentage = (tokensBudget.used / (tokensBudget.used + tokensBudget.remaining)) * 100;
  
  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      {/* Header */}
      <div className="border-b bg-white shadow-sm px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Entrevista IA
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Responde las preguntas de evaluación
            </p>
          </div>
          <SessionTimer screeningId={screeningId} />
        </div>
        
        {/* Token Progress */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="font-medium text-gray-700">Progreso</span>
            <span className="text-gray-600">
              {tokensBudget.used} / {tokensBudget.used + tokensBudget.remaining} tokens
            </span>
          </div>
          <ProgressBar value={tokenPercentage} className="h-2" />
        </div>
      </div>
      
      {/* Jailbreak Warning */}
      {jailbreakWarning && (
        <JailbreakWarning level={jailbreakWarning} />
      )}
      
      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <div className="border-t bg-white px-6 py-4">
        <InputBox
          disabled={!canContinue}
          isStreaming={isStreaming}
          screeningId={screeningId}
        />
        
        {evaluationStatus === 'COMPLETED' && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800 font-semibold">
              ✓ Evaluación completada
            </p>
            <p className="text-green-700 text-sm mt-1">
              Tu respuestas fueron registradas. El reclutador las revisará pronto.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 💬 Componente: MessageBubble

```typescript
// app/(candidate)/screening/[id]/MessageBubble.tsx
'use client';

import { Message } from '@/lib/api/screening';
import { cn } from '@/lib/utils';
import { Markdown } from '@/components/common/Markdown';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.rol === 'USUARIO';
  
  return (
    <div
      className={cn(
        'flex gap-3 animate-fade-in',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {!isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
        </div>
      )}
      
      <div
        className={cn(
          'max-w-xs px-4 py-3 rounded-lg',
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-gray-100 text-gray-900 rounded-bl-none'
        )}
      >
        {isUser ? (
          <p className="text-sm">{message.contenido}</p>
        ) : (
          <Markdown content={message.contenido} className="text-sm" />
        )}
        
        <p className={cn(
          'text-xs mt-1',
          isUser ? 'text-blue-100' : 'text-gray-500'
        )}>
          {new Date(message.marca_tiempo).toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
}
```

---

## ⌨️ Componente: InputBox

```typescript
// app/(candidate)/screening/[id]/InputBox.tsx
'use client';

import { FormEvent, useState } from 'react';
import { useScreeningStore } from '@/stores/screeningStore';
import { apiClient } from '@/lib/api/client';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/useToast';

interface InputBoxProps {
  disabled: boolean;
  isStreaming: boolean;
  screeningId: string;
}

export function InputBox({
  disabled,
  isStreaming,
  screeningId,
}: InputBoxProps) {
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { setStreaming } = useScreeningStore();
  const { toast } = useToast();
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!message.trim() || disabled || isSubmitting) {
      return;
    }
    
    try {
      setIsSubmitting(true);
      setStreaming(true);
      
      const response = await apiClient.post(
        `/api/screenings/${screeningId}/mensajes`,
        { contenido: message }
      );
      
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      
      setMessage('');
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Error desconocido';
      toast({
        variant: 'destructive',
        title: 'Error',
        description: errorMsg,
      });
    } finally {
      setIsSubmitting(false);
      setStreaming(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Escribe tu respuesta..."
        disabled={disabled || isSubmitting || isStreaming}
        className="resize-none"
        rows={3}
      />
      
      <Button
        type="submit"
        disabled={disabled || isSubmitting || isStreaming || !message.trim()}
        className="w-full"
      >
        {isSubmitting ? 'Enviando...' : 'Enviar Respuesta'}
      </Button>
    </form>
  );
}
```

---

## 🎯 Componente: EvaluationModal (Reclutador)

```typescript
// app/(recruiter)/queue/EvaluationModal.tsx
'use client';

import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Screening } from '@/lib/api/screening';
import { apiClient } from '@/lib/api/client';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ChatReplay } from '@/components/sections/ChatReplay';
import { ScoringWidget } from './ScoringWidget';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/useToast';

interface EvaluationModalProps {
  screening: Screening;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EvaluationModal({
  screening,
  open,
  onOpenChange,
}: EvaluationModalProps) {
  const [scores, setScores] = useState<Record<string, number>>({});
  const [feedback, setFeedback] = useState('');
  const [decision, setDecision] = useState<'HIRE' | 'REJECT' | 'PENDING' | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  const handleSubmit = async () => {
    if (!decision) {
      toast({
        variant: 'destructive',
        title: 'Decisión requerida',
        description: 'Por favor selecciona una decisión',
      });
      return;
    }
    
    try {
      setIsSubmitting(true);
      
      await apiClient.post(
        `/api/screenings/${screening.id}/evaluation`,
        {
          rubric_scores: scores,
          decision,
          feedback,
          evaluated_at: new Date().toISOString(),
        }
      );
      
      // Invalidar cache
      await queryClient.invalidateQueries({
        queryKey: ['evaluationQueue'],
      });
      
      toast({
        title: 'Éxito',
        description: 'Evaluación guardada correctamente',
      });
      
      onOpenChange(false);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'No se pudo guardar la evaluación',
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Evaluar: {screening.candidato_nombre}
          </DialogTitle>
        </DialogHeader>
        
        <div className="grid grid-cols-2 gap-6">
          {/* Historial Chat */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Respuestas</h3>
            <ChatReplay messages={screening.messages} />
          </div>
          
          {/* Evaluación */}
          <div className="space-y-4">
            <ScoringWidget
              rubric={screening.rubric}
              scores={scores}
              onScoresChange={setScores}
            />
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Feedback
              </label>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="w-full p-2 border rounded text-sm"
                rows={4}
                placeholder="Notas internas sobre el candidato..."
              />
            </div>
            
            {/* Decision Buttons */}
            <div className="flex gap-2 pt-4">
              <Button
                variant={decision === 'HIRE' ? 'default' : 'outline'}
                onClick={() => setDecision('HIRE')}
                className="flex-1"
              >
                ✓ Contratar
              </Button>
              <Button
                variant={decision === 'REJECT' ? 'destructive' : 'outline'}
                onClick={() => setDecision('REJECT')}
                className="flex-1"
              >
                ✗ Rechazar
              </Button>
              <Button
                variant={decision === 'PENDING' ? 'outline' : 'outline'}
                onClick={() => setDecision('PENDING')}
                className="flex-1"
              >
                ⟲ Revisar
              </Button>
            </div>
            
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting || !decision}
              className="w-full"
            >
              {isSubmitting ? 'Guardando...' : 'Guardar Evaluación'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

---

## 🪝 Hook: useMessageStream (SSE)

```typescript
// hooks/useMessageStream.ts
import { useEffect, useRef } from 'react';
import { useScreeningStore } from '@/stores/screeningStore';

interface StreamMessage {
  token?: string;
  type: 'token' | 'jailbreak_warning' | 'error';
  jailbreak_level?: string;
}

export function useMessageStream(screeningId: string) {
  const {
    addMessage,
    setStreaming,
    setJailbreakWarning,
    updateTokens,
    completeEvaluation,
    messages,
  } = useScreeningStore();
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  
  useEffect(() => {
    const MAX_RETRIES = 5;
    const BASE_DELAY = 1000;
    
    const connect = () => {
      const eventSource = new EventSource(
        `/api/screenings/${screeningId}/mensajes/stream`
      );
      
      eventSource.onmessage = (event) => {
        try {
          const data: StreamMessage = JSON.parse(event.data);
          
          switch (data.type) {
            case 'token':
              if (data.token) {
                // Acumular token a último mensaje
                addMessage({
                  id: Math.random().toString(),
                  numero_secuencia: messages.length,
                  rol: 'ASISTENTE',
                  contenido: data.token,
                  marca_tiempo: new Date().toISOString(),
                  tokens_usados: 0,
                });
              }
              reconnectAttemptsRef.current = 0;
              break;
            
            case 'jailbreak_warning':
              if (data.jailbreak_level) {
                setJailbreakWarning(data.jailbreak_level);
              }
              break;
            
            case 'error':
              console.error('Stream error:', data);
              break;
          }
        } catch (e) {
          console.error('Parse error:', e);
        }
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        setStreaming(false);
        
        if (reconnectAttemptsRef.current < MAX_RETRIES) {
          const delay = BASE_DELAY * Math.pow(2, reconnectAttemptsRef.current);
          setTimeout(connect, delay);
          reconnectAttemptsRef.current++;
        }
      };
      
      eventSourceRef.current = eventSource;
      setStreaming(true);
    };
    
    connect();
    
    return () => {
      eventSourceRef.current?.close();
      setStreaming(false);
    };
  }, [screeningId]);
}
```

---

## 🧪 Tests (Jest + React Testing Library)

```typescript
// __tests__/ChatInterface.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '@/app/(candidate)/screening/[id]/ChatInterface';
import { useScreeningStore } from '@/stores/screeningStore';

// Mock datos
const mockScreening = {
  id: 'test-123',
  estado: 'EN_PROGRESO',
  messages: [],
  tokensBudget: { used: 100, remaining: 1900 },
};

describe('ChatInterface', () => {
  beforeEach(() => {
    // Reset store
    useScreeningStore.getState().reset();
  });
  
  it('debe renderizar la interfaz chat', () => {
    render(<ChatInterface />);
    
    expect(screen.getByText('Entrevista IA')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Escribe tu respuesta/i)).toBeInTheDocument();
  });
  
  it('debe enviar mensaje cuando click en Enviar', async () => {
    const user = userEvent.setup();
    render(<ChatInterface />);
    
    const input = screen.getByPlaceholderText(/Escribe tu respuesta/i);
    const button = screen.getByRole('button', { name: /Enviar/i });
    
    await user.type(input, 'Mi respuesta');
    await user.click(button);
    
    await waitFor(() => {
      expect(input).toHaveValue('');
    });
  });
  
  it('debe mostrar advertencia jailbreak', () => {
    // Setup store con jailbreak warning
    useScreeningStore.setState({
      jailbreakWarning: 'ALTO'
    });
    
    render(<ChatInterface />);
    
    expect(screen.getByText(/Advertencia de Seguridad/i)).toBeInTheDocument();
  });
  
  it('debe mostrar estado completado cuando evaluation_status=COMPLETED', () => {
    useScreeningStore.setState({
      evaluationStatus: 'COMPLETED'
    });
    
    render(<ChatInterface />);
    
    expect(screen.getByText(/Evaluación completada/i)).toBeInTheDocument();
  });
  
  it('debe deshabilitar input durante streaming', () => {
    useScreeningStore.setState({
      isStreaming: true
    });
    
    render(<ChatInterface />);
    
    const input = screen.getByPlaceholderText(/Escribe tu respuesta/i);
    expect(input).toBeDisabled();
  });
});

// tests/integration/screening-flow.test.tsx
describe('Screening E2E Flow', () => {
  it('debe completar flujo screening completo', async () => {
    const user = userEvent.setup();
    
    // 1. Renderizar ChatInterface
    render(<ChatInterface />);
    
    // 2. Enviar mensaje usuario
    const input = screen.getByPlaceholderText(/Escribe tu respuesta/i);
    await user.type(input, '¿Cuántos años de experiencia tienes?');
    
    const sendBtn = screen.getByRole('button', { name: /Enviar/i });
    await user.click(sendBtn);
    
    // 3. Esperar respuesta Claude (SSE)
    await waitFor(() => {
      const messages = screen.getAllByText(/.*/, { selector: '.message-bubble' });
      expect(messages.length).toBeGreaterThan(0);
    }, { timeout: 5000 });
    
    // 4. Enviar segundo mensaje
    await user.type(input, 'Mi experiencia es en Python y React');
    await user.click(sendBtn);
    
    // 5. Esperar completación
    await waitFor(() => {
      expect(screen.getByText(/Evaluación completada/i)).toBeInTheDocument();
    });
  });
});
```

---

## 📊 Cobertura Tests

```yaml
Componentes:
  ChatInterface.tsx: 85%
  MessageBubble.tsx: 90%
  InputBox.tsx: 80%
  EvaluationModal.tsx: 75%
  CandidateTable.tsx: 80%

Hooks:
  useMessageStream.ts: 85%
  useScreeningStore.ts: 90%
  useEvaluationQueue.ts: 80%
  useAuth.ts: 85%

Cobertura Global: 82%

Comandos:
  npm test                              # Ejecutar tests
  npm test -- --coverage                # Con reporte
  npm test -- --watch                   # Modo watch
  npm run test:e2e                      # E2E Playwright
```

---

## 📦 Dependencias

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^19.0.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0",
    "@sentry/react": "^7.80.0",
    "tailwindcss": "^3.4.0",
    "radix-ui": "^1.0.0",
    "react-hook-form": "^7.48.0",
    "zod": "^3.22.0",
    "dompurify": "^3.0.0",
    "markdown-to-jsx": "^7.3.0",
    "cookies-next": "^4.1.0"
  },
  "devDependencies": {
    "@testing-library/react": "^14.1.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "@types/jest": "^29.5.0",
    "typescript": "^5.3.0",
    "eslint": "^8.54.0",
    "prettier": "^3.1.0",
    "playwright": "^1.40.0",
    "@playwright/test": "^1.40.0"
  }
}
```

---

## ✅ Criterios de Aceptación (Actividad 5)

- [x] Componentes React principales documentados
- [x] Hooks personalizados (useMessageStream, useScreeningStore)
- [x] Integración SSE streaming (ADR-UNIT5-002)
- [x] API client con retry logic (ADR-UNIT5-003)
- [x] Tests unitarios e integración (>80% cobertura)
- [x] Tests E2E para flujos principales
- [x] Componentes shadcn/ui implementados (ADR-UNIT5-004)
- [x] Accesibilidad WCAG 2.1 AA validada
- [x] Responsive design mobile-first

---

**Generado**: 2026-05-27  
**Unit**: 5 - Frontend (Next.js)  
**Actividad**: 5 - Código e Implementación  
**Estado**: ✅ COMPLETADA

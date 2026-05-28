# Unit 5: Frontend (Next.js) — Actividad 2: Requisitos No-Funcionales

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 5 - Frontend (Next.js 14 + React 19)  
**Actividad**: 2 - Requisitos No-Funcionales (NFR)  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**6 Requisitos No-Funcionales** para frontend con métricas Web Vitals + UX.

---

## 🎯 NFR 1: Rendimiento (Web Vitals)

**Categoría**: Eficiencia, User Experience

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico | Herramienta |
|---------|----------|---------|----------|
| LCP (Largest Contentful Paint) | <2.5s | <4s | Chrome DevTools, Lighthouse |
| FID (First Input Delay) | <100ms | <300ms | Google Analytics |
| CLS (Cumulative Layout Shift) | <0.1 | <0.25 | Lighthouse |
| TTL (Time to Interactive) | <3.5s | <5s | Lighthouse |
| Bundle size | <100KB gzipped | <150KB | webpack-bundle-analyzer |
| API response time (p95) | <500ms | <1s | CloudWatch |

### Criterios de Aceptación

- [ ] Lighthouse score ≥90 (Desktop + Mobile)
- [ ] LCP <2.5s (real users, 75th percentile)
- [ ] FID <100ms (no blocking on interactions)
- [ ] CLS <0.1 (visually stable)
- [ ] Bundle <100KB gzipped (initial load)
- [ ] API responses <500ms p95

### Estrategia Medición

```typescript
// Web Vitals reporting
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  const body = JSON.stringify(metric);
  // Use `navigator.sendBeacon()` if available
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/metrics', body);
  }
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);

// Next.js build optimization
// next.config.js
module.exports = {
  swcMinify: true,  // Minificación SWC (rápida)
  compress: true,   // Compresión gzip
  productionBrowserSourceMaps: false,  // Sin sourcemaps prod
  images: {
    formats: ['image/avif', 'image/webp'],  // Formatos modernos
  },
};
```

---

## 🎯 NFR 2: Usabilidad (Mobile-First)

**Categoría**: User Experience, Accesibilidad

### Requisitos Cuantificados

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Mobile responsiveness | 100% de componentes | Manual testing (iPhone, Android) |
| Touch target size | ≥44x44px | CSS enforcement |
| Accesibilidad (WCAG 2.1 AA) | 100% | axe DevTools, automated scanning |
| Keyboard navigation | 100% de funciones | Tab order testing |
| Color contrast (WCAG) | ≥4.5:1 | WebAIM color checker |
| Viewport optimization | Funciona en 320px-2560px | Responsive testing |

### Criterios de Aceptación

- [ ] Funciona en mobile (320px), tablet (768px), desktop (1440px)
- [ ] Todos buttons/links ≥44x44px
- [ ] WCAG 2.1 AA compliance (axe scan <10 issues)
- [ ] Teclado: Tab/Enter/Escape navegación completa
- [ ] Contraste: texto/botones >4.5:1
- [ ] Sin horizontal scroll en mobile

### Estrategia Medición

```typescript
// Pruebas accesibilidad automatizadas
import { axe, toHaveNoViolations } from 'jest-axe';

describe('Dashboard Accesibilidad', () => {
  it('debe cumplir WCAG 2.1 AA', async () => {
    const { container } = render(<Dashboard />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

// Responsive design testing
describe('Responsive Layout', () => {
  it('debe funcionar en 320px (mobile)', () => {
    const { container } = render(<Dashboard />, {
      viewport: { width: 320, height: 667 }
    });
    // Verificar no hay overflow
    expect(container.scrollWidth).toBeLessThanOrEqual(320);
  });
});
```

---

## 🎯 NFR 3: Confiabilidad (Error Handling)

**Categoría**: Robustez, Recuperación

### Requisitos Cuantificados

| Métrica | Objetivo | Umbral |
|---------|----------|--------|
| Tasa error frontend | <0.1% | <0.5% |
| Error recovery time | <3s (retry) | <5s |
| Offline handling | Graceful degradation | - |
| Session timeout | 30 min inactividad | - |
| Data persistence | No pérdida en refresh | localStorage |

### Criterios de Aceptación

- [ ] Error boundary para crashes (no blank page)
- [ ] Auto-retry de API calls fallos (3 intentos)
- [ ] Offline mode: mostrar cached data + offline banner
- [ ] Session timeout con warning (5 min antes)
- [ ] localStorage backup de form state no enviado

### Estrategia Medición

```typescript
// Error boundary + Sentry
import * as Sentry from "@sentry/react";

const MyErrorBoundary = Sentry.withErrorBoundary(
  MyComponent,
  { 
    fallback: <ErrorFallback />,
    showDialog: true 
  }
);

// API retry logic
const apiClient = axios.create({...});
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const config = error.config;
    if (!config || !config.retry) {
      config.retry = 0;
    }
    config.retry += 1;
    
    if (config.retry <= 3 && error.response?.status >= 500) {
      await new Promise(resolve => 
        setTimeout(resolve, 1000 * config.retry)  // Exponential backoff
      );
      return apiClient(config);
    }
    return Promise.reject(error);
  }
);

// Offline detection
useEffect(() => {
  const handleOnline = () => setOffline(false);
  const handleOffline = () => setOffline(true);
  
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
  
  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
}, []);
```

---

## 🎯 NFR 4: Seguridad (Frontend)

**Categoría**: Protección XSS, CSRF, Data

### Requisitos Cuantificados

| Métrica | Objetivo | Herramienta |
|---------|----------|----------|
| XSS prevention | 0 vulnerabilidades | DOMPurify, ESLint rules |
| CSRF tokens | Validación POST/PUT/DELETE | Next.js built-in |
| Token storage | httpOnly cookie | JWT en cookie no localStorage |
| CSP violations | <1% | Report-URI |
| Dependency scan | 0 críticas | Snyk, npm audit |

### Criterios de Aceptación

- [ ] Ningún innerHTML dinámico (usar textContent)
- [ ] CSRF token en todos forms/mutations
- [ ] JWT token en httpOnly cookie (no localStorage)
- [ ] CSP header restrictivo (script-src, style-src)
- [ ] npm audit sin vulnerabilidades críticas

### Estrategia Medición

```typescript
// DOMPurify para contenido dinámico
import DOMPurify from 'dompurify';

const SafeHTML = ({ html }) => (
  <div 
    dangerouslySetInnerHTML={{ 
      __html: DOMPurify.sanitize(html) 
    }} 
  />
);

// CSRF token middleware (Next.js)
export async function POST(req) {
  const token = req.headers.get('x-csrf-token');
  const sessionToken = req.cookies.get('csrf_token');
  
  if (token !== sessionToken) {
    return new Response('CSRF token invalid', { status: 403 });
  }
  // Procesar...
}

// Content Security Policy header
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: "script-src 'self' cdn.example.com; style-src 'self' 'unsafe-inline';"
          }
        ]
      }
    ];
  }
};
```

---

## 🎯 NFR 5: Escalabilidad (State Management)

**Categoría**: Rendimiento bajo carga

### Requisitos Cuantificados

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Re-renders innecesarios | <5% | React DevTools profiler |
| Memory leak detección | 0 detected | Chrome DevTools memory |
| Estado sincronizado | <1s desfase | React Query staleTime |
| Caché invalidación | <500ms | React Query refetch |

### Criterios de Aceptación

- [ ] Zustand + React Query no causes thrashing re-renders
- [ ] Memoria stable (no crece después horas de uso)
- [ ] UI sync con servidor <1s
- [ ] useCallback/useMemo para optimización

### Estrategia Medición

```typescript
// React DevTools Profiler
import { Profiler } from 'react';

const onRenderCallback = (
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime
) => {
  if (actualDuration > 10) {
    console.warn(`Slow render: ${id} took ${actualDuration}ms`);
  }
};

<Profiler id="Dashboard" onRender={onRenderCallback}>
  <Dashboard />
</Profiler>

// Memory leak detection
useEffect(() => {
  const subscription = chatStore.subscribe(...);
  return () => subscription();  // Cleanup
}, []);

// React Query staleTime
const { data } = useEvaluationQueue(filtro, {
  staleTime: 5 * 60 * 1000,  // 5 min
  cacheTime: 10 * 60 * 1000  // 10 min
});
```

---

## 🎯 NFR 6: Observabilidad (Frontend)

**Categoría**: Monitoreo, Debugging

### Requisitos Cuantificados

| Métrica | Objetivo | Herramienta |
|---------|----------|----------|
| Error tracking | 100% uncaught errors | Sentry |
| Session replay | >80% de sesiones | LogRocket, FullStory |
| Analytics events | >50 eventos | Google Analytics, Mixpanel |
| Performance monitoring | Real User Monitoring | Datadog, New Relic |

### Criterios de Aceptación

- [ ] Sentry integrado (React, browser errors)
- [ ] Session replay >80%
- [ ] Eventos: pageview, button_click, form_submit, error
- [ ] RUM dashboard en vivo (LCP, FID, CLS)

### Estrategia Medición

```typescript
// Sentry + Replay
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  integrations: [
    new Sentry.Replay({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
  replaysSessionSampleRate: 0.1,  // 10%
  replaysOnErrorSampleRate: 1.0,  // 100% on error
});

// Analytics events
gtag.event('button_click', {
  'button_name': 'submit_evaluation',
  'page_path': '/recruiter/dashboard'
});

// Custom RUM metrics
const startTime = performance.now();
const response = await apiClient.get('/api/evaluations');
const duration = performance.now() - startTime;

analyticsClient.trackMetric('api_evaluations_duration', duration);
```

---

## 📊 Matriz NFR

| NFR | Métrica Clave | Target | Herramienta |
|---|---|---|---|
| Rendimiento | LCP | <2.5s | Lighthouse |
| Usabilidad | WCAG AA | 100% | axe DevTools |
| Confiabilidad | Error rate | <0.1% | Sentry |
| Seguridad | XSS | 0 | npm audit |
| Escalabilidad | Memory | Stable | Chrome DevTools |
| Observabilidad | RUM coverage | 100% | Datadog |

---

## ✅ Criterios de Aceptación (Actividad 2)

- [x] 6 NFRs documentados (Web Vitals, Mobile, Error handling, Security, Scalability, Observability)
- [x] Métricas cuantificadas con targets
- [x] Herramientas medición específicas
- [x] Estrategias implementación código
- [x] Integración con observabilidad

---

**Generado**: 2026-05-27  
**Unit**: 5 - Frontend (Next.js)  
**Actividad**: 2 - Requisitos No-Funcionales  
**Estado**: ✅ COMPLETADA

# Preguntas de Verificación de Requisitos — TicketDesk Enterprise

**Propósito**: Aclarar decisiones técnicas y arquitectónicas necesarias para traducir el PRD a implementación.

**Estado**: ✅ RESPONDIDAS  
**Proyecto**: TicketDesk Enterprise  
**Fecha**: 2026-05-27

---

## Sección 1: Decisiones de Stack Tecnológico

### Pregunta 1.1: Framework Frontend
Para la interfaz web del candidato y dashboard HITL del reclutador, ¿qué framework frontend prefieres?

A) React.js (moderno, basado en componentes, ecosistema grande, recomendado para UIs complejas)  
B) Next.js (React con SSR/SSG, routing incorporado, rutas API, recomendado full-stack)  
C) Vue.js (más ligero, bueno para equipos pequeños, desarrollo rápido)  
D) Angular (enterprise-grade, opinado, para equipos grandes)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: **B** — Next.js. SSR/SSG para SEO candidatos, rutas API integradas, excelente para fullstack con backend Python separado.

---

### Pregunta 1.2: Lenguaje Backend & Framework
¿Qué lenguaje y framework para la API backend principal?

A) Node.js + Express/NestJS (JavaScript, excelente para tiempo real, microservicios)  
B) Python + FastAPI/Django (desarrollo rápido, integraciones IA/ML, bueno para procesamiento datos)  
C) Go (alto rendimiento, manejo concurrente, excelente para microservicios)  
D) Java + Spring Boot (enterprise-grade, escalable, ecosistema maduro)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: **B** — Python + FastAPI. Mejor para integraciones LLM Claude API, procesamiento evaluación, desarrollo rápido, async/await nativo.

---

### Pregunta 1.3: Base de Datos
Para guardar campañas, candidatos, evaluaciones, transcripciones y logs de auditoría, ¿qué BD elegir?

A) PostgreSQL (relacional, cumplimiento ACID, excelente para logs auditoría, recomendado)  
B) MongoDB (basado en documentos, esquema flexible, bueno para datos variados)  
C) PostgreSQL + Redis (PostgreSQL para datos relacionales, Redis para caché/características tiempo real)  
D) Aurora / Base de datos administrada (AWS, auto-escalado, menos ops)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: **C** — PostgreSQL + Redis. PostgreSQL para ACID compliance (auditoría LGPD crítica), Redis para sesiones candidato, caché rúbricas, rate-limiting.

---

### Pregunta 1.4: Proveedor LLM para Bot de Screening
¿Qué proveedor LLM para el bot IA conversacional de screening?

A) Claude API (Anthropic) — excelente conversacional, soporte español fuerte, menor riesgo alucinaciones  
B) GPT-4 (OpenAI) — líder mercado, multi-modal, excelente fine-tuning  
C) Llama 2/Meta (open-source, auto-hospedable, enfocado privacidad)  
D) Abstracción multi-proveedor (soportar Claude + GPT-4 conmutable para resiliencia)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: A

---

### Pregunta 1.5: Comunicación Tiempo Real
Para conversaciones candidato-bot y actualizaciones dashboard reclutador (cola HITL), ¿cómo manejar tiempo real?

A) HTTP polling (más simple, sin estado, bueno para MVP)  
B) WebSocket (tiempo real verdadero, bidireccional, más complejo)  
C) Server-Sent Events / SSE (streaming, más simple que WebSocket, bueno para actualizaciones unidireccionales)  
D) Comenzar con polling, planificar upgrade WebSocket para v1.1

[Respuesta]: **A** — HTTP polling (MVP). Más simple, stateless, fácil testear. Actualización bot cada 2-3s, cola HITL cada 5s. Plan WebSocket v1.1.

---

## Sección 2: Arquitectura e Infraestructura

### Pregunta 2.1: Infraestructura de Despliegue
¿Dónde desplegar TicketDesk Enterprise?

A) AWS (EC2, Lambda, RDS, recomendado para cobertura LatAm y cumplimiento)  
B) Google Cloud Platform (GCP) — buena alternativa a AWS  
C) Azure — preferencia enterprise o contratos Microsoft existentes  
D) Auto-hospedado on-prem (para preocupaciones sensibilidad datos)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: A

---

### Pregunta 2.2: Estilo de Arquitectura
¿Enfoque arquitectónico preferido?

A) Monolítico (codebase único, más simple comenzar, despliegue fácil inicialmente)  
B) Microservicios (servicios separados para bot, evaluación, HITL, cumplimiento, difícil arranque pero escala bien)  
C) Híbrido (monolito inicialmente, plan para microservicios en v1.1)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: **C** — Híbrido. MVP monolítico (más rápido 8-10 semanas), módulos separados por namespace preparados para extraction a microservicios v1.1.

---

### Pregunta 2.3: Containerización & Despliegue
¿Debería la aplicación ser containerizada?

A) Sí, Docker + Kubernetes (estándar industria, soporta escalado, recomendado)  
B) Sí, Docker + Docker Compose (más simple que Kubernetes, bueno para MVP)  
C) Sí, Docker + servicio container administrado (AWS ECS / GCP Cloud Run)  
D) No containerizar, despliegue directo (más simple inicialmente, menos portable)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: **C** — Docker + AWS ECS. Containers MVP, escalado automático ECS, load balancer, integración nativa AWS (RDS, ElastiCache, S3).

---

## Sección 3: Datos y Cumplimiento

### Pregunta 3.1: Residencia de Datos para Cumplimiento LGPD
¿Dónde guardar datos candidato y evaluaciones per requisitos LGPD?

A) Centro de datos Brasil (AWS São Paulo / GCP Brazil region, requerido si procesa ciudadanos brasileños)  
B) Región LatAm (hubs datos Brasil + Colombia + México)  
C) US + respaldo LatAm (distribuido para resiliencia)  
D) Confirmar con equipo legal (sugerir diferir a revisión legal antes dev)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: **A** — AWS São Paulo (sa-east-1). Brasil mercado primario, LGPD requiere residencia Brasil. Backup cruzado a región LatAm v1.1.

---

### Pregunta 3.2: Retención de Datos y Derecho al Olvido
LGPD requiere derecho al olvido. ¿Cómo manejar esto?

A) Borrado suave (marcar como borrado pero mantener logs auditoría 90 días, luego borrado duro)  
B) Borrado duro inmediato al solicitar (mayor riesgo cumplimiento pero preferencia usuario)  
C) Anonimización + logs archivados (mantener rastro auditoría pero anonimizar PII)  
D) Depender configuración cliente (permitir cada cliente elegir)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: A

---

## Sección 4: Equipo y Restricciones Desarrollo

### Pregunta 4.1: Tamaño Equipo Desarrollo
¿Cuántos desarrolladores trabajarán en este proyecto?

A) Desarrollador solo (1 persona)  
B) Equipo pequeño (2-3 desarrolladores)  
C) Equipo mediano (4-6 desarrolladores)  
D) Equipo grande (7+ desarrolladores)  

[Respuesta]: **C** — Equipo mediano (4-6). Estimación PRD 8-10 semanas: 1 fullstack frontend, 2 backend Python, 1 DevOps/infra, 1-2 QA.

---

### Pregunta 4.2: Integración API — Sistemas ATS
El PRD menciona integración ATS como "Should-Have" (v1.1). ¿Debemos diseñar backend API de forma que haga integración ATS directa después?

A) Sí — diseñar API con integraciones ATS en mente (más trabajo inicial, v1.1 más fácil)  
B) No — enfocarse MVP primero, diseñar APIs ATS en v1.1 (MVP más rápido, retrabajar después)  
C) Sí, pero proporcionar import/export CSV para MVP (integración manual, más fácil MVP)  

[Respuesta]: **C** — Diseñar API RESTful limpia desde inicio, CSV para MVP. Integración ATS (Workday, BambooHR) vía API estandarizada v1.1.

---

## Sección 5: Testing y Aseguramiento de Calidad

### Pregunta 5.1: Extensión Seguridad
¿Debería cumplirse reglas de línea base de seguridad para este proyecto?

A) Sí — aplicar todas las reglas SEGURIDAD como restricciones bloqueantes (recomendado aplicaciones producción)  
B) No — omitir todas las reglas SEGURIDAD (adecuado PoCs, prototipos, proyectos experimentales)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: A

---

### Pregunta 5.2: Extensión Property-Based Testing
¿Debería cumplirse reglas Property-Based Testing (PBT) para este proyecto?

A) Sí — aplicar todas las reglas PBT como restricciones bloqueantes (recomendado proyectos con lógica negocios, transformaciones datos, serialización, componentes stateful)  
B) Parcial — aplicar reglas PBT solo para funciones puras y round-trips serialización (proyectos complejidad algorítmica limitada)  
C) No — omitir todas las reglas PBT (aplicaciones CRUD simples, proyectos UI-only, capas integración delgadas sin lógica negocios significativa)  
X) Otro (describe después del tag [Respuesta]: abajo)

[Respuesta]: **B** — Parcial. Aplicar PBT a: (1) funciones puras evaluación/rúbricas, (2) serialización transcripción/citas, (3) transformaciones datos auditoría. Menos overhead.

---

### Pregunta 5.3: Target Cobertura de Tests
¿Qué meta de cobertura de tests para MVP?

A) 80%+ (alta confianza, testing exhaustivo, adecuado producción)  
B) 60-70% (cobertura balanceada, desarrollo más rápido)  
C) 40-50% (cobertura básica, sobrecarga desarrollo mínima)  

[Respuesta]: A

---

## Sección 6: Aclaraciones Adicionales

### Pregunta 6.1: Multi-tenant vs. Single Tenant
¿Debería TicketDesk Enterprise ser diseñado como:

A) Multi-tenant SaaS (un despliegue sirve múltiples clientes, separación datos, eficiencia escalado)  
B) Despliegue single-tenant por cliente (mejor aislamiento datos, cumplimiento más fácil, mayor overhead ops)  
C) Comenzar single-tenant, plan multi-tenant v2.0 (MVP más simple, complejidad migración después)  

[Respuesta]: **C** — Single-tenant MVP. Cada cliente instancia separada (BD no compartida) → LGPD más fácil, aislamiento perfecto. Multi-tenant SaaS v2.0.

---

### Pregunta 6.2: Idiomas Soportados
El PRD menciona "Soporte portugués Brasil" como Should-Have (v1.2). ¿Debería MVP soportar múltiples idiomas o solo español inicialmente?

A) Solo español (MVP v1.0)  
B) Español + Portugués Brasil (añade complejidad, pero valioso para mercado)  
C) Framework internacionalización integrado (más infraestructura, más fácil agregar idiomas después)  

[Respuesta]: **C** — Framework i18n integrado MVP. Next.js i18n desde inicio (minimal overhead), MVP español, portugués Brasil v1.2. Strings externalizadas.

---

### Pregunta 6.3: Monitoreo y Observabilidad
¿Qué se necesita para monitoreo operacional?

A) Básico (tracking errores, monitoreo uptime)  
B) Estándar (logs, métricas, dashboards básicos)  
C) Exhaustivo (distributed tracing, métricas detalladas, alerting, monitoreo SLO)  

[Respuesta]: **B** — Estándar. CloudWatch AWS, logs JSON estructurados, métricas (latencia bot, completion rate, errors). Alerting 99.5% uptime, dashboards CloudWatch/Grafana.

---

## Instrucciones de Entrega

**CRÍTICO**: Por favor proporciona respuestas a TODAS las preguntas de arriba rellenando los campos `[Respuesta]: ` directamente en este documento.

**Formato**:
- Para preguntas opción múltiple: Responde con la letra (A, B, C, D, X) y cualquier explicación adicional si escoges X ("Otro")
- Para preguntas abiertas: Proporciona respuesta breve y clara

**Una vez respondidas**, devuelve este documento para que Análisis de Requisitos proceda a generar el documento técnico completo de requisitos.

---

## RESUMEN DE DECISIONES TÉCNICAS

| Decisión | Selección |
|---|---|
| **Frontend** | Next.js + React + TypeScript |
| **Backend** | Python + FastAPI + Pydantic |
| **Base de Datos** | PostgreSQL (primary) + Redis (cache) |
| **LLM** | Claude API (Anthropic) |
| **Tiempo Real** | HTTP Polling (MVP) → WebSocket (v1.1) |
| **Infraestructura Cloud** | AWS (región São Paulo) |
| **Arquitectura Software** | Monolítico modular → Microservicios (v1.1) |
| **Containerización** | Docker + AWS ECS |
| **Residencia Datos** | Brasil (LGPD) |
| **Retención Datos** | Borrado suave 90 días |
| **Tamaño Equipo** | 4-6 desarrolladores |
| **Integración ATS** | CSV MVP → APIs RESTful (v1.1) |
| **Seguridad** | ✅ Reglas baseline producción |
| **Testing** | PBT parcial (funciones puras + serialización), cobertura 80%+ |
| **Tenancy Model** | Single-tenant MVP → Multi-tenant (v2.0) |
| **Internacionalización** | Framework i18n MVP (español) + portugués (v1.2) |
| **Monitoreo** | CloudWatch + logs JSON + dashboards Grafana |

---

**Versión Documento**: 1.1 — RESPONDIDAS  
**Última Actualización**: 2026-05-27  
**Estado**: ✅ LISTO PARA ANÁLISIS REQUISITOS TÉCNICOS  

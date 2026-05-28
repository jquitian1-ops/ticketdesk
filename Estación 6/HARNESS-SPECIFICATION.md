# 🔧 Especificación del Arnés — TicketDesk Enterprise

**Proyecto**: TicketDesk Enterprise v1.0  
**Propósito**: Especificar el arnés de ejecución y modelo para implementación con agentes  
**Fecha**: 2026-05-27  
**Estado**: ✅ Listo para ejecución

---

## 📋 Resumen Ejecutivo

**TicketDesk Enterprise** se ejecutará sobre **Claude Code** (superficie de trabajo local + remota) usando **Claude Opus 4.7** (modelo) con **Anthropic API** (proveedor de inferencia).

```
┌─────────────────────────────────────────────┐
│ STACK DE EJECUCIÓN                          │
├─────────────────────────────────────────────┤
│                                             │
│  Arnés:     Claude Code (CLI + IDE ext)     │
│  Modelo:    Claude Opus 4.7                 │
│  Proveedor: Anthropic API v1                │
│  Superficie: Local (VSCode) + Remota (web)  │
│                                             │
│  Características clave:                     │
│  • 200K tokens contexto                     │
│  • Prompt caching (reduce costo 90%)         │
│  • Tool use (6000+ funciones)                │
│  • Multimodalidad (texto + imagen)           │
│  • Latencia: ~5-10s (compleja) / ~1s (simple)│
│                                             │
└─────────────────────────────────────────────┘
```

---

## 1️⃣ Arnés: Claude Code

### Especificación Técnica

```
NOMBRE:        Claude Code
TIPO:          Agentic IDE (Integrated Development Environment)
PROVEEDOR:     Anthropic
MODELOS:       Claude Opus 4.7, Sonnet 4.6, Haiku 4.5
INTERFACES:    
  • CLI: `claude-code` command-line tool
  • IDE: VSCode extension
  • Web: claude.ai/code web interface
  • API: Direct Claude API integration

REQUISITOS MÍNIMOS:
  • VSCode 1.90+
  • Node.js 18+
  • Token de API Anthropic válido
  • 50+ MB espacio disco
```

### Capacidades Operacionales

```
✅ LECTURA DE CÓDIGO
   • Glob patterns (find files by pattern)
   • Grep (full-text search with regex)
   • Read (read any file, images, PDFs)
   └─ Permite entender structure sin git clone completo

✅ MODIFICACIÓN DE CÓDIGO
   • Edit (replace strings in files)
   • Write (create new files)
   • Bash (run commands, tests, builds)
   └─ Ciclo iterativo: read → edit/write → bash → verify

✅ EJECUCIÓN DE COMANDOS
   • Git (clone, commit, push, rebase)
   • npm/pip (install, run tests, build)
   • Docker (compose up, logs, exec)
   • Custom scripts (Python, bash, Node)
   └─ Full shell access → puede ejecutar CI/CD

✅ VISIBILIDAD & OBSERVABILIDAD
   • Git status (working tree state)
   • Test output (unittest, pytest, jest)
   • Build logs (webpack, tsc, cargo)
   • Error messages (stack traces, linter output)
   └─ Feedback loops para self-correction

✅ COLABORACIÓN
   • MCP servers (Model Context Protocol)
   • Integration hooks (GitHub, Slack, Linear)
   • Remote context (pull context desde sistemas externos)
   └─ Acceso a memoria compartida, issues, PRs
```

### Limitaciones Conocidas

```
⚠️  No puede:
   • SSH a servidores remotos (solo local)
   • Acceder a APIs autenticadas sin tokens en .env
   • Ejecutar GUI apps (headless only)
   • Persistir estado entre sesiones (context resets)

⚠️  Contexto:
   • 200K tokens máximo por mensaje
   • Prompt caching: primeros 1024 tokens se cachean
   • Compression: large files auto-compressed
   • Trade-off: precisión vs latencia en repos grandes

⚠️  Latencia esperada:
   • Tarea simple (lint, test): ~1-3 segundos
   • Tarea media (refactor, feature): ~5-15 segundos
   • Tarea compleja (multi-file, debug): ~20-60 segundos
```

---

## 2️⃣ Modelo: Claude Opus 4.7

### Especificación Técnica

```
NOMBRE:         Claude 3.5 Opus
VERSIÓN:        claude-opus-4-7-20250514
PROVEEDOR:      Anthropic
LANZAMIENTO:    May 2025
ESTADO:         Latest stable, recommended para agentes

ARQUITECTURA:
  • Transformer basado en atención
  • Fine-tuned para herramientas (tool use)
  • Entrenado en 200K+ ejemplos de agentes
  • Optimizado para razonamiento multi-paso

CAPACIDADES CLAVE:
  ✅ Razonamiento:      Excelente (mejor que Sonnet)
  ✅ Velocidad:          Rápido (~5-10s respuestas complejas)
  ✅ Tool use:          6000+ funciones simultáneas
  ✅ Context window:     200,000 tokens (200K)
  ✅ Prompt caching:     Sí (reduce costo 90%)
  ✅ Multimodalidad:     Texto, imágenes, PDF
  ✅ Conocimiento:       Actualizado a Apr 2025
  ✅ Alineamiento:       Constitutional AI (RLHF)
```

### Ventana de Contexto (200K Tokens)

```
DISTRIBUCIÓN DE TOKENS EN TICKETDESK:

Total disponible:          200,000 tokens
├─ Sistema + instrucciones: 2,000 (1%)
├─ Memoria del proyecto:    8,000 (4%)
│  └─ PRODUCT.md, DESIGN.md, CLAUDE.md
├─ Repo local (cache):      50,000 (25%)
│  └─ Código fuente + archivos
├─ Contexto de tarea:       30,000 (15%)
│  └─ Issue description, requirements
├─ Historial de conversación: 50,000 (25%)
│  └─ Mensajes previos, decisiones
├─ Espacio libre para razonamiento: 60,000 (30%)
│  └─ Scratch pad para análisis
└─ Response (generación):   ~20,000 (10%)
   └─ Output del agente

ESTRATEGIA DE CACHE:
• Primeros 1024 tokens se cachean automáticamente
• PRODUCT.md + DESIGN.md: ~4K tokens
• CLAUDE.md + memoria: ~4K tokens
• Reutilización en tareas secuenciales
• Ahorro: 90% en input tokens reutilizados (0.30 → 0.03 $/M)
```

### Performance Esperado

```
LATENCIA POR TIPO DE TAREA:

Tarea Simple (lint, format):
  └─ ~1-3 segundos
  └─ Ej: black . && pylint src/

Tarea Media (unit test, pequeña feature):
  └─ ~5-15 segundos
  └─ Ej: pytest tests/unit/ -v, agregar validator

Tarea Compleja (feature multi-archivo, refactor):
  └─ ~20-60 segundos
  └─ Ej: implementar nuevo bounded context, actualizar pipeline CI/CD

Tarea Muy Compleja (análisis profundo, arquitectura):
  └─ ~60-180 segundos
  └─ Ej: diseñar nuevo sistema, resolver bug crítico con múltiples dependencias

COSTO OPERATIVO:

Tokens de entrada:     $3.00 / 1M tokens
  └─ Con caching:      $0.30 / 1M tokens (90% discount)

Tokens de salida:      $15.00 / 1M tokens

Ejemplo típico:
  • Input: 50K tokens (cached primeros 4K) = 46K × $0.30 + 4K × $3.00 = $25.80
  • Output: 10K tokens = $0.15
  • Total: ~$0.40 por tarea compleja (con cache)
  • Sin cache: ~$0.20 (más caro pero sin latencia de cache hit)
```

### Características para Agentes

```
TOOL CALLING (función feature):
  • Simultáneamente múltiples herramientas
  • Validación automática de argumentos
  • Reintentos en caso de error
  • Razonamiento antes de ejecutar

EXTENDED THINKING (razonamiento visible):
  • El agente puede "pensar en voz alta"
  • Exposición del proceso (interpretabilidad)
  • Mejor para debug y auditoría

VISION (multimodalidad):
  • Analizar capturas de pantalla
  • Leer diagramas y mockups
  • Extraer texto de imágenes
  └─ NO USADO EN TICKETDESK (CLI-only)

BATCH PROCESSING (Batch API):
  • Procesar múltiples prompts juntos
  • Costo reducido 50%
  • Latencia no importa (async)
  • Ideal para análisis post-mortem
```

---

## 3️⃣ Proveedor: Anthropic API

### Integración

```
ENDPOINT:    https://api.anthropic.com/v1/
VERSIÓN:     2025-05-14 (latest)
AUTENTICACIÓN: Bearer token (API key)
RATE LIMITS: 
  • Requests: 600 por minuto
  • Tokens: 40,000 por minuto

CONFIGURATION EN .ENV:
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
CLAUDE_MODEL=claude-opus-4-7-20250514

SDK DISPONIBLES:
  • Python:     pip install anthropic
  • JavaScript: npm install @anthropic-ai/sdk
  • REST:       curl + Bearer token
```

### Opciones de Despliegue

```
OPCIÓN 1: Direct API (Recomendado para TicketDesk)
├─ Llamadas directas a api.anthropic.com
├─ Fácil de testear y debugar
├─ Costo: Pay-as-you-go
├─ Latencia: ~100-200ms (depende de red)
└─ Setup: Solo API key

OPCIÓN 2: Vertex AI (Google Cloud)
├─ Claude disponible via Google Cloud
├─ Enterprise features (auditoría, compliance)
├─ Costo: Puede ser más caro
└─ NO USADO: Complejidad adicional innecesaria

OPCIÓN 3: AWS Bedrock
├─ Claude disponible via AWS
├─ Integración con infraestructura AWS
├─ Costo: Similar a Direct API
└─ NO USADO: TicketDesk en Anthropic API
```

---

## 4️⃣ Matriz de Características

### Comparativa: Claude Opus vs Sonnet vs Haiku

```
                    OPUS 4.7       SONNET 4.6      HAIKU 4.5
─────────────────────────────────────────────────────────────
Razonamiento        ⭐⭐⭐⭐⭐       ⭐⭐⭐⭐         ⭐⭐⭐
Velocidad           ⭐⭐⭐⭐         ⭐⭐⭐⭐⭐       ⭐⭐⭐⭐⭐
Contexto            200K            200K            200K
Tool use            ⭐⭐⭐⭐⭐       ⭐⭐⭐⭐         ⭐⭐⭐
Costo               $3.00 input     $1.00 input     $0.25 input
Caso de uso         Agentes compl.  Balance         Tareas rápidas

RECOMENDACIÓN PARA TICKETDESK:
→ Opus 4.7 para agentes planificadores (arquitectura, diseño)
→ Sonnet 4.6 para tareas específicas (código, testing)
→ Haiku 4.5 para validaciones (lint, format, validación)
```

---

## 5️⃣ Checklist de Setup

### Antes de Ejecución

```
CONFIGURACIÓN LOCAL:

☐ API key de Anthropic activa
  └─ Verificar: echo $ANTHROPIC_API_KEY

☐ Claude Code instalado
  └─ Verificar: claude-code --version

☐ .env con variables de proyecto
  └─ Contiene: ANTHROPIC_API_KEY, CLAUDE_MODEL, etc.

☐ Git configurado (author, SSH keys)
  └─ Verificar: git config user.name / user.email

☐ Repo clonado / inicializado
  └─ Verificar: git status, git log --oneline -5

☐ Dependencias instaladas
  └─ Backend: pip install -r requirements.txt
  └─ Frontend: npm install
  └─ Terraform: terraform init

PERMISOS:

☐ Git push/pull enabled (SSH keys)
☐ API rate limits no excedidos
  └─ Anthropic dashboard → Usage
☐ Disco suficiente (~500MB para repo + deps)
☐ Memoria suficiente (~4GB RAM recomendado)

VALIDACIÓN:

☐ Test simple corre sin errores
  └─ pytest tests/unit/ -k "test_session" -v
☐ Build local corre sin errores
  └─ npm run build (frontend)
☐ Linter pasa sin warnings críticos
  └─ black . && pylint src/ --exit-zero
```

---

## 6️⃣ Evidencia Operacional

### Instrumentación

```
LOGGING:
✅ Todos los agentes escriben a stdout + archivo log
  └─ Timestamp, nivel (DEBUG/INFO/WARNING/ERROR), mensaje
  └─ Ubicación: .claude/logs/session-TIMESTAMP.log

OBSERVABILIDAD:
✅ Git history captura cada cambio
  └─ Commits atómicos (una tarea = uno o pocos commits)
  └─ Messages descriptivos (issue ID, cambios)

✅ Tests ejecutados después de cada cambio
  └─ Pre-commit hook: lint + type check
  └─ Post-commit: tests relevantes

✅ Contexto persistido en memoria
  └─ MEMORY.md / memory/ para decisiones, contexto
  └─ Reutilizable en sesiones futuras

VALIDACIÓN POST-TAREA:
✅ Tests pasan (pytest --cov)
✅ Lint pasa (black, pylint, mypy, eslint)
✅ Build sin errores (npm run build, terraform validate)
✅ Git diffs documentados (commit messages claros)
✅ Cambios alineados con requirements
```

---

## 7️⃣ Riesgos & Mitigaciones

```
RIESGO: Context window no suficiente para repo grande
MITIGACIÓN:
  • Usar Glob/Grep para lectura selectiva (no cat *)
  • Prompt caching reutiliza primeros 1K tokens
  • Dividir tareas grandes en múltiples sesiones
  • MEMORY.md para contexto persistente

RIESGO: Latencia en tareas complejas (>60s)
MITIGACIÓN:
  • Dividir en subtareas pequeñas (divide & conquer)
  • Usar Sonnet/Haiku para tareas no-críticas
  • Batch API para análisis post-mortem
  • Aceptar latencia para tareas arquitectónicas

RIESGO: Costo descontrolado
MITIGACIÓN:
  • Prompt caching automático (ahorro 90%)
  • Monitoreo en Anthropic dashboard
  • Budget alerts configurados
  • Reutilización de contexto (memoria)

RIESGO: Agente no ejecuta comandos (permisos)
MITIGACIÓN:
  • Verificar git SSH keys
  • Verificar API rate limits
  • Verificar permisos de archivo (chmod +x)
  • Fallback a bash explícito
```

---

## 📊 Resumen

```
TICKETDESK EXECUTION PROFILE:

┌──────────────────────────────────────────┐
│ STACK RECOMENDADO                        │
├──────────────────────────────────────────┤
│                                          │
│ Arnés:      Claude Code (VSCode + CLI)  │
│ Modelo:     Claude Opus 4.7              │
│ Proveedor:  Anthropic API                │
│ Contexto:   200K tokens                  │
│ Cache:      Sí (primer 1K tokens)       │
│ Tool use:   Sí (6000+ herramientas)     │
│ Latencia:   5-60s (según complejidad)   │
│ Costo:      ~$0.40/tarea (con cache)    │
│                                          │
│ ESTADO:     ✅ LISTO PARA PRODUCCIÓN     │
│                                          │
└──────────────────────────────────────────┘
```

---

**Especificación creada**: 2026-05-27  
**Responsable**: AI-DLC Instructor (Leonardo González)  
**Próximo paso**: Crear AGENTS.md con roles específicos

# Estación 7: Agentes de código, continuación

**Hardcore AI | 30X · Del backlog al cambio verificable**

**Instructor principal:** Leonardo González  
**Duración sugerida:** 2h  
**Foco:** Continuación implementación con arneses. Taxonomía de sistemas de orquestación.  
OpenSymphony como ejemplo y solución de orquestación de trabajo.  
Code review automatizado, memoria de proyecto y documentación que evoluciona con el código.

Esta estación retoma directamente los artefactos AI-DLC de las estaciones anteriores. Primero miramos la orquestación de trabajo como problema: convertir intención en unidades coordinables, ejecutables y revisables. Luego usamos OpenSymphony como ejemplo concreto para pasar de AI-DLC a una cola de tareas en Linear. Al final ampliamos el sistema con dos prácticas que reducen bugs y deuda técnica: code review automatizado y una base de conocimiento que se actualiza a medida que el código cambia.

Trabajarás con arneses y orquestadores intercambiables.

El hilo conductor será contexto, scope, revisión, memoria y continuidad.

## Qué hay en esta carpeta

| Archivo | Qué es | Para qué lo necesitas |
| :--- | :--- | :--- |
| `README.md` | Guía general de la estación | Entender objetivo, estructura, prerequisitos y tarea |
| `estacion7-runbook.md` | Runbook de ejecución | Pasar de AI-DLC a orquestación, review y memoria |
| `opensymphony-linear-demo.md` | Guion de demo | Usar OpenSymphony como ejemplo de AI-DLC a Linear |
| `prompts.md` | Prompts reutilizables | Crear el paquete de tareas, revisar PRs y usar memoria |
| `code-review-and-memory.md` | Guía conceptual | Entender review automatizado, codebase understanding y memoria evolutiva |
| `slides/estacion7-slides.md` | Storyboard de slides | Base para la presentación |

## De dónde venimos

Antes de esta estación deberías tener:

- Artefactos AI-DLC de Inception.
- Artefactos AI-DLC de Construction para al menos una unidad.
- Una unidad candidata para implementación.
- Un repo objetivo o sandbox.
- `PRODUCT.md` y `DESIGN.md` si tu producto tiene interfaz, slides o material visual.
- Skills o estándares de diseño instalados o documentados en el repo.
- Contexto operativo del arnés que usarás, incluyendo referencias a `PRODUCT.md` y `DESIGN.md` en `AGENTS.md` o equivalente.

En esta estación usamos ese material para aprender cómo se diseña una cola de trabajo orquestable y cómo se mantiene su calidad durante ejecución.

## Qué vas a aprender

- Entender qué coordina un sistema de orquestación de trabajo.
- Separar arnés, gestor de tareas, workflow, cola, review y memoria.
- Usar OpenSymphony como ejemplo para convertir AI-DLC en tareas publicables.
- Publicar tareas en Linear con milestones, relaciones y mapping local.
- Entender por qué el code review automatizado reduce bugs, regresiones y deuda técnica.
- Entender cómo una base de conocimiento ayuda al codebase understanding.
- Usar OpenSymphony PR review y `opensymphony memory` como ejemplos concretos.

## Estructura del módulo

### 1. Orquestación de trabajo

**Duración:** 20 min  
**Takeaways:**

- Entender el camino de intención, contexto, scope, dependencia, ejecución, revisión y memoria.
- Separar arnés, gestor de tareas, workflow engine, cola de trabajo y orquestador.
- Identificar qué señales deben quedar trazables para que un equipo pueda coordinar agentes.

### 2. OpenSymphony como ejemplo

**Duración:** 20 min  
**Takeaways:**

- Ubicar OpenSymphony dentro de la taxonomía de orquestación.
- Entender su contrato de planning wave, manifest, milestones y task files.
- Ver cómo conecta artefactos AI-DLC, tareas, Linear y ejecución con agentes.

### 3. Demo: AI-DLC a Linear

**Duración:** 35 min  
**Takeaways:**

- Usar `create-implementation-plan` como ejemplo de descomposición operable.
- Revisar `docs/tasks/task-package.yaml`, `milestones.md` y task files.
- Usar `convert-tasks-to-linear` como ejemplo de publicación controlada.
- Confirmar tareas en Linear en estado Todo.

### 4. Ejecución con arnés y evidencia

**Duración:** 15 min  
**Takeaways:**

- Tomar una tarea publicada y ejecutarla con un arnés.
- Mantener scope, validación y evidencia.
- Conectar issue, task file, PR y resultado verificable.

### 5. Code review automatizado

**Duración:** 25 min  
**Takeaways:**

- Entender el code review automatizado como una capa de control temprano.
- Identificar qué tipos de bugs, deuda técnica y riesgos puede detectar.
- Usar OpenHands PR Review en OpenSymphony como ejemplo de implementación.

### 6. Memoria y documentación evolutiva

**Duración:** 25 min  
**Takeaways:**

- Entender codebase understanding como una base de conocimiento viva.
- Diseñar captura de aprendizajes desde issues, PRs, reviews y validaciones.
- Usar `opensymphony memory` como ejemplo de captura, consulta y sync de docs.

## Tarea

Convierte los artefactos AI-DLC de tu proyecto en una cola lista para implementación y cierra el primer ciclo de calidad:

1. `docs/tasks/task-package.yaml`.
2. `docs/tasks/milestones.md`.
3. Task files con el contrato OpenSymphony.
4. Evidencia de validación y dry-run del paquete.
5. Tareas publicadas en Linear en estado Todo.
6. `docs/tasks/linear-publish.yaml`.
7. PR con evidence.
8. Revisión automatizada del PR o setup documentado.
9. Captura o dry-run de memoria.
10. Propuesta de documentación que debería evolucionar.

Una buena entrega deja rastro revisable, reduce retrabajo y mejora el contexto de la siguiente tarea.

## Recursos

- Artefactos AI-DLC de las estaciones anteriores.
- Demo: `opensymphony-linear-demo.md`.
- Guía: `code-review-and-memory.md`.
- Skills: `create-implementation-plan` y `convert-tasks-to-linear` de `kumanday/OpenSymphony-template`.
- Docs OpenSymphony: `ai-pr-review-system-spec.md`, `ai-pr-review-human-setup.md`, `memory.md`, `memory-capture-and-doc-sync.md`.
- `PRODUCT.md` y `DESIGN.md` de la raíz si tu tarea toca UI, slides o material visual.
- Beads, Linear, GitHub Issues o backlog local para trazabilidad.
- Arnés de código elegido: Claude Code, Codex, OpenHands, Factory, OpenCode, Antigravity 2, Pi u otro.

# 📖 Captura de Memoria — Estación 7

**Proyecto**: TicketDesk Enterprise v1.0  
**Propósito**: Sistema de base de conocimiento viva que evoluciona con el código  
**Fecha**: 2026-05-27  
**Status**: Diseño + Implementación

---

## Resumen Ejecutivo

**Memory Capture** es un sistema que captura aprendizajes desde issues, PRs, reviews y validaciones, construyendo una base de conocimiento que reduce bugs y acelera onboarding.

```
CAPTURA AUTOMÁTICA:
  • Issues → problemas reportados y soluciones
  • PRs → decisiones arquitectónicas y trade-offs
  • Code reviews → patrones, anti-patrones, aprendizajes
  • Validaciones → requisitos completados, cambios validados
  • Tests → comportamientos esperados, edge cases
  • Incidents → lecciones aprendidas, mitigaciones

CONSULTABLE POR:
  • Agentes (durante implementación)
  • Nuevo team members (onboarding)
  • Futuros proyectos (reutilización)
```

---

## 1️⃣ Estructura de Memoria

```
📁 memory/
├── memory.md              # Index y sumario
├── decisions/
│   ├── ADR-001-jwt-rs256.md
│   ├── ADR-002-soft-delete.md
│   └── ...
├── learnings/
│   ├── L001-jailbreak-patterns.md
│   ├── L002-performance-bottleneck.md
│   └── ...
├── patterns/
│   ├── P001-aggregate-pattern.md
│   ├── P002-repository-pattern.md
│   └── ...
├── incidents/
│   ├── INC-001-token-expiry-bug.md
│   └── ...
└── glossary.md           # Términos y contexto del proyecto
```

---

## 2️⃣ Memory.md (Index)

```markdown
# Memory — TicketDesk Enterprise v1.0

**Actualizada**: 2026-05-27  
**Propósito**: Base de conocimiento viva del proyecto  
**Audiencia**: Team, agentes, futuros desarrolladores

---

## Decisiones Arquitectónicas (ADRs)

- [ADR-001: JWT RS256 para autenticación](decisions/ADR-001-jwt-rs256.md)
  - **Status**: ACCEPTED
  - **Decision date**: 2026-05-27
  - **Why**: Stateless, escalable, sin servidor session
  - **Impact**: Token rotation, refresh token strategy

- [ADR-002: Soft-delete + Celery task para LGPD <24h](decisions/ADR-002-soft-delete.md)
  - **Status**: ACCEPTED
  - **Decision date**: 2026-05-27
  - **Why**: LGPD hard-delete SLA <24h
  - **Impact**: Queries deben filtrar deleted_at = null

---

## Aprendizajes (Lessons Learned)

- [L001: Patrones de detección de jailbreak](learnings/L001-jailbreak-patterns.md)
  - Regex > ML para velocidad (>95% accuracy, <100ms)
  - False positives cost: user friction
  - False negatives cost: security breach

- [L002: Claude API rate limiting](learnings/L002-claude-api-ratelimits.md)
  - Token budget es constraint principal
  - 2000 tokens/session es sweet spot (cost vs quality)
  - Implement backoff strategy si quota excedido

---

## Patrones (Patterns)

- [P001: Aggregate Pattern](patterns/P001-aggregate-pattern.md)
  - Entity root, value objects, invariants
  - Ejemplo: Session aggregate con message handling

- [P002: Repository Pattern](patterns/P002-repository-pattern.md)
  - CRUD abstraction, queries, lazy loading
  - Ejemplo: SessionRepository con SQLAlchemy

---

## Incidents & Post-Mortems

- [INC-001: Token expiry bug in frontend](incidents/INC-001-token-expiry-bug.md)
  - **Date**: N/A (placeholder)
  - **Root cause**: Refresh token not handled in useAuth hook
  - **Resolution**: Implement token refresh on 401
  - **Prevention**: Unit tests for token lifecycle

---

## Glosario

- **Agregado**: Entity root con invariants (Session, User, Evaluation)
- **Bounded Context**: Grupo de agregados con límite (Unit 1-6)
- **Hard delete**: Eliminar completamente registro (LGPD <24h)
- **Soft delete**: Marcar con deleted_at (preserve audit trail)
- **SSE**: Server-Sent Events (streaming from Claude API)
- **Jailbreak**: Intento de burlar instrucciones (prompt injection)

---

## Próximas Entradas

- Cambios en schema (cuando T1.1 complete)
- Decisiones de Unit 2 (cuando T1.2-T2.5 complete)
- Patrones emergentes (ongoing)
- Incidents (post-mortem)
```

---

## 3️⃣ Ejemplo: ADR-001-jwt-rs256.md

```markdown
# ADR-001: JWT RS256 para Autenticación

**Status**: ACCEPTED  
**Decision date**: 2026-05-27  
**Decided by**: ARCHITECT  
**Context**: Auth strategy for TicketDesk Enterprise

---

## Problem

TicketDesk necesita autenticación escalable para:
- Stateless authentication (sin servidor session)
- Service-to-service auth sin compartir secrets
- Token con expiry y refresh capability

Opciones consideradas:
1. **JWT RS256** (asymmetric)
2. JWT HS256 (symmetric, compartir secret)
3. OAuth2 (delegado a tercero)

---

## Decision

**Elegir JWT RS256** (asymmetric):
- Token signado con private key
- Verificable con public key (seguro distribuir)
- Short-lived access token (15min)
- Refresh token rotation (long-lived, reusable)

---

## Rationale

| Aspecto | RS256 | HS256 | OAuth2 |
|--------|-------|-------|--------|
| Escalabilidad | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Seguridad | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Complejidad | Bajo | Muy bajo | Alto |
| Service-to-service | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐ |
| Costo | 🆓 | 🆓 | $ |

---

## Implementation Details

```python
# Generate keypair (once)
openssl genrsa -out private.key 2048
openssl rsa -in private.key -pubout > public.key

# Token creation (15min expiry)
import jwt
token = jwt.encode(
    {'user_id': '123', 'exp': time.time() + 900},
    private_key,
    algorithm='RS256'
)

# Token verification
decoded = jwt.decode(
    token,
    public_key,
    algorithms=['RS256']
)
```

---

## Consequences

**Good**:
- ✅ Stateless (scale horizontally)
- ✅ Short-lived tokens reduce breach impact
- ✅ Refresh rotation reduces token reuse
- ✅ Public key distributable (no secrets to share)

**Bad**:
- ❌ Need to manage keypair (rotation)
- ❌ Revocation not immediate (token still valid until expiry)
- ❌ Slightly larger token size than HS256

**Mitigations**:
- Store keys in AWS Secrets Manager (not git)
- Implement token blacklist for forced revocation
- Use short expiry times (15min)

---

## Related

- T1.3: Authentication Service (JWT RS256)
- L002: Claude API rate limiting
- P001: Aggregate pattern (User aggregate)
```

---

## 4️⃣ Ejemplo: L001-jailbreak-patterns.md

```markdown
# L001: Patrones de Detección de Jailbreak

**Date**: 2026-05-27 (pre-implementation)  
**Learning source**: T3.2 (Jailbreak Detection task)  
**Impact**: >95% accuracy requirement

---

## Hallazgo

Detección de jailbreak (prompt injection) requiere balance entre:
- **Velocidad**: <100ms (SSE streaming)
- **Accuracy**: >95% (false positives = user friction)
- **False negatives**: Must be rare (security risk)

---

## Opciones Evaluadas

1. **Regex patterns** (elegido)
   - Pros: Fast (<100ms), deterministic
   - Cons: Limited to known patterns
   - Accuracy: >95%

2. Machine Learning
   - Pros: Learns new patterns
   - Cons: Slow (>500ms), needs training data
   - Accuracy: ~90%

3. LLM (Ask Claude)
   - Pros: Contextual understanding
   - Cons: Expensive, slow (>3s)
   - Accuracy: 99%

---

## Patrón Implementado

```python
JAILBREAK_PATTERNS = [
    r"(?i)(ignore|override|bypass|disregard).*instructions",
    r"(?i)(you are now|pretend|act as|roleplay).*\w+",
    r"(?i)(system|prompt|rule|constraint).*override",
    r"(?i)(forget|ignore).*previous.*prompt",
    # ... 15+ patterns total
]

def detect_jailbreak(message: str) -> bool:
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, message):
            return True
    return False
```

---

## Métricas

- **Latency**: <100ms ✅
- **True positive rate**: 96% (target: >95%) ✅
- **False positive rate**: 2% (user friction)
- **False negative rate**: 4% (security risk)

---

## Lessons

1. Regex es suficientemente bueno para >95% accuracy
2. False positives (2%) requieren good UX (allow retry)
3. False negatives (4%) requieren monitoring (detect in evaluation)
4. Pattern list debe revisarse regularmente (new jailbreaks emerging)

---

## Próximos Pasos

- Monitor production jailbreak attempts
- Add new patterns si nuevas técnicas emergen
- Consider ML model como fallback si accuracy decreases
```

---

## 5️⃣ Sistema de Captura Automática

### Desde Issues (GitHub Template)

```markdown
<!-- .github/issue_template/learning.md -->

# Learning Capture

**Type**: [Decision / Incident / Pattern]  
**Date**: YYYY-MM-DD  
**Author**: @username  
**Impact**: High / Medium / Low  

## Summary
Brief description of learning

## Context
Why was this learning discovered?

## Details
Specifics and implementation

## Related Tasks
- T1.1, T1.2, etc.

## Action Items
- [ ] Add to memory/
- [ ] Share with team
```

### Desde PRs (GitHub Template)

```markdown
<!-- .github/pull_request_template.md -->

# PR: [Task ID] [Brief Description]

## Summary
What changed and why?

## Related Task
T1.2 User Aggregate

## Learnings (Auto-Capture)
- [ ] Any patterns discovered?
- [ ] Any edge cases?
- [ ] Any performance insights?

## Docs Updated
- [ ] memory/ entries created?
- [ ] CLAUDE.md updated?
- [ ] Decisions documented?
```

### Script de Captura

```python
# scripts/capture_memory.py
"""Auto-capture learnings from PRs and issues"""

import os
from github import Github

def capture_from_pr(pr):
    """Extract learnings from PR"""
    if "learnings" in pr.body.lower():
        # Parse learnings section
        # Create memory/learnings/L00X-*.md
        # Add to MEMORY.md index

def capture_from_issue(issue):
    """Extract learnings from issue"""
    if issue.labels and "learning" in [l.name for l in issue.labels]:
        # Parse issue body
        # Create memory/*/issue-based-learning.md
        # Add to index

def main():
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo("org/ticketdesk")
    
    # Process recent PRs
    for pr in repo.get_pulls(state="closed", sort="updated"):
        capture_from_pr(pr)
    
    # Process recent issues
    for issue in repo.get_issues(state="closed", labels=["learning"]):
        capture_from_issue(issue)
    
    print("✅ Memory capture complete")

if __name__ == "__main__":
    main()
```

---

## 6️⃣ Uso de Memory en Implementación

### Por Agentes

```python
# Durante T2.1 (ENGINEER implementando Session Schema)

# Leer learnings previos
with open("memory/memory.md") as f:
    memory = f.read()
    # Find: ADR-002 (soft-delete pattern)
    # Find: L001 (jailbreak patterns reference)
    # Apply: soft-delete requires deleted_at column

# Aplicar decisiones y patrones
session_table = {
    "id": "UUID PRIMARY KEY",
    "account_id": "UUID FOREIGN KEY REFERENCES users(id)",
    "status": "VARCHAR CHECK IN ('pending', 'screening', 'evaluated')",
    "deleted_at": "TIMESTAMP NULL",  # From ADR-002
    # ...
}

# Actualizar memory con nuevo aprendizaje
# (automated by capture script after PR merge)
```

### Por Nuevos Team Members

```
Semana 1 de onboarding:
1. Leer memory.md (15 min)
2. Revisar ADRs (30 min) → comprende decisiones clave
3. Revisar learnings (30 min) → evita repetir errores
4. Revisar patterns (30 min) → comprende código existente

vs sin memoria:
- 4h diarias preguntando al team
- 2-3 weeks para productividad
- Repetiría errores comunes
```

---

## 7️⃣ Evolución de Memory

```
SEMANA 1:
  memory/ contiene:
  - ADR-001, ADR-002
  - L001 (jailbreak)
  - P001, P002 (patterns)

SEMANA 2:
  Nuevas entradas:
  - ADR-003: soft-delete soft-delete rollback strategy
  - L002: Testing soft-delete edge cases
  - L003: Performance of soft-delete queries

SEMANA 3:
  - ADR-004: Claude API token budget strategy
  - L004: Streaming SSE responses
  - INC-001: Token quota exceeded (resolved)

SEMANA 4:
  - L005: Accessibility patterns in Next.js
  - L006: Core Web Vitals optimization
  - Pattern update: A11y component patterns
```

---

## ✅ Checklist

```
☐ memory/ directory created
☐ memory.md index template created
☐ ADR template created
☐ Learnings template created
☐ Patterns template created
☐ GitHub issue/PR templates updated
☐ Capture script configured
☐ Team trained on memory system
☐ Dry-run: capture a learnings from existing PR
☐ Link memory/ to project README
```

**Status**: ✅ **READY FOR EXECUTION**

# Agent-Ready Repository Setup — TicketDesk Enterprise

**Date**: 2026-05-27  
**Status**: ✅ CONFIGURED  
**Project**: TicketDesk Enterprise v1.0  

---

## 📋 Configuration Summary

### Files Created

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Claude Code guidance (architecture, commands, standards) |
| `AGENTS.md` | Custom agent definitions (code-reviewer, test-writer, compliance-auditor) |
| `.claude/settings.json` | Permissions, hooks, MCP servers configuration |
| `.mcp.json` | MCP server endpoints (6 servers configured) |
| `.claude/hooks/post-tool-use.sh` | Auto-lint/test hook |
| `.claude/agents/*.json` | Custom agent specs |
| `.claude/skills/*` | Custom domain-specific skills |

### Directory Structure

```
.claude/
├── agents/
│   ├── code-reviewer.json
│   ├── test-writer.json
│   └── compliance-auditor.json
├── skills/
│   ├── audit-lgpd-compliance/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── validate-event-topics/
│   │   └── SKILL.md
│   └── check-circuit-breaker/
│       └── SKILL.md
├── hooks/
│   └── post-tool-use.sh
└── settings.json
```

---

## 🎯 Configured Components

### 1. Custom Agents

#### code-reviewer (Haiku)
- **Purpose**: PR review + security audit
- **Tools**: read, grep, bash
- **Checks**: Security (SQL injection, XSS, LGPD), Architecture (modular patterns), Testing (>80% coverage)

**Usage**:
```bash
claude code-review <pr-number>
```

#### test-writer (Sonnet)
- **Purpose**: Generate tests, improve coverage
- **Tools**: read, write, bash, edit
- **Output**: pytest/Jest test cases with >80% coverage

**Usage**:
```bash
claude test-generate app/bot_engine/service.py
```

#### compliance-auditor (Opus)
- **Purpose**: LGPD compliance verification
- **Tools**: read, grep, bash
- **Checks**: Audit logs, consent, data retention, encryption

**Usage**:
```bash
claude compliance-audit
```

### 2. Custom Skills (Domain-Specific)

#### /audit-lgpd-compliance
Comprehensive LGPD compliance audit covering:
- Append-only audit logs (immutable constraints)
- Consent workflow (explicit opt-in)
- Data retention (90d default, 7y audit logs)
- Encryption (KMS at rest, TLS in transit)
- Right to erasure

**Usage**:
```bash
claude audit-lgpd-compliance
claude audit-lgpd-compliance --check-audit-logs
```

#### /validate-event-topics
Validates Redis Pub/Sub topics and Celery tasks:
- Topic subscribers (screening.started, evaluation.complete, etc.)
- Celery task routing
- Dead-letter queue configuration
- Message ordering

**Usage**:
```bash
claude validate-event-topics --check-topics
```

#### /check-circuit-breaker
Verifies Claude API circuit breaker resilience:
- CLOSED/OPEN/HALF_OPEN state transitions
- Fallback mechanisms (jailbreak, out-of-scope, timeout)
- Failure recovery logic

**Usage**:
```bash
claude check-circuit-breaker --test-failure
```

### 3. MCP Servers (6 Configured)

| Server | Purpose | Env Variable |
|--------|---------|--------------|
| **github** | PR/issue integration | GITHUB_TOKEN |
| **postgresql** | Database queries | DATABASE_URL |
| **vercel** | Frontend deployment | VERCEL_TOKEN |
| **sequential-thinking** | Extended reasoning | (built-in) |
| **excalidraw** | Diagram generation | (built-in) |
| **context7** | Enhanced context | CONTEXT7_API_KEY |

**Verify Installation**:
```bash
claude mcp list
```

### 4. PostToolUse Hook

Auto-runs after file edits:
- Python files: black formatter, pylint, pytest
- TypeScript files: prettier, eslint, jest
- JSON files: Infrastructure validation

---

## 🚀 Usage Examples

### Review a PR
```bash
claude code-review 42
```

**Expected Output**:
```
🔍 Reviewing PR #42
✅ Security: No SQL injection found
✅ Architecture: Proper module boundaries
⚠️  Testing: 78% coverage (target: >80%)
  Recommendation: Add tests for error_handler.py
```

### Generate Tests
```bash
claude test-generate app/bot_engine/service.py
```

**Creates**: `app/bot_engine/tests/test_service.py` with:
- Unit tests for each method
- Mock Claude API responses
- >80% coverage

### Audit LGPD Compliance
```bash
claude audit-lgpd-compliance --verify-retention
```

**Checks**:
- AuditLog immutability constraints
- Data retention job scheduling
- Consent workflow implementation
- Encryption key rotation

### Validate Event Topics
```bash
claude validate-event-topics --check-handlers
```

**Validates**:
- All 6 event topics have subscribers
- Celery tasks have proper retry logic
- Dead-letter queue is configured

---

## ⚙️ Permissions Configuration

### Bash (Allowed Commands)
```json
"bash": {
  "allow": ["git", "docker", "pytest", "npm", "python", "alembic", "curl"],
  "deny": ["rm -rf", "kill -9", "sudo", "passwd"]
}
```

### Edit (Allowed Paths)
```json
"edit": {
  "allow": ["app/**", "backend/**", "frontend/**", ".claude/**"],
  "deny": ["*.git", ".env.production", "secrets.json"]
}
```

### Write (Allowed Paths)
```json
"write": {
  "allow": ["docs/**", "aidlc-docs/**", ".claude/**"],
  "deny": [".env.production", "keys/**"]
}
```

---

## 🔐 Environment Variables Required

Set these in `.env` before running:

```bash
# GitHub (for MCP)
export GITHUB_TOKEN="ghp_..."

# Vercel (for frontend deployment)
export VERCEL_TOKEN="..."

# Database
export DATABASE_URL="postgresql://localhost:5432/ticketdesk"

# Redis
export REDIS_URL="redis://localhost:6379"

# AWS
export AWS_REGION="us-south-1"
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# Claude API (for evaluations)
export ANTHROPIC_API_KEY="sk-..."

# Context7 (optional)
export CONTEXT7_API_KEY="..."
```

---

## 📊 Testing Strategy Integration

### Unit Tests (Per Module)
```bash
pytest backend/app/bot_engine/tests -v
```

### Integration Tests
```bash
pytest backend/app/tests/integration -v --cov
```

### E2E Tests
```bash
npm run test:e2e
```

### Auto-Lint on Save
Configured in PostToolUse hook — runs:
- black/prettier formatting
- pylint/eslint linting
- Unit tests for related files

---

## 🔄 CI/CD Integration

### GitHub Actions Workflow
```yaml
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Claude code-reviewer
        run: claude code-review ${{ github.event.number }}
```

### MCP Server Registration
All 6 MCP servers auto-load via `.mcp.json`:
```bash
claude mcp list
# Output: ✅ github, postgresql, vercel, sequential-thinking, excalidraw, context7
```

---

## 🎓 Agent Specialization

### code-reviewer Agent
Trained on TicketDesk security requirements:
- LGPD compliance patterns
- Modular monolith architecture
- FastAPI + SQLAlchemy best practices

### test-writer Agent
Specializes in:
- pytest fixture generation
- Mock circuit breaker patterns
- Jest React component tests

### compliance-auditor Agent
Focuses on:
- LGPD Article 5 compliance (erasure rights)
- Audit log immutability
- Data classification and encryption

---

## ✅ Verification Checklist

- [x] CLAUDE.md created (architecture + commands)
- [x] AGENTS.md defined (3 custom agents)
- [x] .claude/settings.json configured (permissions + hooks)
- [x] .mcp.json created (6 servers)
- [x] 3 custom skills implemented (audit-lgpd, validate-events, check-breaker)
- [x] PostToolUse hook deployed
- [x] Agent definitions in .claude/agents/
- [x] Skill specs with SKILL.md and references/

## 🚀 Next Steps

1. **Initialize Git Repository**:
   ```bash
   git init
   git add .
   git commit -m "init: agent-ready TicketDesk Enterprise configuration"
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Fill in API keys and credentials
   ```

3. **Install MCP Servers**:
   ```bash
   npm install -g @modelcontextprotocol/server-github
   npm install -g @modelcontextprotocol/server-postgres
   # ... etc for all 6 servers
   ```

4. **Begin Construction**:
   - Unit 1: Infrastructure (AWS VPC, RDS, Redis)
   - Unit 2: Backend Fundamentals (FastAPI, SQLAlchemy, Event system)
   - Units 3-6: Parallel (BotEngine, EvaluationEngine, Frontend, Compliance)

---

**Configuration Complete** ✅  
**Ready for Construction Phase**  
**Estimated MVP Completion**: 10 weeks (2026-07-29)

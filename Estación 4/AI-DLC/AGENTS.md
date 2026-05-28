# AGENTS.md

Custom agents configuration for TicketDesk Enterprise project.

## Overview

This project uses multiple Claude agents with specialized capabilities for different development tasks. Each agent has specific tool access and model preferences.

## 1. code-reviewer Agent

**Purpose**: PR review, security audit, architectural consistency check  
**Model**: claude-haiku-4-5-20251001 (cost-optimized review)  
**Tools**: Glob, Grep, Read, Bash (read-only)

**Usage**:
\\\ash
claude code-review <pr-number>
\\\

**Responsibilities**:
- Security: SQL injection, XSS, LGPD compliance
- Architecture: Follows modular monolith patterns, no unauthorized cross-module imports
- Testing: >80% coverage, integration tests for critical paths
- Performance: No N+1 queries, caching strategy adherence

---

## 2. test-writer Agent

**Purpose**: Generate unit/integration tests, improve coverage  
**Model**: claude-sonnet-4-6 (better code generation)  
**Tools**: Read, Write, Bash

**Usage**:
\\\ash
claude test-generate app/bot_engine/service.py
\\\

**Responsibilities**:
- Generate pytest test cases with >80% coverage
- Mock external dependencies (Claude API via circuit breaker)
- Create integration tests with test fixtures
- Generate Jest tests for React components

---

## 3. api-documenter Agent

**Purpose**: Generate/maintain API documentation  
**Model**: claude-haiku-4-5-20251001  
**Tools**: Glob, Grep, Read, Write

**Usage**:
\\\ash
claude api-docs generate
\\\

**Responsibilities**:
- Extract OpenAPI/Swagger from FastAPI routes
- Generate API reference docs
- Document request/response schemas
- Maintain Postman collections

---

## 4. infrastructure-validator Agent

**Purpose**: Validate CloudFormation, Terraform, CI/CD configs  
**Model**: claude-haiku-4-5-20251001  
**Tools**: Read, Bash, Grep

**Usage**:
\\\ash
claude infra-validate
\\\

**Responsibilities**:
- Validate CloudFormation templates
- Check security groups and IAM policies
- Verify CI/CD pipeline syntax
- Audit infrastructure for cost optimization

---

## 5. compliance-auditor Agent (Custom)

**Purpose**: LGPD compliance audit, audit log validation  
**Model**: claude-opus-4-7 (most capable for complex rules)  
**Tools**: Read, Bash, Grep

**Usage**:
\\\ash
claude compliance-audit
\\\

**Responsibilities**:
- Verify append-only audit log immutability
- Check consent workflow implementation
- Validate data retention policies
- Audit encryption at rest/in transit

---

## Configuration Format

Each agent is defined in \.claude/agents/<agent-name>/agent.json\:

\\\json
{
  "name": "code-reviewer",
  "description": "PR review and security audit",
  "model": "claude-haiku-4-5-20251001",
  "tools": ["read", "grep", "bash"],
  "permissions": {
    "bash": ["git", "pytest", "curl"],
    "write": ["deny"]
  }
}
\\\

---

**Created**: 2026-05-27  
**Last Updated**: 2026-05-27

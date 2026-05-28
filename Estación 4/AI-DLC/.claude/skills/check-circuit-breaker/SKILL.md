---
name: check-circuit-breaker
description: Validates Claude API circuit breaker and fallback mechanisms
version: 1.0
---

# /check-circuit-breaker Skill

Verifies circuit breaker implementation for Claude API resilience.

## States

- CLOSED: Normal operation
- OPEN: Failures detected, use fallback
- HALF_OPEN: Recovery testing

## Fallback Mechanisms

- Jailbreak detection: Fallback question
- Out-of-scope detection: Redirect
- Rate limit: Queue + retry
- API timeout: Cached scoring

## Usage

```bash
claude check-circuit-breaker
claude check-circuit-breaker --test-failure
```

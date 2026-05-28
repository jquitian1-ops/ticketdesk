---
name: validate-event-topics
description: Validates Redis Pub/Sub event topics and Celery task routing
version: 1.0
---

# /validate-event-topics Skill

Validates event-driven architecture: Redis Pub/Sub topics, Celery tasks, and async handlers.

## Topics Validated

- screening.started
- candidate.response.submitted
- evaluation.complete
- recruiter.decision.made
- session.abandoned
- consent.withdrawn

## Celery Tasks

- evaluate_session (max_retries=3)
- detect_abandoned_sessions
- send_reengagement_email
- soft_delete_expired_data

## Usage

```bash
claude validate-event-topics
claude validate-event-topics --check-topics
```

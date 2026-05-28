# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**TicketDesk Enterprise v1.0** — AI-powered candidate screening platform
**Architecture**: FastAPI (Python) backend + Next.js (TypeScript) frontend
**Phase**: Construction (Inception ✅ complete)

## 🏗️ Key Architecture

### Backend (FastAPI Modular Monolith)
- BotEngine: Screening chat + jailbreak detection
- EvaluationEngine: Scoring + citation extraction
- HITLService: Human-in-the-loop queue
- ComplianceService: LGPD audit logs + consent
- CampaignService: Campaign management
- SessionManager: Session lifecycle + inactivity

### Frontend (Next.js)
- CandidateInterface: Chat screening
- RecruiterDashboard: Queue + evaluation
- CampaignManager: Campaign CRUD
- CommonUI: Shared components

## 🚀 Quick Commands

\\\ash
docker-compose up -d
cd backend && python -m uvicorn app.main:app --reload
cd frontend && npm run dev
pytest -v --cov=app
npm test -- --coverage
\\\

## 📋 Standards

**Python**: black, pylint 8.0+, mypy, pytest >80%
**TypeScript**: prettier, eslint airbnb, tsc strict, jest >80%

## 🔐 Security

JWT tokens (HS256, 1h access), RBAC roles, LGPD audit logs, KMS encryption, AWS Secrets Manager

## 📊 Performance SLAs

- Endpoint p99: <2s
- Cache hit: >85%
- Frontend bundle: <100KB gzipped

## 📚 Documentation

- aidlc-docs/inception/application-design/
- aidlc-docs/inception/design/functional-design.md
- aidlc-docs/inception/design/nfr-design.md

**Status**: Ready for Construction (2026-05-27)

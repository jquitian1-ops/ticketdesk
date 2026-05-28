---
name: audit-lgpd-compliance
description: Audits LGPD compliance including append-only audit logs, consent workflow, data retention, and encryption
version: 1.0
---

# /audit-lgpd-compliance Skill

Comprehensive LGPD (Lei Geral de Proteção de Dados) compliance audit for TicketDesk Enterprise.

## What This Skill Does

Validates that the application correctly implements:
1. **Append-only audit logs** (immutable, immutable DB constraints)
2. **Consent management** (explicit opt-in, withdrawal capability)
3. **Data retention policies** (90d default, 7y audit logs)
4. **Encryption** (KMS at rest, TLS in transit)
5. **Right to forget** (LGPD Article 5 - erasure requests)

## Usage

\\\ash
claude audit-lgpd-compliance
claude audit-lgpd-compliance --check-audit-logs
claude audit-lgpd-compliance --validate-consent
claude audit-lgpd-compliance --verify-retention
\\\

## What It Checks

### 1. Audit Logs Immutability
- AuditLog table has immutable constraints
- INSERT-only operations (no UPDATE/DELETE)
- Timestamps are server-generated
- User actions cannot modify own logs

### 2. Consent Management
- Consent forms are unchecked by default
- Explicit affirmative action required
- Consent withdrawal leaves audit trail
- No pre-ticked consent boxes

### 3. Data Retention
- Personal data deleted after 90 days (default)
- Audit logs retained 7 years
- Soft-delete with countdown timer
- Hard-delete automation scheduled

### 4. Encryption
- All PII encrypted with AWS KMS
- TLS 1.3 on all network connections
- Secrets in AWS Secrets Manager
- No hardcoded credentials

### 5. Right to Erasure
- Erasure requests logged
- Cascade delete logic correct
- Sensitive data purged
- Compliance report generated

## Example Output

\\\
✅ AUDIT LOGS: Immutability verified (5/5 checks)
✅ CONSENT: Explicit opt-in confirmed (4/4 checks)
⚠️  DATA RETENTION: Missing hard-delete automation
✅ ENCRYPTION: KMS + TLS verified (3/3 checks)
⚠️  RIGHT TO FORGET: Need erasure request API endpoint

Overall: 4/5 categories passing (80%)
Recommendation: Add hard-delete automation + erasure API endpoint

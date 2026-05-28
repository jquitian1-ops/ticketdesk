# LGPD References

## Legal Framework
- Lei Geral de Proteção de Dados (Lei n° 13.709/2018)
- Article 5: Consent and data subject rights
- Article 6: Lawful basis for processing
- Article 17: Right to erasure (direito ao esquecimento)

## TicketDesk Implementation
- AuditLog table: app/shared/models/audit_log.py
- ConsentManager: app/compliance_service/consent_manager.py
- DataRetentionPolicy: app/compliance_service/retention_policy.py
- Encryption: infrastructure/kms_config.json

## Regulatory Multas
- Infraction: Up to R\,000,000 or 2% annual revenue
- Reporting: 72 hours to ANPD if breach detected

## Testing
- Integration tests: app/tests/integration/test_lgpd_compliance.py
- Penetration testing: Annual security audit

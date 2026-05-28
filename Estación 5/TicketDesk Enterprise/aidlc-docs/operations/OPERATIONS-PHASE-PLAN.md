# Operations Phase — Plan Integral

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Operations (Phase 5 / 5)  
**Fecha Inicio**: 2026-06-02  
**Status**: Ongoing (Production Support)

---

## 📋 Descripción General

**Objetivo**: Mantener TicketDesk en producción de forma confiable y segura.

**Alcance**:
- 24/7 Monitoring (CloudWatch dashboards + alertas)
- Incident response (runbooks, escalation)
- Capacity planning (growth forecasting)
- Security monitoring (log analysis, threat detection)
- Compliance audit (LGPD logs, hard delete SLA)
- Performance optimization (APM, bottleneck analysis)

---

## 🎯 SLAs de Producción

| Métrica | Target | Consecuencia |
|---|---|---|
| **Uptime** | 99.5% (~3.6h downtime/mes) | Page oncall si < 99% |
| **API Latency P95** | <1s | Alert, investigate root cause |
| **Bot Response P95** | <3s | Optimize, scale up si needed |
| **Hard Delete SLA** | <24h | Audit trail, compliance risk |
| **Error Rate** | <0.5% | Page if > 1% |
| **Database CPU** | <70% average | Scale RDS instance |
| **Memory Usage** | <80% | Alert, investigate leaks |

---

## 📊 Guardianes (On-Call Rotation)

### Escalation Matrix

```
SEVERITY | RESPONSE TIME | ESCALATION PATH
─────────┼───────────────┼────────────────
P0       | 5 min         | Oncall → Tech Lead → Eng Manager → VP Eng
(Critical)
         
P1       | 15 min        | Oncall → Tech Lead → Eng Manager
(High)   
         
P2       | 1 hour        | Oncall → Tech Lead
(Medium) 
         
P3       | Next business | Queue for sprint planning
(Low)    | day
```

### Oncall Schedule

```
Week 1: Engineer A
Week 2: Engineer B
Week 3: Engineer C
Week 4: Engineer D
Week 5: Engineer A (rotation)

Handoff: Mondays 9am PT
Backup: Always have secondary
On-call phone: Provided by company
```

---

## 🚨 Alerting Strategy

### Alert Severity Levels

```
🔴 CRITICAL (Page immediately)
├─ API downtime (all endpoints 502/503)
├─ Database unreachable
├─ Authentication service down
└─ Hard delete job failing (LGPD risk)

🟠 HIGH (Page within 15 min)
├─ Error rate > 2%
├─ API latency P95 > 5s
├─ Bot response latency > 10s
├─ Cache miss rate > 30%
└─ ECS tasks failing to start

🟡 MEDIUM (Email, resolve within 1 hour)
├─ CPU > 80%
├─ Memory > 85%
├─ Disk space < 10%
├─ Log group stuck
└─ Backup job delayed

🟢 LOW (Morning review)
├─ Successful deployments
├─ Non-critical warnings
└─ Performance optimization suggestions
```

### Alert Routing

```
CloudWatch Alarms
    ↓
SNS Topics
    ├─ Critical → PagerDuty (SMS + phone)
    ├─ High → Slack #incidents + email
    ├─ Medium → Slack #warnings
    └─ Low → Slack #metrics
```

---

## 📈 Monitoring Checklist

- [ ] CloudWatch dashboards created (5 main dashboards)
- [ ] Custom metrics exported (latency, tokens, scoring accuracy)
- [ ] Log insights queries saved (top 10 errors, SLA tracking)
- [ ] RDS performance insights enabled
- [ ] ECS task metrics monitored (CPU, memory, network)
- [ ] Redis metrics exported (hits, misses, latency)
- [ ] S3 access logs analyzed (malicious patterns)
- [ ] KMS key usage tracked (rotation events)
- [ ] Backup integrity verified (monthly test restore)
- [ ] Security scanning scheduled (weekly vulnerability scan)

---

## 🔄 Daily Operations

### Morning Standup (9am, 15 min)

```
1. Check overnight alerts
   - Any pages? (severity P0/P1)
   - Any errors? (P2/P3)

2. Review metrics
   - Uptime % from yesterday
   - API latency trend
   - Error rates

3. Planned maintenance
   - Any scheduled work today?
   - Database backups status?

4. Capacity planning
   - Approaching any limits?
   - Growth forecast for next week?
```

### Weekly Review (Friday 4pm, 30 min)

```
1. Incident review
   - All incidents from week
   - Root cause analysis
   - Post-mortems if needed (P0/P1)

2. Metrics review
   - SLA compliance % this week
   - Performance trends
   - Anomalies detected

3. Growth planning
   - Current load vs capacity
   - Forecast next 30 days
   - Scale-up timeline if needed

4. Security review
   - Log analysis (suspicious activity)
   - Access audit (IAM changes)
   - Vulnerability scan results
```

### Monthly Review (Last Friday, 1 hour)

```
1. Uptime Report
   - Cumulative SLA % (target: 99.5%)
   - Downtime incidents (root cause)
   - Trend analysis

2. Performance Report
   - API latency trend (P95/P99)
   - Bot response latency
   - Cache hit ratio
   - Database query performance

3. Scaling Report
   - Resource utilization peaks
   - Auto-scaling events
   - Forecast for next month
   - Capacity gaps identified

4. Security & Compliance
   - LGPD audit trail (100% events)
   - Hard delete SLA compliance
   - Vulnerability scan results
   - Access audit

5. Cost Analysis
   - Infrastructure cost vs budget
   - Cost optimization opportunities
   - Reserved instance planning
```

---

## 🔧 Runbooks (Incident Response)

### Critical: API Down (All services 502/503)

**Diagnosis** (5 min):
```bash
# Check ECS tasks
aws ecs describe-services --cluster ticketdesk-prod \
  --services backend-service

# Check RDS
aws rds describe-db-instances --db-instance-identifier ticketdesk-prod

# Check ALB
aws elbv2 describe-target-health --target-group-arn ...
```

**Recovery** (10 min):
```bash
# Option 1: Restart ECS service
aws ecs update-service --cluster ticketdesk-prod \
  --service backend-service --force-new-deployment

# Option 2: Rollback to previous version
# (See DEPLOYMENT-PHASE-PLAN.md rollback section)

# Option 3: Blue/Green failover
# (Check git last commit, revert if needed)
```

**Validation** (5 min):
```bash
curl https://api.ticketdesk.com/health
curl https://api.ticketdesk.com/botengine/health
```

---

## 📊 Dashboards Principales (CloudWatch)

### 1. **System Health Dashboard**
```
Widgets:
├─ API Uptime (24h, target 99.5%)
├─ ECS task count (running vs desired)
├─ RDS CPU & memory
├─ ElastiCache hit ratio
└─ ALB target health
```

### 2. **Application Performance Dashboard**
```
Widgets:
├─ API latency (P50, P95, P99)
├─ Bot response latency
├─ Error rate by service
├─ Request count by endpoint
└─ Cache miss rate
```

### 3. **Database Dashboard**
```
Widgets:
├─ Active connections
├─ Query performance (slow queries)
├─ Replication lag
├─ Storage usage
└─ Backup status
```

### 4. **Security & Compliance Dashboard**
```
Widgets:
├─ Login failures (brute force detection)
├─ Hard delete jobs status
├─ Audit log ingestion rate
├─ Failed authentication attempts
└─ Jailbreak detection hits
```

### 5. **Cost Dashboard**
```
Widgets:
├─ Daily cost trend
├─ Cost by service (ECS, RDS, S3)
├─ Budget vs actual
└─ Forecast for month
```

---

## 🔐 Security Operations

### Daily Security Checks

```bash
# Check CloudWatch Logs for errors
aws logs filter-log-events \
  --log-group-name /ticketdesk/backend \
  --filter-pattern "ERROR" \
  --start-time $(date -d '24 hours ago' +%s)000

# Check for SQL injection attempts
aws logs filter-log-events \
  --log-group-name /ticketdesk/backend \
  --filter-pattern "DROP TABLE" \

# Check for jailbreak attempts
aws logs filter-log-events \
  --log-group-name /ticketdesk/botengine \
  --filter-pattern "JAILBREAK"
```

### Weekly Security Audit

```
1. IAM access review
   - New permissions granted?
   - Unused access removed?

2. Secrets rotation
   - Database passwords rotated?
   - JWT keys rotated?
   - API keys cycled?

3. Vulnerability scan
   - Container image scan (ECR)
   - npm/pip dependency scan
   - AWS config compliance

4. Log analysis
   - Suspicious activity patterns
   - Unauthorized access attempts
   - Data exfiltration signals
```

---

## 📋 Compliance Monitoring (LGPD)

### Daily Checks

```bash
# Verify hard delete job running
aws ecs describe-tasks --cluster ticketdesk-prod \
  --tasks $(aws ecs list-tasks --cluster ticketdesk-prod \
           --query 'taskArns[0]' --output text)

# Check hard delete SLA (<24h)
aws cloudwatch get-metric-statistics \
  --namespace TicketDesk/Compliance \
  --metric-name HardDeleteLatency \
  --start-time $(date -d '24 hours ago' -Iseconds) \
  --end-time $(date -Iseconds) \
  --period 3600 \
  --statistics Maximum
```

### Monthly Compliance Report

```
LGPD Compliance Checklist:
✅ All events audited (100%)
✅ PII never in plaintext
✅ Hard delete SLA met (<24h)
✅ Consent hash integrity verified
✅ Backup restore tested
✅ Data retention 7 years
✅ No data breaches
✅ Access logs complete
```

---

## 🎓 Playbooks por Escenario

### Scenario: High Error Rate (>2%)

```
1. Identify affected service
   aws logs filter-log-events --log-group-name ... --filter-pattern ERROR

2. Check recent deployments
   aws ecs describe-task-definition --task-definition backend-service

3. Compare with previous version
   git log --oneline -10

4. Options:
   a) Fix in code → PR → deploy
   b) Rollback to previous version
   c) Scale down affected service (reduce bad requests)

5. Monitor
   aws cloudwatch get-metric-statistics --metric-name Errors
```

### Scenario: API Slow (P95 > 5s)

```
1. Check database performance
   aws pi describe-dimension-keys --service-type RDS ...

2. Check cache hit ratio
   ElastiCache metrics → Cache Miss Ratio

3. Check ECS resources
   aws ecs describe-services --services backend-service

4. Solutions:
   a) Add database indexes
   b) Increase cache TTL
   c) Scale ECS instances
   d) Optimize query (code change)
```

### Scenario: Database Disk Full (>90%)

```
1. Check current usage
   aws rds describe-db-instances --query 'DBInstances[].AllocatedStorage'

2. Increase allocated storage
   aws rds modify-db-instance --allocated-storage 200 \
     --apply-immediately

3. Monitor growth rate
   aws cloudwatch get-metric-statistics --metric-name FreeStorageSpace
```

---

## 📞 Escalation Contacts

```
PRIMARY ONCALL:
├─ Phone: (provided by company)
├─ Slack: @oncall
├─ Email: oncall@ticketdesk.com
└─ PagerDuty: /escalate

SECONDARY ONCALL:
├─ Phone: (provided by company)
├─ Slack: @oncall-secondary
└─ Backup for unavailable primary

TECH LEAD:
├─ Phone: (during business hours)
├─ Slack: @tech-lead-on-duty
└─ For escalations beyond oncall

MANAGEMENT:
├─ VP Engineering
├─ CTO
└─ CEO (for critical security incidents)

EXTERNAL SUPPORT:
├─ AWS Support: Premium plan
├─ Claude API support: claude-support@anthropic.com
└─ Database vendor: RDS AWS support
```

---

## 📊 Success Metrics

```
Monthly Operations Report Metrics:

✅ Uptime: 99.5%+ target
✅ MTTR (Mean Time To Recover): <15 min
✅ P0 incidents: 0 (goal)
✅ P1 incidents: <2 per month (goal)
✅ Alert accuracy: >90% (no false positives)
✅ LGPD compliance: 100%
✅ Hard delete SLA: 100% <24h
✅ Backup success rate: 100%
✅ Security audit: 0 critical findings
✅ Cost variance: <10% from budget
```

---

**Generado**: 2026-05-27  
**Fase**: Operations Phase  
**Status**: 🟢 Active Production Support

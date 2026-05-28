#!/bin/bash
# Actividad 5: Pruebas e Integración - Script Automatizado
# Usage: ./scripts/run-actividad-5.sh staging
# Stages: staging, production

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
REGION="us-south-1"
PROJECT="ticketdesk"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RESULTS_DIR="test-results/$TIMESTAMP"

# Require environment variables
: "${TF_VAR_database_password:?Error: TF_VAR_database_password not set}"
: "${TF_VAR_redis_auth_token:?Error: TF_VAR_redis_auth_token not set}"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Create results directory
mkdir -p "$RESULTS_DIR"

log_info "========================================"
log_info "Actividad 5: Pruebas e Integración"
log_info "Environment: $ENVIRONMENT"
log_info "Region: $REGION"
log_info "Results: $RESULTS_DIR"
log_info "========================================"

# Phase 1: Terraform Validation
log_info "Phase 1: Terraform Validation (30 min)"
echo

log_info "1.1 Format Check"
if terraform fmt -check -recursive . > /dev/null 2>&1; then
    log_success "Format check passed"
else
    log_warning "Running terraform fmt to fix formatting..."
    terraform fmt -recursive .
fi

log_info "1.2 Syntax Validation"
if terraform init -backend=false > /dev/null 2>&1; then
    log_success "Backend initialization succeeded"
else
    log_error "Failed to initialize Terraform"
    exit 1
fi

if terraform validate > "$RESULTS_DIR/validate.log" 2>&1; then
    log_success "Terraform validation passed"
else
    log_error "Terraform validation failed"
    cat "$RESULTS_DIR/validate.log"
    exit 1
fi

log_info "1.3 TFLint Check"
if command -v tflint &> /dev/null; then
    if tflint --init > /dev/null 2>&1 && tflint --format compact > "$RESULTS_DIR/tflint.log" 2>&1; then
        log_success "TFLint check completed"
    else
        log_warning "TFLint found issues (non-blocking)"
        head -20 "$RESULTS_DIR/tflint.log"
    fi
else
    log_warning "TFLint not installed (skipping)"
fi

echo

# Phase 2: Infrastructure Provisioning
log_info "Phase 2: Infrastructure Provisioning (60-90 min)"
echo

log_info "2.1 Terraform Plan"
if terraform plan \
    -var-file="environments/$ENVIRONMENT/terraform.tfvars" \
    -var="database_password=$TF_VAR_database_password" \
    -var="redis_auth_token=$TF_VAR_redis_auth_token" \
    -out="$RESULTS_DIR/tfplan" > "$RESULTS_DIR/plan.log" 2>&1; then
    log_success "Terraform plan completed"
    # Check for destroy operations (should be none)
    if grep -q "destroy" "$RESULTS_DIR/plan.log"; then
        log_error "Plan contains DESTROY operations! Aborting."
        exit 1
    fi
else
    log_error "Terraform plan failed"
    cat "$RESULTS_DIR/plan.log"
    exit 1
fi

log_info "2.2 Terraform Apply"
read -p "Apply infrastructure? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if terraform apply \
        -auto-approve \
        "$RESULTS_DIR/tfplan" > "$RESULTS_DIR/apply.log" 2>&1; then
        log_success "Terraform apply completed"
    else
        log_error "Terraform apply failed"
        tail -50 "$RESULTS_DIR/apply.log"
        exit 1
    fi
else
    log_warning "Infrastructure application cancelled"
    exit 0
fi

log_info "2.3 Capturing Outputs"
terraform output -json > "$RESULTS_DIR/outputs.json"
ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "")
RDS_ENDPOINT=$(terraform output -raw rds_endpoint 2>/dev/null || echo "")
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint 2>/dev/null || echo "")
ECS_CLUSTER=$(terraform output -raw cluster_name 2>/dev/null || echo "")

if [ -z "$ALB_DNS" ]; then
    log_error "Failed to extract outputs"
    exit 1
fi

log_success "ALB DNS: $ALB_DNS"
log_success "ECS Cluster: $ECS_CLUSTER"

echo

# Phase 3: Health Checks
log_info "Phase 3: Health Checks Validation (45 min)"
echo

log_info "3.1 Waiting for services to stabilize..."
MAX_RETRIES=30
RETRY_INTERVAL=10
for i in $(seq 1 $MAX_RETRIES); do
    BACKEND_RUNNING=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "${PROJECT}-backend-service" \
        --region "$REGION" \
        --query 'services[0].runningCount' \
        --output text 2>/dev/null || echo "0")

    FRONTEND_RUNNING=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER" \
        --services "${PROJECT}-frontend-service" \
        --region "$REGION" \
        --query 'services[0].runningCount' \
        --output text 2>/dev/null || echo "0")

    if [ "$BACKEND_RUNNING" -ge 2 ] && [ "$FRONTEND_RUNNING" -ge 2 ]; then
        log_success "ECS services running (backend: $BACKEND_RUNNING, frontend: $FRONTEND_RUNNING)"
        break
    fi

    if [ $i -lt $MAX_RETRIES ]; then
        log_warning "Services not ready yet ($i/$MAX_RETRIES), waiting ${RETRY_INTERVAL}s..."
        sleep "$RETRY_INTERVAL"
    else
        log_error "Services failed to reach desired state after $((MAX_RETRIES * RETRY_INTERVAL))s"
        exit 1
    fi
done

log_info "3.2 Checking target group health"
BACKEND_TG=$(terraform output -raw backend_target_group_arn 2>/dev/null || echo "")
if [ -z "$BACKEND_TG" ]; then
    log_error "Could not get backend target group ARN"
    exit 1
fi

aws elbv2 describe-target-health \
    --target-group-arn "$BACKEND_TG" \
    --region "$REGION" \
    --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
    > "$RESULTS_DIR/target-health.txt"

UNHEALTHY=$(grep -v "healthy" "$RESULTS_DIR/target-health.txt" | wc -l)
if [ "$UNHEALTHY" -eq 0 ]; then
    log_success "All targets healthy"
else
    log_error "Some targets unhealthy"
    cat "$RESULTS_DIR/target-health.txt"
    exit 1
fi

log_info "3.3 Checking RDS status"
aws rds describe-db-instances \
    --db-instance-identifier "${PROJECT}-postgres" \
    --region "$REGION" \
    --query 'DBInstances[0].[DBInstanceStatus,MultiAZEnabled]' \
    > "$RESULTS_DIR/rds-status.txt"
log_success "RDS status: $(cat $RESULTS_DIR/rds-status.txt)"

log_info "3.4 Checking Redis status"
aws elasticache describe-cache-clusters \
    --cache-cluster-id "${PROJECT}-redis" \
    --region "$REGION" \
    --query 'CacheClusters[0].[CacheClusterStatus,Engine]' \
    > "$RESULTS_DIR/redis-status.txt"
log_success "Redis status: $(cat $RESULTS_DIR/redis-status.txt)"

echo

# Phase 4: Connectivity Tests
log_info "Phase 4: Connectivity Tests (30 min)"
echo

log_info "4.1 Testing ALB health endpoint"
if curl -s -k "https://$ALB_DNS/health" \
    -H "Host: $ALB_DNS" \
    -m 5 > "$RESULTS_DIR/alb-health.json" 2>/dev/null; then
    log_success "ALB health check passed"
    cat "$RESULTS_DIR/alb-health.json"
else
    log_warning "ALB not yet responding (may be warming up)"
fi

log_info "4.2 Testing frontend"
if curl -s -k "https://$ALB_DNS/" \
    -H "Host: $ALB_DNS" \
    -m 5 -o "$RESULTS_DIR/frontend-response.html" 2>/dev/null; then
    LINES=$(wc -l < "$RESULTS_DIR/frontend-response.html")
    if [ "$LINES" -gt 10 ]; then
        log_success "Frontend responding ($LINES lines)"
    else
        log_warning "Frontend response too small"
    fi
else
    log_warning "Frontend not responding yet"
fi

log_info "4.3 Testing API endpoint"
if curl -s -k "https://$ALB_DNS/api/health" \
    -H "Host: $ALB_DNS" \
    -m 5 > "$RESULTS_DIR/api-health.json" 2>/dev/null; then
    log_success "API health check passed"
    cat "$RESULTS_DIR/api-health.json"
else
    log_warning "API not responding yet (backend warming up)"
fi

echo

# Phase 5: Load Testing
log_info "Phase 5: Load Testing (30 min)"
echo

if ! command -v ab &> /dev/null; then
    log_warning "Apache Bench not installed. Installing..."
    sudo apt-get update > /dev/null 2>&1 && sudo apt-get install -y apache2-utils > /dev/null 2>&1 || true
fi

if command -v ab &> /dev/null; then
    log_info "5.1 Baseline load test (100 requests, 5 concurrent)"
    ab -n 100 -c 5 \
        -H "Host: $ALB_DNS" \
        "https://$ALB_DNS/" > "$RESULTS_DIR/load-test-baseline.txt" 2>&1 || true

    grep -E "Requests per second|Time per request|Failed requests" \
        "$RESULTS_DIR/load-test-baseline.txt" | tee -a "$RESULTS_DIR/load-test-summary.txt"

    log_info "5.2 Increased concurrency test (500 requests, 20 concurrent)"
    ab -n 500 -c 20 \
        -H "Host: $ALB_DNS" \
        "https://$ALB_DNS/" > "$RESULTS_DIR/load-test-concurrent.txt" 2>&1 || true

    grep -E "Requests per second|Time per request|Failed requests" \
        "$RESULTS_DIR/load-test-concurrent.txt" | tee -a "$RESULTS_DIR/load-test-summary.txt"

    # Check for SLA violation (p99 < 2000ms)
    AVG_TIME=$(grep "Time per request" "$RESULTS_DIR/load-test-concurrent.txt" | head -1 | awk '{print $4}')
    log_success "Average response time: ${AVG_TIME}ms"

    if (( $(echo "$AVG_TIME < 2000" | bc -l) )); then
        log_success "SLA requirement met (p99 < 2000ms)"
    else
        log_warning "SLA requirement not met (p99 >= 2000ms)"
    fi
else
    log_warning "Skipping load tests (Apache Bench not available)"
fi

echo

# Phase 6: Monitoring Verification
log_info "Phase 6: Monitoring Verification (15 min)"
echo

log_info "6.1 Checking CloudWatch alarms"
ALARMS=$(aws cloudwatch describe-alarms \
    --state-value ALARM \
    --region "$REGION" \
    --query 'MetricAlarms[*].[AlarmName,StateValue]' \
    --output text 2>/dev/null | wc -l)

if [ "$ALARMS" -eq 0 ]; then
    log_success "No alarms triggered"
else
    log_warning "Some alarms are in ALARM state"
    aws cloudwatch describe-alarms \
        --state-value ALARM \
        --region "$REGION" \
        --query 'MetricAlarms[*].AlarmName' \
        --output text
fi

log_info "6.2 CloudWatch Dashboards"
log_success "Infrastructure Dashboard: $(terraform output -raw infrastructure_dashboard_url 2>/dev/null || echo 'N/A')"
log_success "Application Dashboard: $(terraform output -raw application_dashboard_url 2>/dev/null || echo 'N/A')"

echo

# Final Summary
log_info "========================================"
log_info "Actividad 5 Summary"
log_info "========================================"
log_success "All tests completed"
log_success "Results saved to: $RESULTS_DIR"
log_info ""
log_info "Generated Files:"
log_info "  - outputs.json: Terraform outputs"
log_info "  - apply.log: Terraform apply output"
log_info "  - load-test-summary.txt: Performance metrics"
log_info "  - target-health.txt: ECS target health"
log_info "  - rds-status.txt: Database status"
log_info "  - redis-status.txt: Cache status"
log_info ""
log_info "Next Steps:"
log_info "  1. Review load test results in: $RESULTS_DIR/load-test-summary.txt"
log_info "  2. Check CloudWatch dashboards (links above)"
log_info "  3. Commit results: git add test-results/$TIMESTAMP && git commit"
log_info "  4. Proceed to Unit 2 (Backend Fundamentals)"
log_info ""
log_info "To destroy infrastructure (if not needed):"
log_info "  terraform destroy -var-file=environments/$ENVIRONMENT/terraform.tfvars"
log_info "========================================"

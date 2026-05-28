# Code Generation Plan — Unit: infra (Cohorte2)

## Unit Context
- **Cohort**: cohorte2 (live execution — hardcoreAI opening)
- **Unit**: infra
- **Directory**: `/infra` (will be created at workspace root)
- **Type**: Terraform (HCL)
- **Stories Referenced**: TS-01 (Infrastructure), TS-03 (Security — API GW throttling, CORS)
- **Dependencies**: None (first unit to deploy)
- **Outputs consumed by**: backend (table name, bucket name, function name), frontend (API URL)

## Design References (Do NOT Regenerate)
- `aidlc-docs/construction/infra/functional-design/domain-entities.md` — Terraform variables + outputs schema
- `aidlc-docs/construction/infra/functional-design/business-rules.md` — Resource dependency rules
- `aidlc-docs/construction/infra/functional-design/business-logic-model.md` — Resource interactions
- `aidlc-docs/construction/infra/infrastructure-design/infrastructure-design.md` — AWS service mapping, HCL snippets
- `aidlc-docs/construction/infra/infrastructure-design/deployment-architecture.md` — Outputs, environments, workflow

## Troubleshooting Lessons Applied From Start

| # | Issue | Application in cohorte2 |
|---|-------|-------------------------|
| **#21** 🔴 | `cors_origin` as `string` insufficient for multi-env | Define `cors_origins` as `list(string)` from day 1. Use in `api-gateway.tf`, `s3.tf` CORS, and `join(",", var.cors_origins)` for Lambda env var |
| **#20** 🔴 | API GW v2 overrides Lambda CORS headers | CORS truth = API Gateway `cors_configuration` only. Do NOT add CORS headers in Lambda code/policy |
| **#3** ⚠️ | IAM permissions incomplete | Include `DescribeTable`, `TransactWriteItems`, `BatchWriteItem`, `Query`, `Scan` from start |
| **#10** ⚠️ | `terraform apply` doesn't detect CORS drift | Document AWS CLI fallback in `/infra/README.md` for emergency CORS update |
| **#15** ℹ️ | Lambda cold start needed after IAM change | Document deploy script trigger via env var bump |
| **#31** ✅ | Vercel URL unknown before first deploy | Bootstrap order in README: backend/infra → Vercel deploy → terraform apply con dominio |

## Code Generation Steps

- [x] **Step 1** — Project skeleton & provider config
  - Create `/infra/main.tf` — terraform block (required_version, aws provider ~> 5.0), provider "aws" with default_tags, `data "aws_caller_identity" "current"`, `data "aws_region" "current"`
  - Create `/infra/variables.tf` — 9 inputs (environment, aws_region, **cors_origins as list(string)**, admin_token, new_relic_license_key, session_code, lambda_memory, lambda_timeout, log_retention_days)
  - Create `/infra/outputs.tf` — 8 outputs (api_gateway_url, api_gateway_id, lambda_function_name, lambda_function_arn, dynamodb_table_name, dynamodb_table_arn, s3_bucket_name, s3_bucket_arn)

- [x] **Step 2** — DynamoDB
  - Create `/infra/dynamodb.tf` — `aws_dynamodb_table.participants` (PAY_PER_REQUEST, hash_key=PK, range_key=SK, both String, PITR enabled only in prod)

- [x] **Step 3** — S3 bucket
  - Create `/infra/s3.tf` — `aws_s3_bucket.photos` (with account_id suffix), `aws_s3_bucket_public_access_block.photos` (all 4 blocks=true), `aws_s3_bucket_ownership_controls.photos` (BucketOwnerEnforced), `aws_s3_bucket_cors_configuration.photos` (allowed_origins = **var.cors_origins**, methods=[PUT], headers=["*"], max_age=3600)

- [x] **Step 4** — IAM (Lambda execution role)
  - Create `/infra/lambda.tf` (IAM section) — `aws_iam_role.lambda_exec` (trust = lambda.amazonaws.com), `aws_iam_role_policy.lambda_inline` with permissions:
    - DynamoDB: GetItem, PutItem, Query, Scan, UpdateItem, DeleteItem, BatchWriteItem, BatchGetItem, TransactWriteItems, TransactGetItems, DescribeTable (resources: table ARN + index/*)
    - S3: PutObject, GetObject, DeleteObject (bucket/*) + ListBucket, GetBucketLocation (bucket)
    - Logs: CreateLogGroup, CreateLogStream, PutLogEvents (log group ARN only)

- [x] **Step 5** — Lambda function & log group
  - Create `/infra/lambda.tf` (function section) — `aws_lambda_function.api` (nodejs22.x, handler=index.handler, memory/timeout from vars, filename=dummy.zip)
  - Environment variables: DYNAMODB_TABLE_NAME, S3_BUCKET_NAME, ADMIN_TOKEN, NEW_RELIC_LICENSE_KEY, **CORS_ORIGINS=join(",", var.cors_origins)**, SESSION_CODE, NODE_OPTIONS="--enable-source-maps"
  - `aws_cloudwatch_log_group.lambda` (retention = var.log_retention_days)
  - `aws_lambda_permission.apigw` (allow API GW to invoke)

- [x] **Step 6** — API Gateway HTTP API v2
  - Create `/infra/api-gateway.tf`:
    - `aws_apigatewayv2_api.api` with cors_configuration (allow_origins = **var.cors_origins**, methods=[GET,POST,DELETE,OPTIONS], headers=[Content-Type, Authorization, traceparent, tracestate], max_age=3600)
    - `aws_apigatewayv2_integration.lambda` (AWS_PROXY, payload_format=2.0, timeout=29s)
    - 8 routes via `for_each` over `local.routes`: GET /health, POST /upload-url, POST /join, GET /wall, POST /like, GET /leaderboard, POST /admin/sessions, DELETE /admin/sessions/{code}
    - `aws_apigatewayv2_stage.default` (auto_deploy=true, access_log_settings → CW log group, throttling default_route_settings)
    - Per-route throttling on `POST /join` and `POST /like`: burst_limit=5, rate_limit=5

- [x] **Step 7** — CloudWatch log groups & API GW logging role
  - Create `/infra/cloudwatch.tf`:
    - `aws_cloudwatch_log_group.apigw` (retention = var.log_retention_days)
    - `aws_iam_role.apigw_cloudwatch` (for API GW to write to CW)
    - `aws_iam_role_policy_attachment` for AWS managed policy `AmazonAPIGatewayPushToCloudWatchLogs`
    - `aws_api_gateway_account.this` (cloudwatch_role_arn)

- [x] **Step 8** — Default tfvars & environment files
  - Create `/infra/terraform.tfvars` (dev defaults — **cors_origins = ["http://localhost:3000"]**, environment="dev", session_code="LATAM2026")
  - Create `/infra/demo.tfvars.example` (template with Vercel demo URL + localhost)
  - Create `/infra/prod.tfvars.example` (template)

- [x] **Step 9** — Placeholder Lambda artifact & gitignore
  - Create `/infra/dummy.zip` (empty zip with `index.js` exporting `handler` returning 200) — used until backend deploy script overwrites it
  - Create `/infra/.gitignore` (`.terraform/`, `terraform.tfstate*`, `*.tfvars` except `.example`, `dummy.zip`, `.terraform.lock.hcl`)

- [x] **Step 10** — README & operational notes
  - Create `/infra/README.md` covering:
    - Deployment workflow (init/plan/apply/outputs)
    - tfvars selection (`-var-file=demo.tfvars`)
    - Troubleshooting #10 fallback: AWS CLI command to force CORS update if Terraform doesn't detect drift
    - Troubleshooting #15: env var bump pattern for cold start after IAM changes
    - Bootstrap order with frontend (#31)
    - Outputs map to backend/frontend deploy

- [x] **Step 11** — Validation
  - Run `terraform fmt -recursive` in `/infra` (no diffs expected)
  - Run `terraform init` (must succeed)
  - Run `terraform validate` (must return "configuration is valid")
  - Run `terraform plan -var-file=terraform.tfvars` (must succeed, no errors)
  - Document plan output (expected ~25 resources to add)

- [x] **Step 12** — Summary documentation
  - Create `aidlc-docs/construction/infra/code/summary.md` with:
    - List of files created with line counts
    - Validation results
    - Troubleshooting issues mitigated
    - Outputs reference for next units

## Expected File Layout
```
/infra/
├── main.tf
├── variables.tf
├── outputs.tf
├── dynamodb.tf
├── s3.tf
├── lambda.tf
├── api-gateway.tf
├── cloudwatch.tf
├── terraform.tfvars
├── demo.tfvars.example
├── prod.tfvars.example
├── dummy.zip
├── .gitignore
└── README.md
```

## Out of Scope (Deferred / Not in This Unit)
- Lambda code itself (handled by backend unit)
- Frontend deployment (Vercel, handled by frontend unit)
- S3 backend for tfstate (acceptable to use local backend for demo)
- CloudFront / WAF / Custom domain (not required by stories)
- Multi-region deployment (single region us-east-1 per design)

## Success Criteria
1. All 14 files generated with valid HCL
2. `terraform init && terraform validate && terraform plan` all succeed
3. `cors_origins` is `list(string)` everywhere (no string usages)
4. No CORS headers managed in Lambda code (truth = API Gateway)
5. IAM policy includes all DynamoDB + S3 + CW actions required by backend
6. Plan output shows ~25 resources additions, 0 changes, 0 destroys

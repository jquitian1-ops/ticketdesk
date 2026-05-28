# SkillWall Live — Infrastructure (Terraform)

Terraform module that provisions all AWS resources for SkillWall Live in `us-east-1`.

## Resources Provisioned (~25)
- **API Gateway HTTP API v2** with 8 routes, CORS, per-route throttling (5 TPS on `POST /join` and `POST /like`)
- **Lambda** (Node.js 22, 256 MB, 30s timeout) — code uploaded by `backend/scripts/deploy.sh`
- **DynamoDB** table `skillwall-{env}-participants` (PK/SK, on-demand)
- **S3** bucket for photo uploads (private, ownership BucketOwnerEnforced, CORS for pre-signed PUT)
- **IAM** execution role for Lambda + role for API Gateway → CloudWatch logging
- **CloudWatch** log groups for Lambda + API Gateway access logs

## Prerequisites
- Terraform >= 1.5
- AWS CLI configured (`aws configure`)
- `dummy.zip` placeholder exists alongside `main.tf`

## Deployment Workflow

```bash
cd infra

terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
terraform output
```

Outputs of interest:
- `api_gateway_url` — exported to frontend as `NEXT_PUBLIC_API_URL`
- `lambda_function_name` — used by `backend/scripts/deploy.sh`
- `dynamodb_table_name`, `s3_bucket_name` — wired to Lambda env automatically

## Variables Reference

| Variable | Type | Default | Notes |
|---|---|---|---|
| `environment` | string | `"dev"` | `dev`, `demo`, `prod` |
| `aws_region` | string | `"us-east-1"` | Single-region |
| `cors_origins` | list(string) | `["http://localhost:3000"]` | **Always a list** — see Troubleshooting #21 |
| `admin_token` | string (sensitive) | — | Required; protects `/admin/*` |
| `new_relic_license_key` | string (sensitive) | `""` | Optional; OTLP export |
| `session_code` | string | `"LATAM2026"` | Default session code |
| `lambda_memory` | number | `256` | MB |
| `lambda_timeout` | number | `30` | Seconds |
| `log_retention_days` | number | `7` | CloudWatch retention |

## Bootstrap order (troubleshooting #31)

First deploy E2E (greenfield) has a CORS chicken-and-egg with the Vercel URL:

```bash
# 1. Apply infra with localhost-only CORS
terraform apply -var-file=terraform.tfvars

# 2. Deploy backend (Lambda code)
cd ../backend && ./scripts/deploy.sh

# 3. Seed session (troubleshooting #32 — /join returns 404 without it)
curl -X POST $(cd ../infra && terraform output -raw api_gateway_url)admin/sessions \
  -H 'Content-Type: application/json' \
  -d '{"adminToken":"<admin_token>","sessionCode":"LATAM2026"}'

# 4. Deploy frontend to Vercel → capture URL
cd ../frontend
./scripts/env-add.sh NEXT_PUBLIC_API_URL "$(cd ../infra && terraform output -raw api_gateway_url | sed 's:/*$::')"
./scripts/env-add.sh NEXT_PUBLIC_SESSION_CODE LATAM2026
vercel --prod --yes
# → https://<project>.vercel.app

# 5. Add Vercel URL to cors_origins and re-apply
cd ../infra
# edit terraform.tfvars: cors_origins = ["https://<project>.vercel.app", "http://localhost:3000"]
terraform apply -var-file=terraform.tfvars
```

## Troubleshooting

### #10 — CORS update isn't detected by `terraform apply`
Force update via AWS CLI when Terraform doesn't detect drift:

```bash
aws apigatewayv2 update-api \
  --api-id $(terraform output -raw api_gateway_id) \
  --cors-configuration AllowOrigins=https://my-app.vercel.app,http://localhost:3000,AllowMethods=GET,POST,DELETE,OPTIONS,AllowHeaders=Content-Type,Authorization,traceparent,tracestate,MaxAge=3600
```

Then `terraform refresh` to sync state.

### #15 — IAM change requires Lambda cold start
After modifying IAM policy, force cold start by bumping any env var:

```bash
aws lambda update-function-configuration \
  --function-name $(terraform output -raw lambda_function_name) \
  --environment 'Variables={DEPLOY_TIMESTAMP='$(date +%s)',DYNAMODB_TABLE_NAME=...}'
```

Or re-run `backend/scripts/deploy.sh` — it does this automatically.

### #20 / #4 — CORS truth lives in API Gateway
Never set `Access-Control-Allow-Origin` headers in Lambda responses for HTTP API v2. API Gateway overwrites them and may cause duplicate-header errors.

### #21 — `cors_origins` is `list(string)`
Already applied. `var.cors_origins` is used directly in `aws_apigatewayv2_api.cors_configuration` and `aws_s3_bucket_cors_configuration`. For runtime use, the Lambda env var is `join(",", var.cors_origins)`.

## State Management
- Backend: local (default). `terraform.tfstate` is gitignored.
- For team/prod use, switch to S3 + DynamoDB locking.

## Cleanup
```bash
terraform destroy -var-file=terraform.tfvars
```

Note: `aws_api_gateway_account` is account-level and only removed from state. To reset the cloudwatch role manually:
```bash
aws apigateway update-account --patch-operations 'op=replace,path=/cloudwatchRoleArn,value='
```

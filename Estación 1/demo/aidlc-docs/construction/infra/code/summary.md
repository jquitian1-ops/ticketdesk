# Code Generation Summary — Unit: infra (Cohorte2)

**Timestamp**: 2026-05-11
**Branch**: cohorte2
**Workspace**: `/home/andrescaicedom/git/intro30x/infra/`

## Files Generated

| File | Lines | Purpose |
|---|---|---|
| `main.tf` | 27 | terraform block, AWS provider, default tags, account/region data sources |
| `variables.tf` | 62 | 9 input variables (`cors_origins` as `list(string)` — #21) |
| `outputs.tf` | 39 | 8 outputs (API URL, Lambda, DynamoDB, S3) |
| `dynamodb.tf` | 20 | `participants` table (PK/SK, PAY_PER_REQUEST, PITR in prod) |
| `s3.tf` | 33 | photos bucket + public access block + ownership controls + CORS |
| `lambda.tf` | 131 | IAM exec role + inline policy + log group + function + apigw permission |
| `api-gateway.tf` | 100 | HTTP API v2, integration, 8 routes (`for_each`), stage with access logs + throttling |
| `cloudwatch.tf` | 38 | API GW access log group + apigw→CW IAM role + account setting |
| `terraform.tfvars` | 11 | Dev defaults |
| `demo.tfvars.example` | 10 | Demo template |
| `prod.tfvars.example` | 10 | Prod template |
| `.gitignore` | 15 | Excludes state, lock, local tfvars, dummy.zip |
| `README.md` | 119 | Deploy workflow + bootstrap order + troubleshooting playbook |
| `dummy.zip` | (binary) | Placeholder Lambda code (340 bytes) |

**Total**: 14 files, 615 lines of HCL/markdown + 1 binary artifact

## Validation Results

| Check | Result |
|---|---|
| `terraform fmt -recursive` | ✅ Clean (no diffs) |
| `terraform init` | ✅ AWS provider installed |
| `terraform validate` | ✅ Success! The configuration is valid. |
| `terraform plan` (dev tfvars) | ✅ **Plan: 25 to add, 0 to change, 0 to destroy** |

## Resources to Be Created (25)

- 1× `aws_apigatewayv2_api`
- 1× `aws_apigatewayv2_integration`
- 8× `aws_apigatewayv2_route` (`for_each` over `local.routes`)
- 1× `aws_apigatewayv2_stage`
- 1× `aws_api_gateway_account`
- 1× `aws_lambda_function`
- 1× `aws_lambda_permission`
- 2× `aws_iam_role` (lambda_exec, apigw_cloudwatch)
- 1× `aws_iam_role_policy` (lambda inline)
- 1× `aws_iam_role_policy_attachment` (apigw managed policy)
- 2× `aws_cloudwatch_log_group` (lambda, apigw)
- 1× `aws_dynamodb_table`
- 1× `aws_s3_bucket`
- 1× `aws_s3_bucket_public_access_block`
- 1× `aws_s3_bucket_ownership_controls`
- 1× `aws_s3_bucket_cors_configuration`

## Troubleshooting Issues Mitigated From Start

| # | Mitigation in code |
|---|---|
| **#3** ✅ | `lambda.tf` IAM policy includes `DescribeTable`, `TransactWriteItems`, `BatchWriteItem`, `Query`, `Scan`, plus transact and batch variants |
| **#10** ✅ | `README.md` documents AWS CLI fallback to force CORS update when Terraform doesn't detect drift |
| **#15** ✅ | `README.md` documents env-var bump pattern for cold start after IAM changes |
| **#20** ✅ | CORS only in `aws_apigatewayv2_api.cors_configuration`; explicit comment warns against duplicating in Lambda |
| **#21** ✅ | `cors_origins` is `list(string)` in `variables.tf`, used as-is in API GW and S3 CORS, joined to comma string for Lambda env |
| **#31** ✅ | `README.md` includes bootstrap order section for greenfield first deploy |

## Outputs Reference (Consumed by Other Units)

```bash
terraform output -raw api_gateway_url       # → frontend NEXT_PUBLIC_API_URL
terraform output -raw lambda_function_name  # → backend deploy.sh
terraform output -raw dynamodb_table_name   # → already wired to Lambda env
terraform output -raw s3_bucket_name        # → already wired to Lambda env
```

## Next Steps
1. Approve completion of infra unit (Option 2 — Continue to Next Stage)
2. Proceed to **backend unit** code generation (Code Generation Part 1: Planning)
3. After backend, deploy infra (`terraform apply`) and backend (`./scripts/deploy.sh`), then continue to frontend

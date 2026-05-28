#!/usr/bin/env bash
#
# Deploy SkillWall backend Lambda code without running full terraform apply.
#
# Troubleshooting #15: After modifying IAM in infra unit, the running Lambda may
# keep cached credentials. Bump DEPLOY_TIMESTAMP env var on every deploy to
# force a fresh execution context.
#
# Troubleshooting #22: User's ~/.aws/config might have a broken `output=` line.
# Export AWS_DEFAULT_OUTPUT=json to immunize the script.
#
# Troubleshooting #23: AWS CLI v1 does NOT support --no-cli-pager. Do not use it.
#
# Troubleshooting #24: `--environment "Variables={...}"` shorthand fails when the
# JSON value has quotes. Use `file://path.json` instead.
#
# Usage:
#   ./scripts/deploy.sh                # uses skillwall-dev-api by default
#   ./scripts/deploy.sh --env demo     # → skillwall-demo-api
#
set -euo pipefail

export AWS_DEFAULT_OUTPUT="json"

ENV="dev"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      ENV="$2"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

FUNCTION_NAME="skillwall-${ENV}-api"
REGION="${AWS_REGION:-us-east-1}"

cd "$(dirname "$0")/.."

echo "==> Installing dependencies (npm ci)"
npm ci --silent

echo "==> Building bundle (esbuild → dist/index.js)"
npm run build

echo "==> Packaging function.zip"
rm -f function.zip
cd dist
zip -q -r ../function.zip index.js index.js.map
cd ..

echo "==> Updating Lambda function code: ${FUNCTION_NAME} in ${REGION}"
aws lambda update-function-code \
  --function-name "${FUNCTION_NAME}" \
  --zip-file fileb://function.zip \
  --region "${REGION}" \
  > /dev/null

aws lambda wait function-updated \
  --function-name "${FUNCTION_NAME}" \
  --region "${REGION}"

echo "==> Bumping DEPLOY_TIMESTAMP env var (troubleshooting #15)"
# Use a JSON file to avoid shorthand parsing issues (troubleshooting #24).
ENV_JSON_FILE=$(mktemp /tmp/lambda-env.XXXXXX.json)
trap 'rm -f "${ENV_JSON_FILE}"' EXIT

aws lambda get-function-configuration \
  --function-name "${FUNCTION_NAME}" \
  --region "${REGION}" \
  --query 'Environment.Variables' \
  --output json \
  | jq --arg ts "$(date +%s)" '{Variables: (. + {DEPLOY_TIMESTAMP: $ts})}' \
  > "${ENV_JSON_FILE}"

aws lambda update-function-configuration \
  --function-name "${FUNCTION_NAME}" \
  --environment "file://${ENV_JSON_FILE}" \
  --region "${REGION}" \
  > /dev/null

aws lambda wait function-updated \
  --function-name "${FUNCTION_NAME}" \
  --region "${REGION}"

echo "==> Deploy complete: ${FUNCTION_NAME}"

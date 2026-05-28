#!/usr/bin/env bash
#
# Seed the initial session in DynamoDB via the /admin/sessions endpoint.
#
# Troubleshooting #32: /join returns 404 if the SESSION#<code>/METADATA item
# doesn't exist. The first operational step after terraform apply + backend deploy
# is to seed at least one session, otherwise the frontend appears broken
# ("Session not found" on every join attempt).
#
# Usage:
#   ./scripts/seed-session.sh              # seeds LATAM2026
#   ./scripts/seed-session.sh DEMO2026     # custom code
#
set -euo pipefail
export AWS_DEFAULT_OUTPUT=json

SESSION_CODE="${1:-LATAM2026}"

INFRA_DIR="$(cd "$(dirname "$0")/../../infra" && pwd)"
API_URL=$(cd "${INFRA_DIR}" && terraform output -raw api_gateway_url | sed 's:/*$::')
ADMIN_TOKEN=$(cd "${INFRA_DIR}" && grep '^admin_token' terraform.tfvars | sed 's/.*= *"\(.*\)"/\1/')

if [[ "${ADMIN_TOKEN}" == "REPLACE_ME" || -z "${ADMIN_TOKEN}" ]]; then
  echo "Error: admin_token is REPLACE_ME or empty in infra/terraform.tfvars" >&2
  echo "Set it to a real value before seeding (re-run terraform apply afterwards)." >&2
  exit 1
fi

echo "==> Seeding session ${SESSION_CODE} via ${API_URL}/admin/sessions"
RESPONSE=$(curl -sS -X POST "${API_URL}/admin/sessions" \
  -H 'Content-Type: application/json' \
  -d "{\"adminToken\":\"${ADMIN_TOKEN}\",\"sessionCode\":\"${SESSION_CODE}\"}" \
  -w "\nHTTP_STATUS:%{http_code}")

STATUS=$(echo "${RESPONSE}" | grep '^HTTP_STATUS:' | cut -d':' -f2)
BODY=$(echo "${RESPONSE}" | sed '/^HTTP_STATUS:/d')

echo "${BODY}"
echo "Status: ${STATUS}"

if [[ "${STATUS}" == "201" ]]; then
  echo "==> Session ${SESSION_CODE} seeded successfully"
elif [[ "${STATUS}" == "409" ]]; then
  echo "==> Session ${SESSION_CODE} already exists (no-op)"
else
  echo "==> Seed failed with HTTP ${STATUS}" >&2
  exit 1
fi

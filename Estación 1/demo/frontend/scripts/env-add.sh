#!/usr/bin/env bash
#
# Add or replace a Vercel environment variable safely.
#
# Troubleshooting #5: NEVER pipe `echo` to `vercel env add` — `echo` appends
# a trailing newline that gets baked into the JS bundle and breaks comparisons.
#
# Troubleshooting #6: NEXT_PUBLIC_* vars are inlined at build time. Use
# `vercel env add` (persisted) NOT `vercel deploy -e` (ephemeral).
#
# Troubleshooting #19: Always verify the value AFTER setting it, then redeploy.
#
# Usage:
#   ./scripts/env-add.sh NEXT_PUBLIC_API_URL https://6svkxadr3h.execute-api.us-east-1.amazonaws.com
#   ./scripts/env-add.sh NEXT_PUBLIC_SESSION_CODE LATAM2026
#
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 KEY VALUE [environment]" >&2
  echo "  environment defaults to 'production'" >&2
  exit 1
fi

KEY="$1"
VALUE="$2"
ENV="${3:-production}"

if ! command -v vercel >/dev/null 2>&1; then
  echo "Error: vercel CLI not found. Install with: npm i -g vercel" >&2
  exit 1
fi

# Remove existing value (idempotent — ignores "not found")
vercel env rm "${KEY}" "${ENV}" --yes >/dev/null 2>&1 || true

# Add with printf so no trailing newline is written
printf '%s' "${VALUE}" | vercel env add "${KEY}" "${ENV}"

echo "✓ ${KEY}=${VALUE} (env: ${ENV})"
echo "Run 'vercel --prod --yes' to deploy with the new value."

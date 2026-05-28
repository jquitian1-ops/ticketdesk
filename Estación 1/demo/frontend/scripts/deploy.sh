#!/usr/bin/env bash
#
# Deploy SkillWall frontend to Vercel production.
#
# Prerequisites:
#   - vercel CLI installed and authenticated (`vercel login`)
#   - Project linked (`vercel link`)
#   - Env vars set via ./scripts/env-add.sh (NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SESSION_CODE)
#
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v vercel >/dev/null 2>&1; then
  echo "Error: vercel CLI not found. Install with: npm i -g vercel" >&2
  exit 1
fi

echo "==> Listing current production env vars (verify before deploying — troubleshooting #19)"
vercel env ls production || true

echo ""
echo "==> Building locally to surface errors before pushing"
npm run build

echo ""
echo "==> Deploying to production"
vercel --prod --yes

echo ""
echo "==> Deploy complete. Verify the live API URL embedded in the JS bundle:"
echo "    1. Open the production URL in a browser"
echo "    2. DevTools → Network → confirm /wall request hits the correct API Gateway"
echo "    3. If it points at a stale URL, re-run ./scripts/env-add.sh and redeploy"
echo "       (NEXT_PUBLIC_* are build-time inlined per troubleshooting #6)"

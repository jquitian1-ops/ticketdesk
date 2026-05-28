# SkillWall Live — Frontend (Next.js)

Next.js 15 (App Router) + Tailwind 4 + TypeScript frontend for SkillWall Live. Deploys to Vercel.

## Stack
- **Next.js 15** with App Router and Turbopack dev server
- **React 19**
- **Tailwind CSS 4** (CSS-first config, `@theme` block in `globals.css`)
- **TypeScript** strict mode
- **lucide-react** for icons

## Local development

```bash
# 1. Install (see Tailwind oxide note below if it fails)
npm install

# 2. Copy env template
cp .env.local.example .env.local
# Edit .env.local to point NEXT_PUBLIC_API_URL at your dev API

# 3. Run dev server
npm run dev
# → http://localhost:3000
```

### Tailwind 4 native binding (troubleshooting #27)

If `npm run build` fails with `Cannot find native binding`, install the platform package explicitly:

```bash
# Linux glibc x64 (Ubuntu, Debian, Fedora)
npm install @tailwindcss/oxide-linux-x64-gnu --no-save

# macOS Apple Silicon
npm install @tailwindcss/oxide-darwin-arm64 --no-save

# Linux Alpine (musl)
npm install @tailwindcss/oxide-linux-x64-musl --no-save
```

This is a known npm optional-deps bug.

## Scripts
| Script | Purpose |
|---|---|
| `npm run dev` | Local dev server (Turbopack) |
| `npm run build` | Production build (`.next/`) |
| `npm run start` | Run the production build locally |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run lint` | ESLint |

## Vercel deployment

> ⚠️ `NEXT_PUBLIC_*` env vars are **inlined at build time**. Setting them via `vercel deploy -e` is ephemeral; you must `vercel env add` and redeploy.

### One-time setup
```bash
vercel login
vercel link   # link this directory to a Vercel project
```

### Set env vars (per environment)

Use the helper script — it handles all known footguns (troubleshooting #5, #6, #19):

```bash
# Production
./scripts/env-add.sh NEXT_PUBLIC_API_URL https://6svkxadr3h.execute-api.us-east-1.amazonaws.com
./scripts/env-add.sh NEXT_PUBLIC_SESSION_CODE LATAM2026
```

The script:
1. Removes any existing value (no orphaned older versions)
2. Pipes the value with `printf` (**not `echo`**)
3. Adds the var via `vercel env add` (persisted across deploys)

### Deploy

```bash
./scripts/deploy.sh
```

The deploy script:
1. Lists current env vars so you can verify before pushing (troubleshooting #19)
2. Runs a local `next build` first to surface errors fast
3. Pushes to production via `vercel --prod --yes`

### Verifying the deployed bundle (troubleshooting #19)

After deploying:
1. Open the production URL.
2. DevTools → Network. Trigger a wall fetch.
3. Confirm it hits the correct API Gateway origin.
4. If stale, re-run `./scripts/env-add.sh NEXT_PUBLIC_API_URL <correct-url>` and redeploy.

### Bootstrap order on first deploy (troubleshooting #31)

The Vercel URL doesn't exist until after the first `vercel --prod`. The flow:

```bash
# 1. Backend/infra apply already done; API Gateway URL exists.
# 2. Configure env vars and deploy to Vercel for the first time.
./scripts/env-add.sh NEXT_PUBLIC_API_URL "$(cd ../infra && terraform output -raw api_gateway_url | sed 's:/*$::')"
./scripts/env-add.sh NEXT_PUBLIC_SESSION_CODE LATAM2026
vercel --prod --yes
# → https://<project>.vercel.app

# 3. Add the Vercel URL to infra cors_origins and re-apply terraform.
cd ../infra
# edit terraform.tfvars:
#   cors_origins = ["https://<project>.vercel.app", "http://localhost:3000"]
terraform apply -var-file=terraform.tfvars
# → API Gateway, S3 CORS, and Lambda CORS_ORIGINS env all aligned in one apply (#21)
```

## Architecture notes

### Trailing slash sanitization (troubleshooting #14)
Terraform exposes the API URL with a trailing slash (`https://x.execute-api.../`). `lib/api.ts` strips it defensively:

```typescript
export const API_BASE = RAW_BASE.replace(/\s+/g, "").replace(/\/+$/, "");
```

So `/join` always resolves to `https://x.execute-api.../join`, never `//join`.

### CSP from env vars (troubleshooting #16)
`next.config.ts` reads `NEXT_PUBLIC_API_URL` to build `connect-src` dynamically — there is **no hardcoded gateway ID anywhere**. A CSP that doesn't match the runtime API URL silently blocks fetches in WebKit (impossible to diagnose without this fix).

### `<img>` instead of `next/image` (troubleshooting #30)
S3 pre-signed URLs include credentials in the query string and have a 1h validity. Passing them through `next/image` (which caches in the Vercel optimizer) breaks signatures and can leak credentials. We use `<img>` with `onError` fallback to a local default avatar.

### Security headers
Set globally via `next.config.ts → headers()`:
- `Content-Security-Policy` (dynamic, see above)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

### State management
No global store. Pages own their state via `useState`/`useCallback`. Identity persists in `localStorage` under keys `skillwall_participantId` and `skillwall_sessionCode`. Wall + Leaderboard poll every 2 s via `setInterval`.

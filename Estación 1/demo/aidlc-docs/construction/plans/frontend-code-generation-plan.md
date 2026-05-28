# Code Generation Plan — Unit: frontend (Cohorte2)

## Unit Context
- **Cohort**: cohorte2 (live execution — hardcoreAI opening)
- **Unit**: frontend
- **Directory**: `/frontend` (will be created at workspace root)
- **Type**: Next.js 15 (App Router, TypeScript strict) + Tailwind 4 + React 19
- **Stories Referenced**: US-01..US-07 (functional UX)
- **Dependencies**: infra (provides `api_gateway_url`) + backend (deployed, API responding)
- **Deploy target**: Vercel

## Live API to Consume
**API Gateway**: `https://6svkxadr3h.execute-api.us-east-1.amazonaws.com/` (trailing slash → must strip per #14)
- Session ya seedeada (`LATAM2026`) con 2 participantes de prueba
- CORS allow_origins actual: `["http://localhost:3000"]` — para que el deploy de Vercel funcione, **después del primer deploy** hay que actualizar `cors_origins` y re-aplicar (bootstrap order #31)

## Design References (Do NOT Regenerate)
- `aidlc-docs/construction/frontend/functional-design/business-logic-model.md`
- `aidlc-docs/construction/frontend/functional-design/business-rules.md`
- `aidlc-docs/construction/frontend/functional-design/domain-entities.md`
- `aidlc-docs/construction/frontend/functional-design/frontend-components.md`
- `aidlc-docs/construction/frontend/infrastructure-design/infrastructure-design.md`
- `aidlc-docs/construction/frontend/infrastructure-design/deployment-architecture.md`

## Troubleshooting Lessons Applied From Start

| # | Issue | Application in cohorte2 frontend |
|---|-------|----------------------------------|
| **#5** 🔴 | Vercel env vars with newline | `scripts/env-add.sh` uses `printf '%s'` (never `echo`) |
| **#6** 🔴 | `NEXT_PUBLIC_*` are build-time only | README explicit: `vercel env add` (not `-e`) + redeploy mandatory |
| **#14** ✅ | API URL trailing slash | `lib/api.ts`: `API_BASE.replace(/\s+/g, "").replace(/\/+$/, "")` |
| **#16** 🔴 | CSP hardcoded blocks WebKit | `next.config.ts` reads `NEXT_PUBLIC_API_URL`, parses via `new URL()`, injects `.origin` into `connect-src`. Zero hardcoded gateway IDs |
| **#19** 🔴 | Wrong Vercel env var | `scripts/env-add.sh` does `vercel env rm` first (idempotent); `scripts/deploy.sh` lists env vars before pushing |
| **#27** 🔴 | Tailwind 4 native binding | README documents `npm install @tailwindcss/oxide-linux-x64-gnu --no-save` fallback if oxide native binding missing |
| **#28** ⚠️ | Next 16 requires Node 22+ | Use Next 15.5.x to work with Node 18 locally; Vercel respects `engines.node` |
| **#29** ⚠️ | ESLint flat config ignores | `eslint.config.mjs` includes explicit `{ ignores: [...] }` block |
| **#30** 📌 | `<img>` vs `next/image` with S3 presigned | Use `<img>` + onError fallback; disable `@next/next/no-img-element` |
| **#31** ✅ | CORS bootstrap order | README documents post-deploy `terraform apply` with Vercel URL added to `cors_origins` |

## Code Generation Steps

- [x] **Step 1** — Project skeleton
  - `/frontend/package.json` (Next.js 15, React 19, Tailwind 4, lucide-react, clsx, tailwind-merge)
  - `/frontend/tsconfig.json` (strict, paths alias `@/*`)
  - `/frontend/next.config.ts` — reads `NEXT_PUBLIC_API_URL` (cleaned) and builds CSP `connect-src` dynamically (#16); 5 security headers
  - `/frontend/postcss.config.mjs` (Tailwind 4 plugin)
  - `/frontend/eslint.config.mjs` — with `ignores` block (#29) and `@next/next/no-img-element` off (#30)
  - `/frontend/.gitignore`
  - `/frontend/.env.local.example` (template; no real values)

- [x] **Step 2** — Global styles & layout
  - `/frontend/src/app/globals.css` — Tailwind 4 `@import "tailwindcss"` + `@theme` block with design tokens
  - `/frontend/src/app/layout.tsx` — RootLayout with metadata, body
  - `/frontend/public/default-avatar.png` — 1×1 transparent placeholder

- [x] **Step 3** — Types and constants
  - `/frontend/src/types/index.ts` — synced with backend (Skill, Participant, LeaderEntry, SkillEntry, response types)
  - `/frontend/src/constants/skills.ts` — 15-skill catalog identical to backend

- [x] **Step 4** — Library: API client
  - `/frontend/src/lib/api.ts` — `API_BASE` with trailing slash stripped (#14), `SESSION_CODE`, `ApiError` class. Functions: `getUploadUrl`, `uploadToS3`, `joinSession`, `getWall`, `getLeaderboard`, `likeSkill`. All requests include `traceparent` header

- [x] **Step 5** — Library: utilities
  - `/frontend/src/lib/storage.ts` — SSR-safe `getStored`/`setStored`/`clearStored`/`getRegistration`/`setRegistration` (localStorage keys: `skillwall_participantId`, `skillwall_sessionCode`)
  - `/frontend/src/lib/utils.ts` — `cn()` helper (clsx + tailwind-merge)
  - `/frontend/src/lib/trace.ts` — W3C `traceparent` generator using `crypto.getRandomValues`

- [x] **Step 6** — Reusable UI components
  - `/frontend/src/components/skill-chip.tsx` — Modes: `select` (toggle for join form) + `like` (with heart icon + count)
  - `/frontend/src/components/participant-card.tsx` — Image with onError fallback to default avatar (#30); isSelf highlight (blue border, ribbon "(tú)")
  - `/frontend/src/components/leaderboard.tsx` — Two columns (Top Participantes + Top Skills) with empty state
  - `/frontend/src/components/join-form.tsx` — Form with displayName, skills (3–5), optional photo upload (≤2MB; jpeg/png/webp). Calls getUploadUrl→uploadToS3→joinSession

- [x] **Step 7** — Pages
  - `/frontend/src/app/page.tsx` — HomePage: check localStorage on mount → redirect /wall if registered, else JoinForm
  - `/frontend/src/app/wall/page.tsx` — WallPage: tabs (Wall/Leaderboard), sort toggle (new/top), polling `setInterval(2000ms)` on mount + cleanup on unmount, logout button

- [x] **Step 8** — Deploy scripts & README
  - `/frontend/scripts/env-add.sh` — Wrapper: `vercel env rm` then `printf | vercel env add` (#5, #6, #19)
  - `/frontend/scripts/deploy.sh` — Lists env vars before deploy (#19), runs local build first, then `vercel --prod --yes`
  - `/frontend/README.md` — Stack, scripts, Vercel deploy workflow, bootstrap order, troubleshooting

- [x] **Step 9** — Local validation
  - `cd frontend && npm install`
  - If Tailwind oxide native binding fails: `npm install @tailwindcss/oxide-linux-x64-gnu --no-save` (#27)
  - `npx tsc --noEmit` (must pass)
  - `npm run lint` (must be clean after ignores)
  - `npm run build` (must produce static `/` and `/wall`)

- [x] **Step 10** — Summary documentation
  - `aidlc-docs/construction/frontend/code/summary.md` — files, line counts, validation results, troubleshooting mitigations

## Expected File Layout
```
/frontend/
├── package.json
├── tsconfig.json
├── next.config.ts
├── postcss.config.mjs
├── eslint.config.mjs
├── .gitignore
├── .env.local.example
├── public/
│   └── default-avatar.png
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   ├── page.tsx           # Join
│   │   └── wall/page.tsx      # Wall + Leaderboard
│   ├── components/
│   │   ├── join-form.tsx
│   │   ├── skill-chip.tsx
│   │   ├── participant-card.tsx
│   │   └── leaderboard.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   ├── storage.ts
│   │   ├── trace.ts
│   │   └── utils.ts
│   ├── types/index.ts
│   └── constants/skills.ts
├── scripts/
│   ├── env-add.sh
│   └── deploy.sh
└── README.md
```

## Out of Scope (Deferred to Build & Test)
- E2E tests with Playwright (Build & Test phase: WebKit + retries for #11, #12, #17, #18)
- OTel browser SDK (only `traceparent` header forwarded for now)
- i18n (Spanish hardcoded per design)
- PWA / offline

## Success Criteria
1. ~25 files generated with valid TS/JSX
2. `npm install` succeeds (with native-binding fallback documented)
3. `npx tsc --noEmit` → 0 errors
4. `npm run lint` → clean
5. `npm run build` → static output for `/` and `/wall` (first-load JS ~113 KB)
6. `next.config.ts` reads CSP `connect-src` from env (no hardcoded API URL)
7. `lib/api.ts` strips trailing slash defensively
8. README documents `printf | vercel env add` flow + Tailwind native binding fix

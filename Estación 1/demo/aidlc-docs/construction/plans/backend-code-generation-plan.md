# Code Generation Plan — Unit: backend (Cohorte2)

## Unit Context
- **Cohort**: cohorte2 (live execution — hardcoreAI opening)
- **Unit**: backend
- **Directory**: `/backend` (will be created at workspace root)
- **Type**: Node.js 22 (TypeScript → esbuild → CJS bundle)
- **Stories Referenced**: US-01..US-07 (functional), TS-02 (OTel), TS-03 (Security)
- **Dependencies**: infra unit (DynamoDB table, S3 bucket, Lambda function provisioned)
- **Outputs consumed by**: API Gateway (Lambda code), frontend (HTTP contract)

## Design References (Do NOT Regenerate)
- `aidlc-docs/construction/backend/functional-design/business-logic-model.md` — 8 handlers spec
- `aidlc-docs/construction/backend/functional-design/business-rules.md` — Validation rules
- `aidlc-docs/construction/backend/functional-design/domain-entities.md` — DynamoDB schema + TS interfaces
- `aidlc-docs/construction/backend/infrastructure-design/infrastructure-design.md` — Lambda config + IAM
- `aidlc-docs/construction/backend/infrastructure-design/deployment-architecture.md` — Deploy workflow

## Troubleshooting Lessons Applied From Start

| # | Issue | Application in cohorte2 |
|---|-------|-------------------------|
| **#1** 🔴 | Lambda ESM vs CJS bundle | esbuild `format: 'cjs'`, `platform: 'node'`, `target: 'node22'`, output `dist/index.js` |
| **#2** 🔴 | API GW HTTP v2 base64-encoded body | `parseBody` decodes `event.body` when `event.isBase64Encoded === true` |
| **#7** 🔴 | Jest + Node 22 dynamic import crash | Mock `@aws-sdk/s3-request-presigner` at top of handler tests; use `jest.config.cjs` |
| **#8** 🔴 | Jest env var capture order | `tests/setup.ts` sets env vars BEFORE handler imports; `setupFiles` in jest.config |
| **#13** ✅ | photoObjectKey optional | Zod schema: `.optional().default("")` |
| **#15** ⚠️ | Cold start after IAM change | `deploy.sh` bumps `DEPLOY_TIMESTAMP` env var on every deploy |
| **#20** 🔴 | API GW v2 overrides Lambda CORS | Lambda response helper sets only `Content-Type` — NEVER CORS headers |
| **#23, #24** ✅ | AWS CLI v1 quirks in deploy.sh | No `--no-cli-pager`, use `file://` for `--environment` instead of shorthand |
| **#32** 🔴 | `/join` requires session seeded | `scripts/seed-session.sh` provided; README documents bootstrap step |

> **Note**: `business-rules.md` line 27 (cohorte1) says "Lambda adds CORS header". Cohorte2 overrides this per #20: **API Gateway is the only CORS authority**.

## Code Generation Steps

- [x] **Step 1** — Project setup
  - `/backend/package.json` (deps: aws-sdk v3, zod, uuid, otel; devDeps: typescript, esbuild, jest, ts-jest)
  - `/backend/tsconfig.json` (target ES2022, module CommonJS, strict, esModuleInterop)
  - `/backend/esbuild.config.mjs` (entry src/index.ts, bundle, format=cjs, platform=node, target=node22, output dist/index.js)
  - `/backend/jest.config.cjs` (preset ts-jest, testEnvironment node, setupFiles for env vars before module import)
  - `/backend/.gitignore`

- [x] **Step 2** — Types & constants
  - `/backend/src/types/index.ts` — `Skill`, `Participant`, `ParticipantRecord`, `SessionRecord`, `VoteRecord`, response types
  - `/backend/src/constants/skills.ts` — 15-skill catalog (ids '1'..'15')

- [x] **Step 3** — HTTP utilities
  - `/backend/src/http.ts` — `parseBody()` (decode base64 per #2), `json()` (no CORS headers per #20), `error()`, `getQuery()`, `getHeader()`, `getMethod()`, `getPath()`, `HttpError` class

- [x] **Step 4** — Middleware: Zod validation
  - `/backend/src/middleware/validation.ts` — Schemas for each route input (sessionCode, displayName, skills array 3–5, participantId UUID, photoObjectKey optional per #13, contentType enum, adminToken)

- [x] **Step 5** — Middleware: structured logger
  - `/backend/src/middleware/logger.ts` — JSON logger with `traceId` correlation. Events: SESSION_CREATED, SESSION_DELETED, JOIN_CREATED, LIKE_CAST, IDEMPOTENT_LIKE, VALIDATION_FAILED, etc.

- [x] **Step 6** — Middleware: OTel
  - `/backend/src/middleware/otel.ts` — OpenTelemetry NodeSDK init (OTLP/HTTP exporter to New Relic, no-op if `NEW_RELIC_LICENSE_KEY` empty)

- [x] **Step 7** — Services: DynamoDB
  - `/backend/src/services/dynamodb.ts` — DocumentClient singleton, methods: `getSession`, `putSession`, `deleteSession`, `getParticipant`, `putParticipant`, `queryParticipants`, `incrementSkillLike`, `batchDeleteSession`, `describeTable`. Apply #26 (no narrowing on `QueryCommandOutput.Items`, cast locally)

- [x] **Step 8** — Services: S3
  - `/backend/src/services/s3.ts` — `getUploadUrl(key, contentType)` (1h PUT), `getReadUrl(key)` (1h GET, empty key → "")

- [x] **Step 9** — Router
  - `/backend/src/router.ts` — Static map `method path → handler` + dynamic regex for `DELETE /admin/sessions/{code}`. 404 fallback

- [x] **Step 10** — Handlers (8 files in `src/handlers/`)
  - `health.ts` — `GET /health` (DescribeTable)
  - `upload-url.ts` — `POST /upload-url` (random objectKey, return presigned PUT)
  - `join.ts` — `POST /join` (validate, **verify session exists → 404 per #32**, UUID, putParticipant, return with photo URL)
  - `wall.ts` — `GET /wall` (query, sort by createdAt or totalLikes, signed URLs)
  - `like.ts` — `POST /like` (reject self-vote, verify voter, TransactWriteItems with conditional, idempotent on duplicate)
  - `leaderboard.ts` — `GET /leaderboard` (top 10 participants + top 10 skills)
  - `admin-create.ts` — `POST /admin/sessions` (validate adminToken, putSession, log SESSION_CREATED)
  - `admin-delete.ts` — `DELETE /admin/sessions/{code}` (token via body/header/auth/query, batchDelete, log SESSION_DELETED)

- [x] **Step 11** — Lambda entry point
  - `/backend/src/index.ts` — `exports.handler` = APIGatewayProxyHandlerV2. Init OTel, parse event, route, catch unhandled, log REQUEST_COMPLETED with traceId

- [x] **Step 12** — Deploy script & seed script
  - `/backend/scripts/deploy.sh` — `npm ci → npm run build → zip → aws lambda update-function-code → wait → bump DEPLOY_TIMESTAMP via file:// (per #15 + #24)`. Export `AWS_DEFAULT_OUTPUT=json` (per #22). No `--no-cli-pager` (per #23)
  - `/backend/scripts/seed-session.sh` — Reads api_gateway_url + admin_token from infra/, POSTs `/admin/sessions`. Documents #32.
  - Both made executable (`chmod +x`)

- [x] **Step 13** — Tests (3 suites)
  - `/backend/tests/setup.ts` — Sets env vars BEFORE handler imports (per #8)
  - `/backend/tests/validation.test.ts` — Zod schemas (22 tests targeting each rule)
  - `/backend/tests/handlers.test.ts` — Per-handler unit tests with mocked services + presigner (per #7)
  - `/backend/tests/integration.test.ts` — Router + Lambda handler entry; asserts no CORS headers in response (per #20)

- [x] **Step 14** — Build verification & summary
  - `cd backend && npm install`
  - `npx tsc --noEmit` (typecheck)
  - `npm run build` (esbuild → `dist/index.js`)
  - `npx jest` (full suite)
  - Create `aidlc-docs/construction/backend/code/summary.md`

## Expected File Layout
```
/backend/
├── package.json
├── tsconfig.json
├── esbuild.config.mjs
├── jest.config.cjs
├── .gitignore
├── src/
│   ├── index.ts                  # Lambda entry
│   ├── router.ts
│   ├── http.ts
│   ├── types/index.ts
│   ├── constants/skills.ts
│   ├── middleware/
│   │   ├── validation.ts
│   │   ├── logger.ts
│   │   └── otel.ts
│   ├── services/
│   │   ├── dynamodb.ts
│   │   └── s3.ts
│   └── handlers/
│       ├── health.ts
│       ├── upload-url.ts
│       ├── join.ts
│       ├── wall.ts
│       ├── like.ts
│       ├── leaderboard.ts
│       ├── admin-create.ts
│       └── admin-delete.ts
├── tests/
│   ├── setup.ts
│   ├── validation.test.ts
│   ├── handlers.test.ts
│   └── integration.test.ts
└── scripts/
    ├── deploy.sh
    └── seed-session.sh
```

## Out of Scope (Deferred)
- Real AWS calls in tests (integration tests use mocks; smoke tests via `aws lambda invoke` after deploy)
- WebSocket / long-poll (frontend uses HTTP polling per design)
- Multi-tenant auth (single admin token)
- Database migrations (single-table design)
- E2E tests (covered after all units deployed)

## Success Criteria
1. ~28 files generated with valid TypeScript
2. `npm install` succeeds
3. `npx tsc --noEmit` passes (0 errors)
4. `npm run build` produces `dist/index.js` (CJS bundle ~5MB)
5. `npx jest` passes all suites (~35 tests)
6. Troubleshooting #1, #2, #7, #8, #13, #15, #20, #23, #24, #32 all visible in code

# Phase 1 Production Readiness Checklist

**Milestone:** M8 — Final Production Acceptance and Demo Preparation  
**Scope:** Sari Arta single-workspace Phase 1 MVP  
**Decision:** Application acceptance baseline complete; production launch remains a separate human-approved deployment activity.

## Status meanings

- **Verified:** implemented and checked in the local acceptance environment.
- **Required at deployment:** implementation guard exists, but values or evidence depend on the selected production environment.
- **Deferred:** intentionally outside Phase 1 and not a production blocker for the approved MVP workflow.

## 1. Permissions and data access

| Check | Status | Evidence / required action |
|---|---|---|
| Protected APIs require an authenticated identity | Verified | FastAPI dependency enforcement and authorization tests |
| Roles are limited to `admin` and `sales` | Verified | Central permission map in `domain/identity.py` |
| Admin-only membership administration | Verified | Role-permission tests cover denial to ordinary sales users |
| Tenant-scoped business rows | Verified | PostgreSQL forced RLS policy inspection plus rejection of unowned workspace selection |
| Audit-event user access | Verified | Phase 1 does not expose audit records through an ordinary user API; direct operational access must remain restricted |
| Frontend has no direct database access | Verified | Next.js uses FastAPI service calls |
| Local demo authentication disabled in production | Verified | Production configuration rejects `DEVELOPMENT_AUTH_SUBJECT`; frontend checks environment |
| Production identity provider, MFA, and user lifecycle | Required at deployment | Configure the approved Supabase project, issuer, JWKS, access policy, and real users |

## 2. Agent runtime

| Check | Status | Evidence / required action |
|---|---|---|
| Durable run saved before queue delivery | Verified | PostgreSQL `agent_runs` record precedes Redis enqueue |
| Visible status and attempt metadata | Verified | queued/running/succeeded/failed/cancelled plus timestamps, attempts, heartbeat, and safe errors |
| Bounded exponential retries | Verified | Provider failures retry up to `AGENT_MAX_ATTEMPTS` |
| User cancellation | Verified | `POST /api/v1/agent-runs/{id}/cancellations`; late provider results are ignored |
| Worker interruption recovery | Verified | Periodic scan requeues stale queued/running durable runs; exhausted runs fail safely |
| Queue delivery idempotence | Verified | Executor locks the run and only starts `queued` work; duplicate messages cannot duplicate completion |
| CRM usable without AI | Verified | AI never owns lead status, opportunity conversion, tasks, or external actions |
| Real provider data policy | Required at deployment | Approve the data sent to OpenAI before setting `AI_ENABLED=true` |

## 3. Logging and audit

| Check | Status | Evidence / required action |
|---|---|---|
| Structured API and Worker logs | Verified | JSON logs include event, severity, timestamp, and correlation ID |
| Correlation ID validation/propagation | Verified | HTTP header → saved Agent Run → Worker context → response header |
| Safe AI failure messages | Verified | Provider exception details are logged operationally but not returned or saved as customer-facing error text |
| Business activity history | Verified | Lead changes, tasks, assessment review, conversion, and stage changes create append-only activities |
| Security audit records for Agent actions | Verified | Run request, cancellation, and assessment decision create `audit_events` with actor and request ID |
| Log aggregation, access control, alerting, and retention | Required at deployment | Select production logging destination and document operator access/retention |

## 4. Backup and restore

| Check | Status | Evidence / required action |
|---|---|---|
| Database backup command | Verified | `make backup` creates a private custom-format PostgreSQL dump under ignored `backups/` |
| Restore verification | Verified | `make verify-backup BACKUP_FILE=/absolute/path/file.dump` restores into an isolated temporary database and checks schema/tenant records |
| Backup encryption, remote copy, schedule, retention | Required at deployment | Configure managed encrypted backups and an off-host copy; assign an owner and retention period |
| Uploaded file backup | Deferred | Phase 1 has no production knowledge/proposal file workflow; add object-storage backup before Phase 2 files are enabled |
| Recovery objectives | Required at deployment | Business owner must approve RPO/RTO for the selected hosting environment |

## 5. Environment and deployment configuration

| Check | Status | Evidence / required action |
|---|---|---|
| Secrets excluded from source and example files | Verified | `.env.example` contains local-only placeholders; real `.env` is ignored |
| Unsafe local production values rejected | Verified | Settings reject localhost database/Redis, example auth endpoints, development identity, and default public token in production |
| AI key required only in real AI mode | Verified | `AI_ENABLED=true` requires `OPENAI_API_KEY` |
| Database and Redis health | Verified | Compose health checks plus API live/ready endpoints |
| Separate production services and secrets | Required at deployment | Provision managed PostgreSQL/Redis, TLS ingress, secret manager, DNS, and isolated production environment |
| Container image/security scanning | Required at deployment | Add registry scanning and a patch cadence when the hosting target is selected |

## 6. Acceptance evidence

- Backend lint and type checks pass.
- Qualification, retry, failure, cancellation, recovery, authorization, CRM, and opportunity tests pass.
- Frontend lint, type checks, component tests, and production build pass.
- Docker Compose configuration validates.
- Local database backup restores successfully into an isolated temporary database.
- Browser smoke test covers public homepage, local sign-in, dashboard, A/B/C assessments, and opportunity pipeline.
- The five-minute script can complete without OpenAI or real customer information.

## 7. Production launch gate

M8 acceptance does **not** authorize deployment. Before real customer use, the human owner must approve:

1. Hosting region, Supabase project, real users, and MFA policy.
2. Secrets, TLS, DNS, monitoring destination, alert owner, and retention.
3. Encrypted automated backup schedule plus recorded restore evidence.
4. Customer privacy/consent rules and data permitted to leave the environment.
5. Whether OpenAI mode remains disabled or is enabled under an approved processing policy.
6. A named rollback owner and launch window.

Phase 2 multi-domain agents remain explicitly out of scope until this production launch gate is addressed or the project owner separately authorizes Phase 2.

# Phase 1 Implementation Tasks

## Status and authority

**Project:** Enterprise AI Business Development Agent Platform  
**Reference business:** Sari Arta  
**Current phase:** Phase 1 — MVP  
**Current state:** Documentation complete; application implementation not started  
**Scope sources:** `docs/roadmap.md`, then `docs/mvp-scope.md`, then the enterprise design documents  
**Coding gate:** Do not begin M1 implementation until the project owner approves the plan.

## Next highest-priority milestone

### M1 — Runnable project foundation

**Objective:** Create a reproducible development environment in which the frontend, backend, PostgreSQL, and Redis start successfully and can be validated automatically.

This milestone comes first because every Phase 1 capability depends on a stable application structure, dependency policy, configuration model, database connectivity, and test commands. It intentionally does not implement CRM or AI business features.

### M1 tasks

| ID | Task | Deliverable | Acceptance evidence |
|---|---|---|---|
| FND-001 | Establish repository layout | `apps/web`, `apps/api`, infrastructure and documentation locations | Layout is documented and contains no duplicated application ownership |
| FND-002 | Pin runtime and package-manager policy | Node, Python and dependency-manager versions; lockfiles | Clean setup uses the documented versions and locked dependencies |
| FND-003 | Scaffold Next.js frontend | Strict TypeScript App Router shell with basic health/status page | Frontend lint, type check and production build pass |
| FND-004 | Scaffold FastAPI backend | Typed application shell with `/health/live` and `/health/ready` | API unit test and type/lint checks pass |
| FND-005 | Establish backend layering | Route, application, domain and adapter package boundaries | Dependency direction is documented and tested by import conventions |
| FND-006 | Create local service environment | Docker Compose for PostgreSQL and Redis plus application profiles | Services start, report healthy and persist development DB data |
| FND-007 | Define configuration and secrets policy | Validated settings, `.env.example`, safe development defaults | Missing required configuration fails safely; no secret is committed |
| FND-008 | Add database connectivity baseline | SQLAlchemy 2.x session/unit-of-work boundary and Alembic setup | API readiness check verifies DB connectivity; empty migration cycle succeeds |
| FND-009 | Add quality commands | Ruff, Python type checking, pytest, ESLint, TypeScript check and frontend tests | One documented command runs the local affected checks |
| FND-010 | Add CI baseline | Workflow for lint, types, tests and build without deployment | CI definition is syntax-valid and mirrors local validation |
| FND-011 | Add developer setup documentation | Prerequisites, startup, shutdown, validation and troubleshooting | A new developer can reach healthy frontend/API/services from the guide |

### M1 implementation decisions

- Use a monorepo with `apps/web` and `apps/api`; keep the worker in the Python application until asynchronous work begins.
- Use npm for the Next.js workspace unless scaffolding reveals a concrete limitation.
- Use a pinned modern Python version supported by all selected packages.
- Use SQLAlchemy 2.x and Alembic.
- Run PostgreSQL and Redis locally with Docker Compose.
- Keep Supabase Auth and managed PostgreSQL as the deployment baseline, but do not require paid or remote services to run M1 locally.
- Use synthetic configuration and test data only.
- Do not add n8n, object storage, pgvector workflows, OpenAI calls, or business tables in M1.

### M1 exit criteria

- A clean checkout can be configured using documented commands.
- Next.js, FastAPI, PostgreSQL, and Redis run locally.
- Frontend and API health are visible.
- The API readiness check detects database failure.
- Lint, type checks, unit tests and frontend build pass.
- No secrets, real customer data, production deployment or external messages are involved.

## Remaining Phase 1 milestones

### M2 — Identity and data foundation

**Depends on:** M1

- [ ] ID-001 Integrate Supabase Auth behind the FastAPI authentication boundary.
- [ ] ID-002 Validate issuer, audience, signature, expiry and subject for access tokens.
- [ ] ID-003 Implement seeded Sari Arta workspace and `admin`/`sales` membership.
- [ ] ID-004 Implement request identity and tenant context without trusting a client-selected tenant ID.
- [ ] DB-001 Create initial identity, CRM, task, agent-run and audit migrations.
- [ ] DB-002 Add foreign keys, state constraints, version fields and tenant-scoped indexes.
- [ ] DB-003 Add repository integration-test database and migration tests.
- [ ] SEC-001 Test unauthenticated, wrong-role and cross-workspace access denial.

**Exit:** Authenticated admin and sales users reach protected API operations with tested role and tenant enforcement.

### M3 — CRM lead vertical slice

**Depends on:** M2

- [ ] CRM-001 Implement organization create, read, update, list and search.
- [ ] CRM-002 Implement contact create, read, update, list and search.
- [ ] CRM-003 Implement authenticated manual lead creation.
- [ ] CRM-004 Implement lead list, filters, cursor pagination and detail.
- [ ] CRM-005 Implement version-protected lead editing, ownership, priority and status.
- [ ] CRM-006 Implement duplicate warnings by email, phone and company domain.
- [ ] CRM-007 Implement public inquiry endpoint with validation, idempotency and rate limiting.
- [ ] WEB-001 Build company, contact, lead-list and lead-detail interfaces.
- [ ] WEB-002 Add loading, empty, validation, conflict and safe-error states.
- [ ] TEST-001 Add API and end-to-end coverage for lead capture and management.

**Exit:** A user can capture and manage a lead entirely through the application, while duplicate retries and stale updates are handled safely.

### M4 — Tasks, activity and opportunity conversion

**Depends on:** M3

- [ ] WORK-001 Implement task create, assign, reschedule, complete and list.
- [ ] WORK-002 Implement manual notes and append-only activity history.
- [ ] WORK-003 Emit automatic activity events for important lead changes.
- [ ] OPP-001 Implement transactional qualified-lead conversion.
- [ ] OPP-002 Prevent duplicate conversion and reuse the existing company/contact.
- [ ] OPP-003 Implement opportunity list, detail and validated stage transitions.
- [ ] WEB-003 Add task, activity and opportunity interfaces.
- [ ] TEST-002 Test status transitions, conversion idempotency and transaction rollback.

**Exit:** A salesperson can plan follow-up, inspect history and convert a qualified lead without duplicating business records.

### M5 — Actionable dashboard

**Depends on:** M4

- [ ] DASH-001 Define dashboard aggregation queries.
- [ ] DASH-002 Show new/unassigned leads and qualification-review queue.
- [ ] DASH-003 Show overdue/upcoming tasks.
- [ ] DASH-004 Show lead counts and opportunity counts/value by stage.
- [ ] DASH-005 Show recent activity and links to filtered work lists.
- [ ] TEST-003 Validate dashboard totals against seeded records.

**Exit:** A salesperson can identify the next useful action from the dashboard.

### M6 — Asynchronous agent runtime

**Depends on:** M3; may proceed after the lead read model is stable

- [ ] RUN-001 Implement canonical PostgreSQL agent-run records.
- [ ] RUN-002 Add Redis-backed job enqueueing and worker execution.
- [ ] RUN-003 Implement queued/running/succeeded/failed/cancelled transitions.
- [ ] RUN-004 Add timeout, bounded retry, cancellation and correlation IDs.
- [ ] RUN-005 Add status API and frontend progress/retry view.
- [ ] RUN-006 Ensure Redis contains no unique business result.
- [ ] TEST-004 Test browser refresh, provider failure, worker retry and terminal-state behavior.

**Exit:** A synthetic job survives browser refresh, records its canonical state in PostgreSQL and fails safely.

### M7 — AI Lead Qualification Agent

**Depends on:** M6 and stable M3 lead data

- [ ] AI-001 Define versioned qualification instructions, rubric and structured output schema.
- [ ] AI-002 Implement narrow read-only tools for lead, company, contact, task and activity data.
- [ ] AI-003 Integrate the OpenAI Agents SDK through a small provider boundary.
- [ ] AI-004 Enforce time, token, tool-call and retry budgets.
- [ ] AI-005 Persist validated assessments and safe run metadata.
- [ ] AI-006 Implement accept, reject and rerun actions with human identity and timestamps.
- [ ] AI-007 Prevent AI output from changing lead status or creating external effects.
- [ ] AI-008 Build representative synthetic evaluation cases for hot, warm, cold and insufficient-data leads.
- [ ] WEB-004 Build qualification action, result, confidence, missing-data and review interfaces.
- [ ] TEST-005 Test schema validity, tool permissions, safe failure and human-control rules.

**Exit:** Representative leads produce reviewable structured results without automatic CRM state changes.

### M8 — Hardening and MVP demonstration

**Depends on:** M1–M7

- [ ] OPS-001 Add structured logging, redaction and correlation IDs across the critical path.
- [ ] OPS-002 Add health/readiness checks and operational troubleshooting guidance.
- [ ] OPS-003 Document and test PostgreSQL backup and restore.
- [ ] SEC-002 Complete Phase 1 authorization, rate-limit and input-abuse tests.
- [ ] AUD-001 Verify audit coverage for login and consequential CRM/AI actions.
- [ ] QA-001 Add the critical sign-in-to-conversion end-to-end test.
- [ ] DEMO-001 Create synthetic Sari Arta demonstration data.
- [ ] DEMO-002 Create a five-to-seven-minute repeatable demonstration script.
- [ ] DOC-001 Update roadmap checkboxes only for implemented and verified capabilities.

**Exit:** All Phase 1 acceptance criteria in `docs/roadmap.md` pass.

## Sequencing

```text
M1 Foundation
  → M2 Identity and data
  → M3 CRM lead slice
  → M4 Tasks and conversion
  → M5 Dashboard

M3 CRM lead slice
  → M6 Agent runtime
  → M7 Lead Qualification Agent

M4 + M5 + M7
  → M8 Hardening and demonstration
```

M5 and M6 may run in parallel only if more than one developer is available. For one developer, complete them in the listed order to maintain a usable non-AI system before adding AI.

## Approval checkpoint

Approval of this plan authorizes implementation of **M1 only**. It does not authorize:

- Access to real Sari Arta or customer data.
- Creation or purchase of Supabase/OpenAI production resources.
- Production deployment.
- External communication.
- Phase 2–4 implementation.
- Destructive operations, commits, pushes or publication.

At the end of M1, report validation evidence before beginning M2.

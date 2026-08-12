# Enterprise AI Business Development Agent Platform

AI-assisted lead management for Sari Arta, an Indonesian commercial-kitchen engineering business.

## Current delivery

**Phase 1 — MVP is accepted through M8.** M1–M6 deliver the runnable application,
identity/data foundation, CRM workflow, AI qualification, opportunity conversion, public
website, and sales workspace. M7–M8 complete the reliability and demonstration baseline with
durable Agent Run status, bounded retries, cancellation, interruption recovery, correlation
IDs, structured logs, safe failures, three synthetic acceptance scenarios, and verified local
backup/restore tooling. Phase 2 now includes an additive Agent Registry, a development-only IVC
qualification workflow, and a unified multi-domain Agent Playground; the accepted Phase 1 Sari Arta
runtime remains the operational baseline.

Phase 2.5 adds the deny-by-default Knowledge Foundation: tenant-scoped sources, explicit
domain/agent bindings, private document metadata, human approval, asynchronous PDF/text/Markdown
extraction, deterministic chunking, embedding-provider abstraction, pgvector retrieval, and complete
citation metadata. It returns evidence candidates only; no conversational Knowledge Assistant is
enabled, and IVC knowledge retrieval remains disabled.

M1 provides:

- A Next.js 16 frontend shell.
- A layered FastAPI backend.
- PostgreSQL and Redis local services.
- SQLAlchemy and Alembic migration foundations.
- Locked frontend and backend dependencies.
- Unit tests, linting, type checks and production builds.
- Docker images and Docker Compose orchestration.

M1 does not connect to Supabase, OpenAI, real customer data or production infrastructure.

M2 adds Supabase-compatible asymmetric JWT verification, protected identity APIs,
synthetic `admin` and `sales` memberships, core PostgreSQL business tables, tenant
row-security policies, and authorization/integration tests. It still uses no live
Supabase project or real customer data.

M3 adds authenticated company, contact, and lead management; optimistic concurrency;
duplicate warnings; a rate-limited, idempotent public inquiry endpoint; Supabase SSR
session support; and an operational Next.js sales workspace.

M4 adds follow-up tasks, append-only activity history, automatic lead-change events,
a Redis-backed qualification worker, OpenAI Agents SDK structured output, saved agent
runs and assessments, and explicit human acceptance or rejection. AI is disabled by
default and does not change lead status or perform external actions.

M5 adds transactional qualified-lead conversion, concurrent duplicate protection,
company/contact reuse, a staged opportunity pipeline, guarded stage transitions, and
automatic conversion/stage activity records.

M6 adds the responsive Sari Arta website and consultation flow, dashboard and lead detail
workspace, A/B/C qualification results, deterministic API-key-free demo qualification, and
the switchable OpenAI Agents SDK provider. Every assessment still requires human review.

M7 makes the workflow presentation-ready: Agent Runs persist attempt and retry metadata in
PostgreSQL, delayed retries travel through Redis, API and Worker logs use JSON with correlation
IDs, provider details are not exposed in saved failure messages, and `make demo-seed` loads
four realistic but entirely synthetic business scenarios.

M8 closes Phase 1 application acceptance: queued/running Agent Runs can be cancelled, the
Worker recovers stale durable runs after an interrupted attempt or lost queue delivery, critical
Agent actions write audit records, and the dataset includes Level A school, Level B hospital,
and Level C low-value inquiry outcomes. `make backup` and `make verify-backup` provide a
repeatable local restore check. Production deployment still requires the human launch gate in
`docs/production-readiness-checklist.md`.

The first Phase 2 framework increment adds versioned domain and agent registration, tenant-level
capability bindings and activation records, and localized registry metadata for English, Chinese,
and Bahasa Indonesia. Sari Arta is registered as the active `commercial_kitchen` domain. The
`laboratory_animal_facility` package now provides a development-only IVC qualification workflow,
three fully synthetic demo cases, and localized English, Chinese, and Bahasa Indonesia output. It
reuses durable Agent Runs and mandatory human review, but enables no knowledge retrieval, external
action, or production activation. Admins can inspect the registry through
`/api/v1/agent-registry/*`.

Phase 2.3 adds the authenticated `/agent-playground` page. Users can switch between the Commercial
Kitchen and IVC Facility agents, edit structured synthetic briefs, request English, Chinese, or
Bahasa Indonesia output, and compare normalized qualification results. Playground runs reuse the
durable Worker but do not create or alter CRM records. See
[Agent Playground](docs/agent-playground.md).

Phase 2.5.1 adds the authenticated `/knowledge` workspace and a tenant/domain-scoped knowledge
control plane. Administrators can create collections, upload synthetic or approved files, submit
exact versions for review, approve or reject them, bind them to a same-domain agent, and activate or
archive them. This management layer does not enable a conversational Knowledge Assistant or
automatically publish documents to vector retrieval. See the bilingual
[enterprise knowledge management design](docs/enterprise-knowledge-management-design.en.md).

## Repository layout

```text
apps/
├── web/                 Next.js application
└── api/                 FastAPI application and migrations
    ├── src/sari_api/
    │   ├── api/         HTTP routes and schemas
    │   ├── application/ Use cases and orchestration
    │   ├── domain/      Deterministic rules and models
    │   ├── adapters/    Database and external-system adapters
    │   └── core/        Configuration and cross-cutting concerns
    ├── migrations/
    └── tests/
docs/                    Architecture, scope, roadmap and task documents
.github/workflows/       Continuous integration
compose.yaml             Local services and application containers
Makefile                 Common development and validation commands
```

The frontend calls FastAPI for business behavior. PostgreSQL is the canonical data store.
Redis transports asynchronous jobs but holds no unique business state.

## Quick start

Read [Local Development](docs/development.md) for the complete setup.

After dependencies are installed:

```bash
cp .env.example .env
make services-up
make migrate
make demo-seed
make api-dev
```

In another terminal:

```bash
make web-dev
```

Open:

- Web: <http://localhost:3000>
- API liveness: <http://localhost:8000/health/live>
- API readiness: <http://localhost:8000/health/ready>
- Local API documentation: <http://localhost:8000/docs>

## Validation

Run the complete affected validation suite:

```bash
make check
```

This command runs backend lint, type checks and tests; frontend lint, type checks, tests and production build; and Docker Compose configuration validation.

Create and verify a local database backup:

```bash
make backup
make verify-backup BACKUP_FILE=/absolute/path/to/sariarta-YYYYMMDDTHHMMSSZ.dump
```

## Project documents

- [Documentation index](docs/README.md)
- [Project roadmap](docs/roadmap.md)
- [Phase 1 demo script](docs/demo-script.md)
- [Production readiness checklist](docs/production-readiness-checklist.md)
- [MVP scope](docs/mvp-scope.md)
- [Phase 1 tasks](docs/phase-1-tasks.md)
- [Technical architecture](docs/technical-architecture.en.md)
- [Knowledge foundation](docs/knowledge-foundation-design.en.md)
- [Development rules](AGENTS.md)

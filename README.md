# Enterprise AI Business Development Agent Platform

AI-assisted lead management for Sari Arta, an Indonesian commercial-kitchen engineering business.

## Current delivery

The project is in **Phase 1 — MVP**. **M1 — Runnable project foundation** and
**M2 — Identity and data foundation** are complete. The next milestone is the
CRM lead vertical slice.

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

The frontend calls FastAPI for business behavior. PostgreSQL is the canonical data store. Redis will support asynchronous jobs but holds no unique business state.

## Quick start

Read [Local Development](docs/development.md) for the complete setup.

After dependencies are installed:

```bash
cp .env.example .env
make services-up
make migrate
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

## Project documents

- [Documentation index](docs/README.md)
- [Project roadmap](docs/roadmap.md)
- [MVP scope](docs/mvp-scope.md)
- [Phase 1 tasks](docs/phase-1-tasks.md)
- [Technical architecture](docs/technical-architecture.md)
- [Development rules](AGENTS.md)

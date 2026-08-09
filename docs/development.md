# Local Development

## Prerequisites

- Node.js 24 and npm 11.
- Python 3.13.
- Docker Desktop with Docker Compose 2.
- GNU Make or a compatible `make` implementation.

The repository pins the Node and Python minor versions in `.nvmrc`, `.python-version`, package metadata and container images. Dependency lockfiles pin installable packages.

## 1. Configure the environment

From the repository root:

```bash
cp .env.example .env
```

The example values are local-only synthetic credentials. Do not reuse them outside a development machine.

## 2. Install frontend dependencies

```bash
npm --prefix apps/web ci
```

## 3. Install backend dependencies

Create an isolated environment and install the locked development set:

```bash
python3 -m venv apps/api/.venv
apps/api/.venv/bin/pip install --requirement apps/api/requirements-dev.lock
```

On a macOS Python.org installation that has not linked its certificate bundle, use the system CA file without disabling TLS verification:

```bash
SSL_CERT_FILE=/etc/ssl/cert.pem apps/api/.venv/bin/pip install --requirement apps/api/requirements-dev.lock
```

## 4. Start PostgreSQL and Redis

```bash
make services-up
docker compose ps
```

The services store local state in named Docker volumes. `make services-down` stops containers without deleting data.

## 5. Apply migrations

```bash
make migrate
```

M1 contains the migration baseline. M2 creates the identity and core business tables and
adds synthetic `admin` and `sales` memberships for local authorization tests. These accounts
use reserved `.example` addresses and are not real Sari Arta users.

Later Phase 1 migrations add CRM behavior, AI qualification, work tracking, and the M5
opportunity-stage constraint. Always run `make migrate` after pulling application changes.

Load the optional synthetic presentation dataset after migrations:

```bash
make demo-seed
```

The command creates fixed `.example` company/contact scenarios, representative leads, tasks,
an opportunity, and Level A/B/C qualification results. The M8 acceptance set covers a school
central kitchen, hospital kitchen, and low-value single-equipment inquiry. It is idempotent and
only maintains records with reserved synthetic IDs; it never deletes CRM records. Never replace
it with real customer data.

Protected API calls require a Supabase access token signed by an asymmetric `ES256` or
`RS256` project key. Configure the issuer, audience and JWKS URL in `.env`; symmetric JWT
secrets are intentionally unsupported. The local test suite uses generated keys and never
requires a live Supabase project.

The Next.js application uses Supabase SSR cookie sessions when
`NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` are configured.
For local Docker development only, the server-side `DEVELOPMENT_AUTH_SUBJECT` selects the
seeded synthetic administrator. The frontend still requires the local demo credentials from
`DEMO_AUTH_EMAIL` and `DEMO_AUTH_PASSWORD`, then stores a signed, HttpOnly eight-hour session
cookie. The example credentials are `admin@sariarta.local` / `SariArtaDemo2026!` and must never
be reused outside local demonstration. FastAPI rejects the development identity path in
production, and the frontend demo login is disabled unless `APP_ENVIRONMENT=development`.

The public inquiry form requires `PUBLIC_SITE_TOKEN`; the local value is synthetic. Its
FastAPI endpoint applies a Redis fixed-window rate limit and PostgreSQL idempotency. Redis
unavailability causes a safe `503` instead of accepting an unbounded public write.

External AI is disabled by default. With `AI_ENABLED=false`, the worker uses the deterministic
qualification rubric so local demos work without an API key. To use the approved OpenAI
provider path, set `AI_ENABLED=true`, provide `OPENAI_API_KEY`, and select the approved model
through `OPENAI_MODEL`. Never put a real key in `.env.example`, source control, logs, or
screenshots. The qualification input is a minimal saved CRM snapshot; sensitive SDK tracing
is disabled. Agent Runs use `AGENT_MAX_ATTEMPTS` and exponential retry timing based on
`AGENT_RETRY_BASE_SECONDS`. PostgreSQL stores attempt state and safe failures; Redis stores
only immediate or delayed queue messages. `AGENT_STALE_AFTER_SECONDS` defines when a queued or
running record is considered interrupted, and the Worker checks for recovery every
`AGENT_RECOVERY_INTERVAL_SECONDS`. Duplicate recovered queue messages are safe because execution
locks and checks the durable run state. Users can cancel queued/running work through the API;
provider completion after cancellation is discarded.

## 6. Start the applications

Terminal one:

```bash
make api-dev
```

Terminal two:

```bash
make web-dev
```

Terminal three, when testing asynchronous qualification:

```bash
cd apps/api
.venv/bin/python -m sari_api.worker
```

With the default `AI_ENABLED=false`, the worker returns a repeatable demo assessment. When
`AI_ENABLED=true`, startup requires `OPENAI_API_KEY`; provider failures are stored as safe run
failures while manual lead, task, and activity work remains available.

The backend readiness endpoint returns HTTP 503 when PostgreSQL cannot be reached. Liveness remains available so operations can distinguish a running process from a ready service.

## 7. Run validation

All checks:

```bash
make check
```

Backend only:

```bash
make api-check
```

Frontend only:

```bash
make web-check
```

Docker configuration only:

```bash
make compose-check
```

## Full container profile

After local validation, build and run the application containers with:

```bash
docker compose --profile app up --build
```

This profile starts the web, API, qualification worker, PostgreSQL, and Redis containers for
local verification. It is not a production deployment definition.

## Backup and restore verification

Create a private local custom-format dump:

```bash
make backup
```

Verify that dump by restoring it into an isolated temporary database which is removed after the
check:

```bash
make verify-backup BACKUP_FILE=/absolute/path/to/sariarta-YYYYMMDDTHHMMSSZ.dump
```

Local `backups/` is ignored by Git. Production requires encrypted automated backups, off-host
retention, monitoring, and an approved RPO/RTO; see `docs/production-readiness-checklist.md`.

## Dependency updates

Frontend lockfile:

```bash
npm --prefix apps/web install
```

Backend production lockfile:

```bash
apps/api/.venv/bin/pip-compile apps/api/pyproject.toml --output-file apps/api/requirements.lock --strip-extras
```

Backend development lockfile:

```bash
apps/api/.venv/bin/pip-compile apps/api/pyproject.toml --extra dev --output-file apps/api/requirements-dev.lock --strip-extras
```

Dependency changes require the relevant checks and review of generated lockfile differences.

## Troubleshooting

### Port already in use

The defaults are web `3000`, API `8000`, PostgreSQL `5432` and Redis `6379`. Stop the conflicting local process or change the development mapping deliberately in `compose.yaml`.

### Readiness is unhealthy

Check service health:

```bash
docker compose ps
docker compose logs postgres
```

Confirm `DATABASE_URL` points to `localhost` when the API runs on the host and to `postgres` when it runs inside Compose.

### Resetting local development data

Removing Docker volumes deletes local database and Redis data. This is destructive and should be done only when the exact local targets and recovery need are understood.

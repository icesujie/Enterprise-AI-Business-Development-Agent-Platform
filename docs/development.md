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

Protected API calls require a Supabase access token signed by an asymmetric `ES256` or
`RS256` project key. Configure the issuer, audience and JWKS URL in `.env`; symmetric JWT
secrets are intentionally unsupported. The local test suite uses generated keys and never
requires a live Supabase project.

The Next.js application uses Supabase SSR cookie sessions when
`NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` are configured.
For local Docker development only, the server-side `DEVELOPMENT_AUTH_SUBJECT` selects the
seeded synthetic administrator. FastAPI rejects this development path in production.

The public inquiry form requires `PUBLIC_SITE_TOKEN`; the local value is synthetic. Its
FastAPI endpoint applies a Redis fixed-window rate limit and PostgreSQL idempotency. Redis
unavailability causes a safe `503` instead of accepting an unbounded public write.

AI qualification is disabled by default. To use the approved OpenAI provider path, set
`AI_ENABLED=true`, provide `OPENAI_API_KEY`, and select the approved deployment through
`OPENAI_MODEL`. Never put a real key in `.env.example`, source control, logs, or screenshots.
The qualification input is a minimal saved CRM snapshot; sensitive SDK tracing is disabled.

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

Without an API key the worker records a safe failed status. Manual lead, task, and activity
work remains available.

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

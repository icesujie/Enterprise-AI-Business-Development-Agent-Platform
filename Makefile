PYTHON := apps/api/.venv/bin

.PHONY: check api-check web-check compose-check services-up services-down migrate api-dev web-dev

check: api-check web-check compose-check

api-check:
	$(PYTHON)/ruff check apps/api/src apps/api/tests apps/api/migrations
	$(PYTHON)/mypy apps/api/src
	$(PYTHON)/pytest apps/api/tests

web-check:
	npm --prefix apps/web run lint
	npm --prefix apps/web run typecheck
	npm --prefix apps/web run test:ci
	npm --prefix apps/web run build

compose-check:
	docker compose config --quiet

services-up:
	docker compose up --detach postgres redis

services-down:
	docker compose down

migrate:
	cd apps/api && .venv/bin/alembic upgrade head

api-dev:
	$(PYTHON)/uvicorn sari_api.main:app --app-dir apps/api/src --reload --port 8000

web-dev:
	npm --prefix apps/web run dev


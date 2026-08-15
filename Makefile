PYTHON := apps/api/.venv/bin

.PHONY: check api-check web-check compose-check services-up services-down migrate demo-seed api-dev worker-dev web-dev backup verify-backup

check: api-check web-check compose-check

api-check:
	$(PYTHON)/ruff check apps/api/src apps/api/tests apps/api/migrations
	cd apps/api && .venv/bin/mypy
	$(PYTHON)/pytest apps/api/tests

web-check:
	npm --prefix apps/web run format:check
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

demo-seed: migrate
	PYTHONPATH=apps/api/src $(PYTHON)/python -m sari_api.demo_seed

api-dev:
	$(PYTHON)/uvicorn sari_api.main:app --app-dir apps/api/src --reload --port 8000

worker-dev:
	PYTHONPATH=apps/api/src $(PYTHON)/python -m sari_api.worker

web-dev:
	npm --prefix apps/web run dev

backup:
	./scripts/backup-database.sh

verify-backup:
	@test -n "$(BACKUP_FILE)" || (echo "Set BACKUP_FILE=/absolute/path/to/backup.dump" && exit 2)
	./scripts/verify-database-restore.sh "$(BACKUP_FILE)"

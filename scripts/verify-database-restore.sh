#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'Usage: %s /absolute/path/to/backup.dump\n' "$0" >&2
  exit 2
fi

backup_file="$1"
if [[ ! -f "${backup_file}" ]]; then
  printf 'Backup does not exist: %s\n' "${backup_file}" >&2
  exit 2
fi

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verification_database="sariarta_restore_check_$$"

cleanup() {
  docker compose exec -T postgres dropdb \
    --username=sariarta \
    --if-exists \
    "${verification_database}" >/dev/null
}
trap cleanup EXIT

cd "${repository_root}"
docker compose exec -T postgres createdb \
  --username=sariarta \
  "${verification_database}"
docker compose exec -T postgres pg_restore \
  --username=sariarta \
  --dbname="${verification_database}" \
  --no-owner \
  --no-privileges < "${backup_file}"

revision_count="$(docker compose exec -T postgres psql \
  --username=sariarta \
  --dbname="${verification_database}" \
  --tuples-only \
  --no-align \
  --command='SELECT count(*) FROM alembic_version;')"
tenant_count="$(docker compose exec -T postgres psql \
  --username=sariarta \
  --dbname="${verification_database}" \
  --tuples-only \
  --no-align \
  --command='SELECT count(*) FROM tenants;')"

if [[ "${revision_count}" -lt 1 || "${tenant_count}" -lt 1 ]]; then
  printf 'Restore verification failed: required records are missing.\n' >&2
  exit 1
fi

printf 'Restore verified in temporary database %s.\n' "${verification_database}"

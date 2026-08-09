#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
destination_dir="${1:-${repository_root}/backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_file="${destination_dir}/sariarta-${timestamp}.dump"
temporary_file="${backup_file}.partial"

mkdir -p "${destination_dir}"
umask 077

cd "${repository_root}"
docker compose exec -T postgres pg_dump \
  --username=sariarta \
  --dbname=sariarta \
  --format=custom \
  --no-owner \
  --no-privileges > "${temporary_file}"
mv "${temporary_file}" "${backup_file}"

printf '%s\n' "${backup_file}"

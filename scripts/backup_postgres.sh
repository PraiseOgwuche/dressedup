#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
mkdir -p "${BACKUP_DIR}"

docker compose -f docker-compose.pi.yml exec -T db pg_dump -U postgres dressedup > "${BACKUP_DIR}/dressedup_${TIMESTAMP}.sql"
echo "Backup written to ${BACKUP_DIR}/dressedup_${TIMESTAMP}.sql"


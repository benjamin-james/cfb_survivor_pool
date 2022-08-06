#!/usr/bin/env bash
source "$(dirname $0)/.env"
FDUMP="/var/lib/postgresql/data/BACKUP_${POSTGRES_DB}.dump"
DBNAME=${1:-db}
export PGPASSWORD="${POSTGRES_PASSWORD}"
/usr/bin/docker exec -u root "${DBNAME}" pg_dump -v -Fc -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f "${FDUMP}"

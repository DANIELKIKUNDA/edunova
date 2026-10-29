#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL required}"; : "${BACKUP_DIR:=./backups}"
mkdir -p "$BACKUP_DIR"; umask 077
stamp=$(date -u +%Y%m%dT%H%M%SZ); out="$BACKUP_DIR/edunova-$stamp.dump"
pg_dump --format=custom --no-owner --no-acl "$DATABASE_URL" > "$out"
sha256sum "$out" > "$out.sha256"; echo "$out"

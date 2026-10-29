#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL required}"; file=${1:?backup dump required}
sha256sum -c "$file.sha256"
if [[ "${CONFIRM_RESTORE:-}" != "RESTORE_EDUNOVA" ]]; then echo 'Set CONFIRM_RESTORE=RESTORE_EDUNOVA'; exit 2; fi
pg_restore --clean --if-exists --no-owner --no-acl --dbname="$DATABASE_URL" "$file"

#!/usr/bin/env bash
set -euo pipefail
: "${RELEASE_TAG:?required}"; : "${DEPLOY_DIR:?required}"
cd "$DEPLOY_DIR"
git fetch --tags --force
previous="$(git rev-parse HEAD)"; printf '%s\n' "$previous" > .previous_release
git checkout --detach "$RELEASE_TAG"
docker compose -f docker-compose.production.yml build --pull
docker compose -f docker-compose.production.yml run --rm api /app/../scripts/migrate_production.sh || { git checkout --detach "$previous"; exit 1; }
docker compose -f docker-compose.production.yml up -d --remove-orphans
for i in $(seq 1 30); do curl -fsS "${READINESS_URL:-http://127.0.0.1:8000/v1/operations/ready}" >/dev/null && exit 0; sleep 2; done
"$(dirname "$0")/rollback_production.sh"; exit 1

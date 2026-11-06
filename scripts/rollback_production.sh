#!/usr/bin/env bash
set -euo pipefail
: "${DEPLOY_DIR:?required}"; cd "$DEPLOY_DIR"; previous="$(cat .previous_release)"
git checkout --detach "$previous"; docker compose -f docker-compose.production.yml build; docker compose -f docker-compose.production.yml up -d --remove-orphans

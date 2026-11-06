#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/services/api"
python -m compileall -q app
pytest -q
cd "$ROOT"
python scripts/audit_lot11_maximal.py

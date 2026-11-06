#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../services/api"
python -m compileall -q app
pytest -q

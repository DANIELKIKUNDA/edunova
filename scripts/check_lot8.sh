#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/services/api"
python -m compileall -q app tests
pytest -q
if grep -RInE 'TODO|FIXME|NotImplementedError' app --exclude='*.pyc'; then
  echo 'Stubs found in backend core' >&2
  exit 1
fi

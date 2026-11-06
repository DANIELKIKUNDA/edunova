#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/services/api"
python -m compileall -q app
pytest -q
cd "$ROOT"
python scripts/audit_lot10_analytics.py
python scripts/audit_lot10_uiux_maximal.py
if grep -R -n -E 'TODO|FIXME|NotImplementedError' services/api/app apps/mobile/lib/src/features/analytics apps/mobile/lib/src/features/home/presentation/home_page.dart; then
  echo 'Functional stub marker detected' >&2
  exit 1
fi
echo 'LOT10.1 certification: PASS'

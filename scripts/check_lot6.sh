#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/services/api"
python -m compileall -q app tests
pytest -q
cd "$ROOT"
python - <<'PY'
import ast
from pathlib import Path
issues=[]
for p in Path('services/api/app').rglob('*.py'):
    tree=ast.parse(p.read_text(), filename=str(p))
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and len(node.body)==1 and isinstance(node.body[0],ast.Pass):
            issues.append(f'{p}:{node.lineno}:{node.name}')
if issues:
    raise SystemExit('Functional pass-only stubs:\n'+'\n'.join(issues))
print('LOT6 functional-stub audit PASS')
PY

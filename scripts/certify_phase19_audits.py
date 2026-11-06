"""Run the repository's read-only historical structural audits locally."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
out = root / 'evidence' / os.environ.get('EDUNOVA_CERT_EVIDENCE', 'local-phase19') / 'audits'
out.mkdir(exist_ok=True, parents=True)
results = []
for script in sorted((root / 'scripts').glob('audit_*.py')):
    with (out / (script.stem + '.log')).open('w', encoding='utf-8') as log:
        try:
            result = subprocess.run([sys.executable, '-X', 'utf8', str(script)], cwd=root, stdout=log, stderr=subprocess.STDOUT, timeout=90)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
            log.write('\nTIMEOUT after 90 seconds\n')
    results.append({'script': str(script.relative_to(root)), 'exit_code': code})
    print(script.name, code, flush=True)
(out / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print('STRUCTURAL AUDITS:', sum(r['exit_code'] == 0 for r in results), 'succeeded,', sum(r['exit_code'] != 0 for r in results), 'failed; not functional tests', flush=True)
sys.exit(any(r['exit_code'] != 0 for r in results))

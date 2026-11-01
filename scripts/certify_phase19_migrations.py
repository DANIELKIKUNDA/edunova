"""Apply repository migrations only to the dedicated local certification DB."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
psql = Path('C:/Program Files/PostgreSQL/16/bin/psql.exe')
database = os.environ.get('EDUNOVA_MIGRATION_TEST_DATABASE', 'edunova_phase19_test')
if database not in {'edunova_phase19_test', 'edunova_phase19_final_test'}:
    raise SystemExit('Refusing a database outside the local certification allowlist')
for migration in sorted((root / 'services/api/migrations').glob('*.sql')):
    print('APPLY', migration.name, flush=True)
    result = subprocess.run([str(psql), '-X', '-h', '127.0.0.1', '-p', '55439', '-U', 'edunova_cert', '-d', database, '-v', 'ON_ERROR_STOP=1', '-f', str(migration)])
    if result.returncode:
        sys.exit(result.returncode)
print('ALL MIGRATIONS APPLIED', flush=True)

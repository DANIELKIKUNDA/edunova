"""Local evidence runner. Never reads .env or connects to production services."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence' / 'local-phase19'
OUT.mkdir(exist_ok=True)
env = os.environ.copy()
for key in list(env):
    if any(token in key.upper() for token in ('SECRET', 'TOKEN', 'API_KEY', 'DATABASE_URL', 'REDIS_URL', 'AWS_', 'GOOGLE_APPLICATION_CREDENTIALS')):
        env.pop(key, None)
env.update(EDUNOVA_ENV='test', AI_PROVIDER='fake', PAYMENT_PROVIDER='sandbox', FCM_ENABLED='false', PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
python = str(ROOT / '.venv/Scripts/python.exe')
flutter = str(Path.home() / 'dev/flutter/bin/flutter.bat')
jobs = {
    'compile': ([python, '-m', 'compileall', '-q', 'services/api/app', 'services/api/tests'], ROOT),
    'collect': ([python, '-m', 'pytest', '--collect-only', '-q', 'services/api/tests'], ROOT),
    'phase19': ([python, '-m', 'pytest', '-q', 'services/api/tests/test_phase19_payment_hardening.py', 'services/api/tests/test_phase19_atomic_finance.py', 'services/api/tests/test_phase19_atomic_callback.py', '--junitxml=' + str(OUT / 'phase19.xml')], ROOT),
    'backend': ([python, '-m', 'pytest', '-q', 'services/api/tests', '--junitxml=' + str(OUT / 'backend.xml')], ROOT),
    'pip-check': ([python, '-m', 'pip', 'check'], ROOT),
    'freeze': ([python, '-m', 'pip', 'freeze'], ROOT),
    'postgres': ([python, '-m', 'pytest', '-q', 'services/api/tests/test_phase19_atomic_finance.py', 'services/api/tests/test_phase19_atomic_callback.py', 'services/api/tests/test_phase19_postgres_concurrency.py', 'services/api/tests/test_phase19_postgres_constraints.py', '--junitxml=' + str(OUT / 'postgres.xml')], ROOT),
    'migrations': ([python, str(ROOT / 'scripts/certify_phase19_migrations.py')], ROOT),
}
for app in ('admin', 'mobile'):
    for task, args in {'analyze': ['analyze', '--no-pub'], 'test': ['test', '--no-pub', '--reporter=expanded'], 'web': ['build', 'web', '--release', '--no-pub']}.items():
        jobs[f'{app}-{task}'] = ([flutter, *args], ROOT / 'apps' / app)

def run(name):
    command, cwd = jobs[name]
    start = time.monotonic()
    with (OUT / f'{name}.log').open('w', encoding='utf-8') as log:
        log.write('COMMAND: ' + subprocess.list2cmdline(command) + '\nCWD: ' + str(cwd) + '\n')
        log.flush()
        try:
            job_env = env.copy()
            if name == 'postgres':
                job_env['EDUNOVA_FINANCE_TEST_DATABASE_URL'] = 'postgresql+psycopg://edunova_cert@127.0.0.1:55439/edunova_phase19_test'
            result = subprocess.run(command, cwd=cwd, env=job_env, stdout=log, stderr=subprocess.STDOUT, timeout=4500)
            code = result.returncode
        except subprocess.TimeoutExpired:
            log.write('\nTIMEOUT after 4500 seconds\n')
            code = 124
    record = dict(command=command, cwd=str(cwd), exit_code=code, seconds=round(time.monotonic()-start, 2))
    (OUT / f'{name}.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(name, record, flush=True)

if __name__ == '__main__':
    for name in sys.argv[1:]:
        run(name)

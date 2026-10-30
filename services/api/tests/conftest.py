import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# A distinct database per pytest process avoids deleting another Windows run's
# open SQLite file (for example while a PostgreSQL certification runs alongside).
from uuid import uuid4
TEST_DIR = ROOT.parents[1] / '.local-certification'
TEST_DIR.mkdir(exist_ok=True)
TEST_DB = TEST_DIR / f'pytest-{uuid4().hex}.db'
os.environ['EDUNOVA_ENV'] = 'test'
os.environ['DATABASE_URL'] = f'sqlite+pysqlite:///{TEST_DB}'
os.environ['JWT_SECRET'] = 'pytest-secret-' + ('x' * 48)

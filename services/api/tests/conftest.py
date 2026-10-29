import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Every backend test run starts from a clean isolated database.
TEST_DB = ROOT / '.pytest_edunova.db'
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ['EDUNOVA_ENV'] = 'test'
os.environ['DATABASE_URL'] = f'sqlite+pysqlite:///{TEST_DB}'
os.environ['JWT_SECRET'] = 'pytest-secret-' + ('x' * 48)

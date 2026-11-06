"""Opt-in real PostgreSQL fixtures, restricted to the dedicated local test DB."""
import os
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import StaticPool


def build_test_engine():
    url = os.getenv('EDUNOVA_FINANCE_TEST_DATABASE_URL')
    if not url:
        return create_engine('sqlite+pysqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    parsed = make_url(url)
    if (parsed.get_backend_name(), parsed.host, parsed.port, parsed.database) != ('postgresql', '127.0.0.1', 55439, 'edunova_phase19_test'):
        raise RuntimeError('Refusing a database outside the dedicated local certification cluster')
    schema = 'cert_' + uuid4().hex
    control = create_engine(url)
    with control.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA {schema}'))
    control.dispose()
    engine = create_engine(url, connect_args={'options': f'-csearch_path={schema} -clock_timeout=10000 -cstatement_timeout=20000'})
    engine.certification_schema = schema
    return engine


def dispose_test_engine(engine):
    schema = getattr(engine, 'certification_schema', None)
    engine.dispose()
    if schema:
        control = create_engine(os.environ['EDUNOVA_FINANCE_TEST_DATABASE_URL'])
        with control.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        control.dispose()

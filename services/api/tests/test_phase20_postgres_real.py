"""Phase 20 certification against a real PostgreSQL 16 service.

These tests deliberately use PHASE20_POSTGRES_URL instead of the SQLite test
fixture, so a green result is evidence of a real PostgreSQL execution.
"""
from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.shared.infrastructure.database import Base, build_engine

# Importing Runtime registers every mapped production table on Base.metadata.
import app.runtime  # noqa: F401,E402


@pytest.fixture(scope="session")
def pg_engine():
    url = os.environ["PHASE20_POSTGRES_URL"]
    assert url.startswith("postgresql"), "real PostgreSQL URL required"
    engine = build_engine(url)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS phase20_idempotency (
                operation_key text PRIMARY KEY,
                payload_hash text NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS phase20_tenant_probe (
                tenant_id text NOT NULL,
                item_id text NOT NULL,
                payload jsonb NOT NULL,
                PRIMARY KEY (tenant_id, item_id)
            )
        """))
        connection.execute(text("ALTER TABLE phase20_tenant_probe ENABLE ROW LEVEL SECURITY"))
        connection.execute(text("ALTER TABLE phase20_tenant_probe FORCE ROW LEVEL SECURITY"))
        connection.execute(text("DROP POLICY IF EXISTS phase20_tenant_isolation ON phase20_tenant_probe"))
        connection.execute(text("""
            CREATE POLICY phase20_tenant_isolation ON phase20_tenant_probe
            USING (tenant_id = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
        """))
    yield engine
    engine.dispose()


def test_01_real_postgresql_16(pg_engine):
    with pg_engine.connect() as c:
        version = c.scalar(text("SHOW server_version_num"))
    assert int(version) >= 160000


def test_02_driver_is_psycopg(pg_engine):
    assert pg_engine.dialect.name == "postgresql"
    assert pg_engine.dialect.driver == "psycopg"


def test_03_pool_is_bounded_and_pre_ping_enabled(pg_engine):
    assert pg_engine.pool.size() == int(os.getenv("DB_POOL_SIZE", "10"))
    assert pg_engine.pool._pre_ping is True


def test_04_full_production_metadata_created(pg_engine):
    names = inspect(pg_engine).get_table_names()
    assert len(names) >= 40


def test_05_metadata_creation_is_idempotent(pg_engine):
    before = set(inspect(pg_engine).get_table_names())
    Base.metadata.create_all(pg_engine)
    assert set(inspect(pg_engine).get_table_names()) == before


def test_06_mapped_tables_have_primary_keys(pg_engine):
    db = inspect(pg_engine)
    missing = [
        table for table in Base.metadata.tables
        if not db.get_pk_constraint(table)["constrained_columns"]
    ]
    assert missing == []


def test_07_foreign_keys_are_materialized(pg_engine):
    db = inspect(pg_engine)
    assert sum(len(db.get_foreign_keys(t)) for t in db.get_table_names()) >= 20


def test_08_transaction_rollback_is_atomic(pg_engine):
    with pytest.raises(RuntimeError):
        with pg_engine.begin() as c:
            c.execute(text("INSERT INTO phase20_idempotency(operation_key,payload_hash) VALUES ('rollback','x')"))
            raise RuntimeError("interrupt")
    with pg_engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM phase20_idempotency WHERE operation_key='rollback'")) == 0


def test_09_primary_key_prevents_duplicate_processing(pg_engine):
    with pg_engine.begin() as c:
        c.execute(text("DELETE FROM phase20_idempotency WHERE operation_key='duplicate'"))
        c.execute(text("INSERT INTO phase20_idempotency(operation_key,payload_hash) VALUES ('duplicate','a')"))
    with pytest.raises(IntegrityError):
        with pg_engine.begin() as c:
            c.execute(text("INSERT INTO phase20_idempotency(operation_key,payload_hash) VALUES ('duplicate','b')"))


def test_10_concurrent_replays_create_one_row(pg_engine):
    with pg_engine.begin() as c:
        c.execute(text("DELETE FROM phase20_idempotency WHERE operation_key='concurrent'"))

    def insert_once():
        with pg_engine.begin() as c:
            return c.execute(text("""
                INSERT INTO phase20_idempotency(operation_key,payload_hash)
                VALUES ('concurrent','same')
                ON CONFLICT (operation_key) DO NOTHING
            """)).rowcount

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: insert_once(), range(16)))
    assert sum(results) == 1
    with pg_engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM phase20_idempotency WHERE operation_key='concurrent'")) == 1


def _tenant_rows(pg_engine, tenant):
    with pg_engine.begin() as c:
        c.execute(text("SET LOCAL app.tenant_id = :tenant"), {"tenant": tenant})
        return c.execute(text("SELECT tenant_id,item_id FROM phase20_tenant_probe ORDER BY item_id")).all()


def test_11_rls_accepts_current_tenant(pg_engine):
    with pg_engine.begin() as c:
        c.execute(text("SET LOCAL app.tenant_id = 'campus-a'"))
        c.execute(text("DELETE FROM phase20_tenant_probe"))
        c.execute(text("INSERT INTO phase20_tenant_probe VALUES ('campus-a','a1','{}'::jsonb)"))
    assert _tenant_rows(pg_engine, "campus-a") == [("campus-a", "a1")]


def test_12_rls_hides_other_tenant(pg_engine):
    assert _tenant_rows(pg_engine, "campus-b") == []


def test_13_rls_rejects_cross_tenant_write(pg_engine):
    with pytest.raises(DBAPIError):
        with pg_engine.begin() as c:
            c.execute(text("SET LOCAL app.tenant_id = 'campus-b'"))
            c.execute(text("INSERT INTO phase20_tenant_probe VALUES ('campus-a','forbidden','{}'::jsonb)"))


def test_14_jsonb_round_trip(pg_engine):
    with pg_engine.begin() as c:
        value = c.scalar(text("SELECT '{\"offline\":true,\"attempts\":2}'::jsonb"))
    assert value == {"offline": True, "attempts": 2}


def test_15_unicode_round_trip(pg_engine):
    sample = "Université de Lubumbashi — étudiant"
    with pg_engine.connect() as c:
        assert c.scalar(text("SELECT CAST(:value AS text)"), {"value": sample}) == sample


def test_16_timezone_is_utc(pg_engine):
    with pg_engine.connect() as c:
        assert c.scalar(text("SELECT current_setting('TIMEZONE')")).upper() in {"UTC", "ETC/UTC"}


def test_17_statement_timeout_is_enforced_and_connection_recovers(pg_engine):
    with pytest.raises(DBAPIError):
        with pg_engine.begin() as c:
            c.execute(text("SET LOCAL statement_timeout = '30ms'"))
            c.execute(text("SELECT pg_sleep(0.15)"))
    with pg_engine.connect() as c:
        assert c.scalar(text("SELECT 1")) == 1


def test_18_indexed_idempotency_lookup_plan(pg_engine):
    with pg_engine.begin() as c:
        c.execute(text("SET LOCAL enable_seqscan = off"))
        plan = "\n".join(row[0] for row in c.execute(text(
            "EXPLAIN SELECT * FROM phase20_idempotency WHERE operation_key='concurrent'"
        )))
    assert "Index Scan" in plan


def test_19_query_latency_budget(pg_engine):
    started = time.perf_counter()
    with pg_engine.connect() as c:
        for _ in range(200):
            assert c.scalar(text("SELECT 1")) == 1
    assert time.perf_counter() - started < 3.0


def test_20_connection_health_after_degraded_scenarios(pg_engine):
    with pg_engine.connect() as c:
        assert c.scalar(text("SELECT current_database()")) == "edunova_test"

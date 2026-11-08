"""Check deployed SQL constraints, rather than SQLAlchemy create_all substitutes."""
import os
from uuid import uuid4

import psycopg
import pytest

pytestmark = pytest.mark.skipif(not os.getenv('EDUNOVA_FINANCE_TEST_DATABASE_URL'), reason='Requires the locally migrated certification PostgreSQL database')


@pytest.fixture
def migrated():
    from sqlalchemy.engine import make_url
    url = make_url(os.environ['EDUNOVA_FINANCE_TEST_DATABASE_URL'])
    assert (url.host, url.port, url.database) == ('127.0.0.1', 55439, 'edunova_phase19_test')
    with psycopg.connect(host=url.host, port=url.port, dbname=url.database, user=url.username) as connection:
        try:
            yield connection
        finally:
            connection.rollback()


def test_migrated_finance_rejects_nonpositive_receipt(migrated):
    with pytest.raises(psycopg.errors.CheckViolation):
        migrated.execute("INSERT INTO student_finance_receipts (id,institution_id,student_id,reference,amount_minor,currency,payment_method,issued_by,issued_at) VALUES (%s,'cert','student','receipt',0,'CDF','mobile_money','cert',CURRENT_TIMESTAMP)", (uuid4().hex,))


def test_migrated_charge_rejects_overallocation(migrated):
    with pytest.raises(psycopg.errors.CheckViolation):
        migrated.execute("INSERT INTO student_finance_charges (id,institution_id,student_id,registration_id,fee_item_id,code,label,amount_minor,paid_minor,currency,state,created_at) VALUES (%s,'cert','student','registration','fee','fee','Tuition',100,101,'CDF','paid',CURRENT_TIMESTAMP)", (uuid4().hex,))


@pytest.mark.parametrize('constraint', ['uq_gateway_idempotency', 'uq_gateway_merchant_ref', 'uq_gateway_provider_ref', 'uq_gateway_provider_event', 'uq_finance_external_ref', 'uq_finance_reference'])
def test_migrated_unique_constraints_exist(migrated, constraint):
    row = migrated.execute("SELECT contype FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public' AND c.conname=%s", (constraint,)).fetchone()
    assert row == ('u',)

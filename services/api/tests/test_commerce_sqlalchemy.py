from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.modules.commerce.domain.model import Money, PaymentIntent, PaymentState
from app.modules.commerce.infrastructure.sqlalchemy_repo import SqlAlchemyPaymentRepository
from app.modules.identity.domain.model import Account
from app.modules.identity.infrastructure.sqlalchemy_repo import SqlAlchemyAccountRepository
from app.shared.infrastructure.database import Base


def make_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_account_repository_persists_and_finds_case_insensitive_email():
    sf = make_session_factory(); repo = SqlAlchemyAccountRepository(sf)
    now = datetime(2026,9,20,tzinfo=UTC)
    account = Account(id="a1", display_name="Daniel", password_hash="hash", email="daniel@example.com", created_at=now)
    repo.save(account)
    assert repo.find_by_login("DANIEL@EXAMPLE.COM").id == "a1"


def test_payment_repository_enforces_idempotency_lookup():
    sf = make_session_factory(); repo = SqlAlchemyPaymentRepository(sf)
    now = datetime(2026,9,20,tzinfo=UTC)
    p = PaymentIntent(id="p1",account_id="a1",plan_code="premium-30d",amount=Money(3000),phone_number="+243",idempotency_key="idem",state=PaymentState.PENDING,provider="sandbox",provider_reference="ref",created_at=now,updated_at=now,expires_at=now+timedelta(minutes=15))
    repo.save(p)
    found = repo.get_by_idempotency("a1","idem")
    assert found is not None and found.id == "p1"

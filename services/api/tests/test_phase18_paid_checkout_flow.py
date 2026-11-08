from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import pytest
from app.shared.infrastructure.database import Base
from app.modules.commerce.application.campus_paid_checkout import CampusPaidCheckoutService, CampusPaidOrderRow
from app.modules.commerce.application.campus_offers import CampusOfferRow
from app.modules.commerce.infrastructure.sqlalchemy_repo import CampusLicenseRow
from app.modules.commerce.infrastructure.memory import FakeMobileMoneyProvider
from app.modules.commerce.domain.model import Money, PaymentState, WebhookEvent

NOW=datetime(2026,10,18,tzinfo=timezone.utc)
class Authorized:
    def _admin(self, institution_id, actor_id):
        if institution_id!='univ-1' or actor_id!='rector': raise PermissionError('forbidden')

@pytest.fixture
def flow(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'payments.db'))
    Base.metadata.create_all(engine)
    sessions=sessionmaker(engine)
    provider=FakeMobileMoneyProvider()
    service=CampusPaidCheckoutService(sessions, Authorized(), {provider.name:provider}, lambda: NOW)
    with sessions.begin() as s:
        s.add(CampusOfferRow(code='campus-30d',label='Campus 30 jours',price_cdf=10000,seats=100,duration_days=30,grace_days=5,active=True,revision=1,updated_by='owner',updated_at=NOW))
    return service,sessions,provider

def checkout(flow,key='abcdefgh'):
    svc,_,provider=flow
    return svc.checkout(institution_id='univ-1',actor_id='rector',offer_code='campus-30d',phone_number='0999999999',provider_name=provider.name,idempotency_key=key)

def event(flow, checkout_result, state=PaymentState.SUCCEEDED, amount=10000):
    provider=flow[2]
    return WebhookEvent(provider=provider.name,event_id='evt-1',provider_reference=checkout_result['provider_reference'],state=state,amount=Money(amount),received_at=NOW)

def test_verified_payment_fulfills_once(flow):
    result=checkout(flow)
    assert checkout(flow)==result
    assert flow[1]().query(CampusLicenseRow).count()==0
    first=flow[0].verified_event(provider_name=flow[2].name,event=event(flow,result))
    assert first['state']=='succeeded' and first['license_id']
    duplicate=flow[0].verified_event(provider_name=flow[2].name,event=event(flow,result))
    assert duplicate['duplicate'] is True and duplicate['license_id']==first['license_id']
    with flow[1]() as s: assert s.query(CampusLicenseRow).count()==1

def test_failed_payment_cannot_grant(flow):
    result=checkout(flow)
    response=flow[0].verified_event(provider_name=flow[2].name,event=event(flow,result,PaymentState.FAILED))
    assert response['state']=='failed'
    flow[0].verified_event(provider_name=flow[2].name,event=event(flow,result))
    with flow[1]() as s: assert s.query(CampusLicenseRow).count()==0

def test_amount_mismatch_never_grants(flow):
    result=checkout(flow)
    with pytest.raises(ValueError,match='amount_mismatch'):
        flow[0].verified_event(provider_name=flow[2].name,event=event(flow,result,amount=9000))
    with flow[1]() as s: assert s.query(CampusLicenseRow).count()==0

def test_reused_idempotency_with_changed_offer_is_rejected(flow):
    checkout(flow)
    with pytest.raises(ValueError,match='idempotency_key_conflict'):
        flow[0].checkout(institution_id='univ-1',actor_id='rector',offer_code='different',phone_number='0999999999',provider_name=flow[2].name,idempotency_key='abcdefgh')

def test_inactive_offer_cannot_checkout(flow):
    with flow[1].begin() as s:
        s.get(CampusOfferRow,'campus-30d').active=False
    with pytest.raises(ValueError,match='unavailable'): checkout(flow)

def test_unprivileged_user_cannot_checkout(flow):
    with pytest.raises(PermissionError):
        flow[0].checkout(institution_id='univ-1',actor_id='student',offer_code='campus-30d',phone_number='0999999999',provider_name=flow[2].name,idempotency_key='abcdefgh')

def test_renewal_extends_existing_term(flow):
    a=checkout(flow,'abcdefgh'); flow[0].verified_event(provider_name=flow[2].name,event=event(flow,a))
    b=checkout(flow,'ijklmnop'); flow[0].verified_event(provider_name=flow[2].name,event=event(flow,b))
    with flow[1]() as s:
        rows=s.scalars(select(CampusLicenseRow).order_by(CampusLicenseRow.starts_at)).all()
        assert len(rows)==2
        assert rows[1].starts_at==rows[0].ends_at

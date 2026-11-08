from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.shared.infrastructure.database import Base
from app.modules.commerce.application.campus_offers import CampusOffer, CampusOfferService

class Governance:
    def require(self, actor, permission):
        assert permission == 'platform.roles.manage'
        if actor != 'volcano-admin':
            raise PermissionError('platform_permission_required')

def service():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return CampusOfferService(sessionmaker(bind=engine), Governance(), lambda: datetime.now(timezone.utc))

def offer(revision=1, price=100000, active=True):
    return CampusOffer('campus-annual', 'Licence annuelle', price, 200, 365, 14, active, revision)

def test_catalog_create_update_and_revision_conflict():
    svc=service()
    assert svc.put(actor_id='volcano-admin', offer=offer(), expected_revision=0).revision == 1
    assert svc.list(actor_id='volcano-admin')[0].price_cdf == 100000
    with pytest.raises(ValueError, match='revision_conflict'):
        svc.put(actor_id='volcano-admin', offer=offer(), expected_revision=0)
    svc.put(actor_id='volcano-admin', offer=offer(2, 150000), expected_revision=1)
    assert svc.list(actor_id='volcano-admin')[0].price_cdf == 150000

def test_catalog_forbids_institutional_admin_and_students():
    svc=service()
    for actor in ('student', 'campus-rector'):
        with pytest.raises(PermissionError):
            svc.list(actor_id=actor)
        with pytest.raises(PermissionError):
            svc.put(actor_id=actor, offer=offer(), expected_revision=0)

def test_catalog_rejects_invalid_offer():
    for bad in ('campus annual', '../escape', ''):
        with pytest.raises(ValueError, match='invalid_campus_offer'):
            CampusOffer(bad,'Label',100,5,365,0,True,1)
    with pytest.raises(ValueError, match='invalid_campus_offer'):
        offer(price=-1)

def test_catalog_is_not_a_payment_or_license_grant():
    svc=service()
    svc.put(actor_id='volcano-admin', offer=offer(), expected_revision=0)
    assert [x.code for x in svc.list(actor_id='volcano-admin')] == ['campus-annual']
    assert not hasattr(svc, 'activate_license')
    assert not hasattr(svc, 'confirm_payment')

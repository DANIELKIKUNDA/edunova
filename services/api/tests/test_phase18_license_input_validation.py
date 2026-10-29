from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from app.modules.commerce.application.commercial_service import CommercialService
from app.modules.campus.domain.model import CampusRole, MembershipState

@pytest.fixture
def subject():
    repo=Mock()
    campus=Mock()
    campus.membership.return_value=SimpleNamespace(role=CampusRole.ADMIN,state=MembershipState.ACTIVE)
    return CommercialService(repo,campus,lambda:datetime(2026,10,18,tzinfo=timezone.utc)),repo

@pytest.mark.parametrize('seats', [0,-1,100001,True,1.5])
def test_creation_rejects_invalid_seats_before_persistence(subject,seats):
    svc,repo=subject
    with pytest.raises(ValueError,match='invalid_license_seats'):
        svc.create_license(institution_id='uni',actor_id='admin',plan_code='free',seats=seats,price_cdf=0)
    repo.save_license.assert_not_called()

@pytest.mark.parametrize('plan', ['\x00campus','campus\n','a'*129,' campus '])
def test_creation_rejects_ambiguous_plan_code(subject,plan):
    svc,repo=subject
    with pytest.raises(ValueError,match='invalid_plan_code'):
        svc.create_license(institution_id='uni',actor_id='admin',plan_code=plan,seats=10,price_cdf=0)
    repo.save_license.assert_not_called()

@pytest.mark.parametrize('seats', [0,100001,True])
def test_renewal_rejects_invalid_seats_before_persistence(subject,seats):
    svc,repo=subject
    with pytest.raises(ValueError,match='invalid_license_seats'):
        svc.renew_license(institution_id='uni',actor_id='admin',renewal_reference='ref',plan_code='free',seats=seats,price_cdf=0)
    repo.renew_license_atomic.assert_not_called()

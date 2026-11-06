from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from app.modules.commerce.application.commercial_service import CommercialService
from app.modules.campus.domain.model import CampusRole, MembershipState


def service():
    repo=Mock()
    campus=Mock()
    campus.membership.return_value=SimpleNamespace(role=CampusRole.ADMIN,state=MembershipState.ACTIVE)
    return CommercialService(repo,campus,lambda:datetime(2026,10,18,tzinfo=timezone.utc)),repo


def test_complimentary_license_never_books_fictitious_revenue():
    svc,repo=service()
    license=svc.create_license(institution_id='uni',actor_id='admin',plan_code='campus-free',seats=10,price_cdf=0)
    assert license.price_cdf==0
    repo.save_license.assert_called_once()
    repo.append_ledger.assert_not_called()


@pytest.mark.parametrize('duration,grace',[(0,0),(3661,0),(365,-1),(365,91)])
def test_invalid_duration_is_rejected_before_writing(duration,grace):
    svc,repo=service()
    with pytest.raises(ValueError,match='invalid_license_duration'):
        svc.create_license(institution_id='uni',actor_id='admin',plan_code='campus-free',seats=10,price_cdf=0,duration_days=duration,grace_days=grace)
    repo.save_license.assert_not_called()


def test_paid_license_still_requires_verified_payment():
    svc,repo=service()
    with pytest.raises(ValueError,match='verified_payment_required'):
        svc.create_license(institution_id='uni',actor_id='admin',plan_code='paid',seats=10,price_cdf=100)
    repo.save_license.assert_not_called()

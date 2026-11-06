from datetime import timedelta
import pytest
from test_commerce_lot29 import setup, NOW
from app.modules.campus.domain.model import CampusRole

KW=dict(institution_id='u',actor_id='a',plan_code='campus',seats=20,price_cdf=0,duration_days=30,grace_days=7)

def test_renewal_extends_paid_period_and_is_idempotent():
    service, repo = setup()
    first = service.create_license(**KW)
    renewed = service.renew_license(**KW,renewal_reference='receipt-1')
    assert renewed.starts_at == first.ends_at
    assert renewed.ends_at == first.ends_at + timedelta(days=30)
    assert renewed.grace_until == renewed.ends_at + timedelta(days=7)
    repeated = service.renew_license(**KW,renewal_reference='receipt-1')
    assert repeated.id == renewed.id and repeated.ends_at == renewed.ends_at
    assert repo.current_license('u').id == renewed.id

def test_renewal_reference_cannot_change_payload():
    service,_=setup()
    service.renew_license(**KW,renewal_reference='r')
    with pytest.raises(ValueError,match='renewal_reference_conflict'):
        service.renew_license(**(KW|{'seats':30}),renewal_reference='r')

def test_suspended_license_cannot_be_renewed_implicitly():
    service,_=setup()
    service.create_license(**KW)
    service.suspend_license(institution_id='u',actor_id='a')
    with pytest.raises(ValueError,match='license_suspended_or_canceled'):
        service.renew_license(**KW,renewal_reference='r')

def test_non_admin_cannot_renew():
    service,_=setup(role=CampusRole.TEACHER)
    with pytest.raises(PermissionError):
        service.renew_license(**KW,renewal_reference='r')

def test_invalid_duration_and_reference():
    service,_=setup()
    with pytest.raises(ValueError):service.renew_license(**KW,renewal_reference=' ')
    with pytest.raises(ValueError):service.renew_license(**(KW|{'duration_days':0}),renewal_reference='r')

@pytest.mark.parametrize('reference', [' r', 'r ', '\tr', 'r\n', 'r\x00', '\x7f', ''])
def test_renewal_reference_rejects_ambiguous_or_control_characters(reference):
    service, _ = setup()
    with pytest.raises(ValueError, match='invalid_renewal_reference'):
        service.renew_license(**KW, renewal_reference=reference)

def test_renewal_plan_rejects_ambiguous_whitespace():
    service, _ = setup()
    with pytest.raises(ValueError, match='invalid_plan_code'):
        service.renew_license(**(KW | {'plan_code': ' campus '}), renewal_reference='valid')

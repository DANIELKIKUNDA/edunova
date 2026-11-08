"""Direct service calls must not bypass HTTP payment guards."""
import pytest
from test_commerce_lot29 import setup

def test_service_rejects_unverified_paid_initial_license():
    service, repo = setup()
    with pytest.raises(ValueError, match="verified_payment_required"):
        service.create_license(institution_id="u", actor_id="a", plan_code="campus", seats=10, price_cdf=1000)
    assert repo.current_license("u") is None

def test_service_rejects_unverified_paid_renewal_without_mutation():
    service, repo = setup()
    initial = service.create_license(institution_id="u", actor_id="a", plan_code="campus", seats=10, price_cdf=0)
    with pytest.raises(ValueError, match="verified_payment_required"):
        service.renew_license(institution_id="u", actor_id="a", plan_code="campus", seats=10, price_cdf=1000, renewal_reference="fake-receipt")
    assert repo.current_license("u").id == initial.id

def test_free_administrative_renewal_remains_idempotent():
    service, repo = setup()
    args = dict(institution_id="u", actor_id="a", plan_code="campus", seats=10, price_cdf=0, renewal_reference="grant-2026")
    first = service.renew_license(**args)
    second = service.renew_license(**args)
    assert first.id == second.id

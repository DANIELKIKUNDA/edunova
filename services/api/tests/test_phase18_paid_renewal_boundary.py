"""Prevent a user-supplied receipt string from masquerading as a paid receipt."""
import pytest
from fastapi import HTTPException
from app.modules.commerce.api.router import CampusRenewalRequest, renew_campus_license


def test_paid_renewal_is_rejected_before_any_provisioning(monkeypatch):
    from app.modules.commerce.api import router
    class FailIfCalled:
        def renew_license(self, **kwargs):
            raise AssertionError('must not provision without verified payment')
    monkeypatch.setattr(router.runtime, 'commercial', FailIfCalled())
    req = CampusRenewalRequest(renewal_reference='unverified-receipt', seats=10,
                               price_cdf=1000, duration_days=30)
    with pytest.raises(HTTPException) as error:
        renew_campus_license('institution', req, auth=object())
    assert error.value.status_code == 409
    assert error.value.detail == 'verified_payment_required_for_paid_campus_renewal'


def test_free_administrative_renewal_not_blocked_by_payment_boundary(monkeypatch):
    from app.modules.commerce.api import router
    class Sentinel(Exception):
        pass
    class Called:
        def renew_license(self, **kwargs):
            raise Sentinel()
    monkeypatch.setattr(router.runtime, 'commercial', Called())
    req = CampusRenewalRequest(renewal_reference='free-grant', seats=10,
                               price_cdf=0, duration_days=30)
    with pytest.raises(Sentinel):
        renew_campus_license('institution', req, auth=type('Auth', (), {'account_id':'admin'})())


def test_paid_initial_license_is_rejected_before_any_provisioning(monkeypatch):
    from app.modules.commerce.api import router
    class FailIfCalled:
        def create_license(self, **kwargs):
            raise AssertionError('must not provision paid license without verified payment')
    monkeypatch.setattr(router.runtime, 'commercial', FailIfCalled())
    req = router.CampusLicenseRequest(seats=30, price_cdf=120000)
    with pytest.raises(HTTPException) as error:
        router.create_campus_license('institution', req, auth=object())
    assert error.value.status_code == 409
    assert error.value.detail == 'verified_payment_required_for_paid_campus_license'


def test_free_initial_license_preserves_administrative_path(monkeypatch):
    from app.modules.commerce.api import router
    class Sentinel(Exception):
        pass
    class Called:
        def create_license(self, **kwargs):
            raise Sentinel()
    monkeypatch.setattr(router.runtime, 'commercial', Called())
    req = router.CampusLicenseRequest(seats=30, price_cdf=0)
    with pytest.raises(Sentinel):
        router.create_campus_license('institution', req, auth=type('Auth', (), {'account_id': 'admin'})())

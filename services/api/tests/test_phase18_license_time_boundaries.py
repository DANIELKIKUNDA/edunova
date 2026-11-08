"""Phase 18: an institutional licence must never grant access before its start."""
from datetime import datetime, timedelta, timezone
import pytest
from app.modules.commerce.domain.commercial import CampusLicense, LicenseState

NOW = datetime(2026, 10, 18, tzinfo=timezone.utc)

def license(*, grace_days=2):
    return CampusLicense('license-1','university-1','campus-annual',LicenseState.ACTIVE,
                         100,10000,NOW + timedelta(days=1), NOW + timedelta(days=31),
                         NOW + timedelta(days=31 + grace_days),'admin',NOW)

def test_future_license_is_not_yet_valid():
    lic = license()
    assert lic.effective_state(NOW) == LicenseState.EXPIRED
    assert not lic.permits(NOW, 10)

def test_license_activates_at_start_boundary():
    lic = license()
    assert lic.effective_state(lic.starts_at) == LicenseState.ACTIVE
    assert lic.permits(lic.starts_at, 100)
    assert not lic.permits(lic.starts_at, 101)

def test_grace_period_end_is_exclusive():
    lic = license()
    assert lic.effective_state(lic.ends_at) == LicenseState.GRACE
    assert lic.permits(lic.ends_at, 1)
    assert lic.effective_state(lic.grace_until) == LicenseState.EXPIRED
    assert not lic.permits(lic.grace_until, 1)

def test_invalid_grace_before_end_rejected():
    with pytest.raises(ValueError, match='invalid_campus_license'):
        CampusLicense('license-1','university-1','campus-annual',LicenseState.ACTIVE,
                      100,10000,NOW,NOW + timedelta(days=30),NOW + timedelta(days=2),'admin',NOW)

def test_suspended_future_license_stays_suspended():
    lic = license()
    from dataclasses import replace
    assert replace(lic,state=LicenseState.SUSPENDED).effective_state(NOW) == LicenseState.SUSPENDED

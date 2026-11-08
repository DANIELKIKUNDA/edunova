from datetime import datetime, timedelta, timezone
from app.modules.commerce.domain.combined_access import resolve_combined_access


def test_expiry_exposed_only_for_active_rights():
    now = datetime(2026, 10, 18, tzinfo=timezone.utc)
    future = now + timedelta(days=5)
    expired = now - timedelta(seconds=1)
    rights = resolve_combined_access(now=now, personal_premium_until=future,
        verified_active_membership=True, institution_id='uni-a',
        campus_license_until=expired, campus_institution_active=True,
        campus_seat_assigned=True).as_dict()
    assert rights['personal_premium_until'] == future.isoformat()
    assert rights['campus_access_until'] is None
    assert rights['campus_access'] is False


def test_campus_expiry_does_not_imply_premium():
    now = datetime(2026, 10, 18, tzinfo=timezone.utc)
    future = now + timedelta(days=1)
    rights = resolve_combined_access(now=now, personal_premium_until=None,
        verified_active_membership=True, institution_id='uni-a',
        campus_license_until=future, campus_institution_active=True,
        campus_seat_assigned=True).as_dict()
    assert rights['campus_access_until'] == future.isoformat()
    assert rights['personal_premium_until'] is None
    assert rights['personal_tier'] == 'free'


def test_expiry_not_leaked_for_unverified_membership():
    now = datetime(2026, 10, 18, tzinfo=timezone.utc)
    rights = resolve_combined_access(now=now, personal_premium_until=None,
        verified_active_membership=False, institution_id='uni-a',
        campus_license_until=now + timedelta(days=3), campus_institution_active=True,
        campus_seat_assigned=True).as_dict()
    assert rights['campus_access_until'] is None

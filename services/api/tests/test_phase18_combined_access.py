from datetime import datetime, timedelta, timezone

import pytest

from app.modules.commerce.domain.combined_access import resolve_combined_access

NOW = datetime(2026, 10, 18, tzinfo=timezone.utc)


def access(**changes):
    args = dict(now=NOW, personal_premium_until=None,
                verified_active_membership=False, institution_id=None,
                campus_license_until=None, campus_institution_active=False,
                campus_seat_assigned=False)
    args.update(changes)
    return resolve_combined_access(**args)


def campus(**changes):
    args = dict(verified_active_membership=True, institution_id='uni-a',
                campus_license_until=NOW + timedelta(days=20),
                campus_institution_active=True, campus_seat_assigned=True)
    args.update(changes)
    return access(**args)


def test_free_without_campus():
    assert access().as_dict() == dict(personal_tier='free', personal_premium=False,
                                     campus_access=False, campus_institution_id=None,
                                     personal_premium_until=None, campus_access_until=None)


def test_premium_without_campus():
    result = access(personal_premium_until=NOW + timedelta(days=1))
    assert result.personal_premium and not result.campus_access


def test_free_with_campus():
    result = campus()
    assert result.campus_access and result.tier == 'free'


def test_premium_with_campus():
    result = campus(personal_premium_until=NOW + timedelta(days=1))
    assert result.campus_access and result.personal_premium


@pytest.mark.parametrize('change', [
    {'verified_active_membership': False},
    {'institution_id': None},
    {'institution_id': ' '},
    {'campus_license_until': None},
    {'campus_license_until': NOW},
    {'campus_institution_active': False},
    {'campus_seat_assigned': False},
])
def test_campus_denial_never_removes_premium(change):
    result = campus(personal_premium_until=NOW + timedelta(days=1), **change)
    assert not result.campus_access
    assert result.personal_premium
    assert result.campus_institution_id is None


def test_expired_personal_does_not_remove_campus():
    result = campus(personal_premium_until=NOW - timedelta(seconds=1))
    assert not result.personal_premium and result.campus_access


def test_naive_expirations_fail_closed():
    result = campus(personal_premium_until=datetime(2030, 1, 1),
                    campus_license_until=datetime(2030, 1, 1))
    assert not result.personal_premium and not result.campus_access


def test_naive_now_is_rejected():
    with pytest.raises(ValueError, match='timezone_aware_now_required'):
        access(now=datetime(2026, 10, 18))

"""Phase 18: revoked Campus membership must not reveal license data."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.modules.commerce.api import router
from app.modules.campus.domain.model import MembershipState

@pytest.mark.parametrize('membership', [None, SimpleNamespace(state=MembershipState.SUSPENDED)])
def test_campus_license_status_denies_inactive_members(monkeypatch, membership):
    monkeypatch.setattr(router.runtime.campus_repo, 'membership', lambda *args: membership)
    monkeypatch.setattr(router.runtime.commercial, 'license_status', lambda *_: (_ for _ in ()).throw(AssertionError('private license lookup')))
    with pytest.raises(HTTPException) as exc:
        router.campus_license_status('university', SimpleNamespace(account_id='student'))
    assert exc.value.status_code == 403

def test_campus_license_status_allows_active_members(monkeypatch):
    monkeypatch.setattr(router.runtime.campus_repo, 'membership', lambda *args: SimpleNamespace(state=MembershipState.ACTIVE))
    monkeypatch.setattr(router.runtime.commercial, 'license_status', lambda *_: {'license': None, 'effective_state': None})
    assert router.campus_license_status('university', SimpleNamespace(account_id='student'))['license'] is None

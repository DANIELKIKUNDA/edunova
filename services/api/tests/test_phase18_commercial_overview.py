from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.modules.commerce.api import router


def test_commercial_overview_rejects_non_admin(monkeypatch):
    monkeypatch.setattr(router.runtime.campus_repo, 'institution', lambda _: SimpleNamespace(state='active'))
    monkeypatch.setattr(router.runtime.commercial, '_admin', lambda *a: (_ for _ in ()).throw(PermissionError('campus_commerce_admin_required')))
    with pytest.raises(HTTPException) as error:
        router.campus_commercial_overview('campus', SimpleNamespace(account_id='student'))
    assert error.value.status_code == 403


def test_commercial_overview_no_license(monkeypatch):
    monkeypatch.setattr(router.runtime.campus_repo, 'institution', lambda _: SimpleNamespace(state='active'))
    monkeypatch.setattr(router.runtime.commercial, '_admin', lambda *a: None)
    monkeypatch.setattr(router.runtime.commercial, 'license_status', lambda _: dict(license=None, effective_state=None, active_students=4, seat_overage=4, permitted=False))
    result = router.campus_commercial_overview('campus', SimpleNamespace(account_id='admin'))
    assert result['licensed_seats'] == 0
    assert result['seat_overage'] == 4
    assert result['access_permitted'] is False
    assert result['paid_renewal_available'] is False

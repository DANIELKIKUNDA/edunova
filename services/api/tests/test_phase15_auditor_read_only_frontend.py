"""Auditor can read but cannot create persistent statistical archives."""
import pytest
from app.modules.campus.domain.model import CampusRole
from test_institutional_analytics_lot27 import seed


def test_institutional_auditor_cannot_capture_snapshot():
    cs,_,_,_,_,ia,i,p,_,off = seed()
    cs.invite_member('owner',i.id,account_id='audit_user',role=CampusRole.AUDITOR,unit_id=None)
    cs.accept_invitation('audit_user',i.id)
    assert ia._authorize('audit_user',i.id).role == CampusRole.AUDITOR
    with pytest.raises(PermissionError,match='institutional_analytics_auditor_read_only'):
        ia.capture_snapshot('audit_user',i.id,academic_period_id=p.id,offering_id=off.id)


def test_owner_capture_authorization_remains_available():
    *_,ia,i,p,co,off = seed()
    # Existing positive snapshot regression tests cover end-to-end HMAC/SQL writes.
    assert ia._authorize('owner',i.id).role == CampusRole.OWNER

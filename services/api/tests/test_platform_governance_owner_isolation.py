"""Phase 17: owner privilege isolation (no implicit escalation)."""
from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.identity.application.service import RegisterInput

def account(label):
    a, tokens = runtime.identity.register(RegisterInput(display_name=label,email=f'{label}@example.test',phone_number=None,password='Password123!',device_name='pytest'))
    return a.id, {'Authorization': f'Bearer {tokens.access_token}'}

def test_owner_grants_and_last_owner_guards():
    owner, oh = account('p17-owner-guard')
    delegate, dh = account('p17-delegate-guard')
    runtime.platform_governance.bootstrap_owner(owner)
    c = TestClient(app)
    r=c.put(f'/v1/platform/members/{delegate}',headers=oh,json={'role':'platform_admin'})
    assert r.status_code == 200
    assert c.put(f'/v1/platform/members/{owner}',headers=dh,json={'role':'read_only_analyst','expected_version':1}).status_code == 403
    assert c.put(f'/v1/platform/members/{delegate}',headers=dh,json={'role':'owner','expected_version':1}).status_code == 403
    assert c.post(f'/v1/platform/members/{owner}/deactivate',headers=dh,json={'expected_version':1}).status_code == 403
    assert c.get('/v1/platform/members',headers=dh).status_code == 403
    assert c.get('/v1/platform/members',headers=oh).status_code == 200

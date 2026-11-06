from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.platform_governance.domain.model import PlatformRole,PERMISSIONS
from app.modules.identity.application.service import RegisterInput

def account(login):
 a,t=runtime.identity.register(RegisterInput(display_name=login,email=f'{login}@example.test',phone_number=None,password='Password123!',device_name='pytest'));return {'account_id':a.id,'access_token':t.access_token}
def auth(x):return {'Authorization':f"Bearer {x['access_token']}"}
def test_seven_roles_are_distinct_and_least_privilege():
 assert len(PlatformRole)==7
 assert 'platform.commerce.manage' in PERMISSIONS[PlatformRole.FINANCE_COMMERCIAL]
 assert 'platform.content.manage' not in PERMISSIONS[PlatformRole.FINANCE_COMMERCIAL]
 assert PERMISSIONS[PlatformRole.READ_ONLY_ANALYST]==frozenset({'platform.dashboard.analytics','platform.analytics.read'})
def test_owner_can_grant_role_and_role_cannot_manage_roles():
 owner=account('owner-recovery'); analyst=account('analyst-recovery');runtime.platform_governance.bootstrap_owner(owner['account_id'])
 c=TestClient(app);r=c.put(f"/v1/platform/members/{analyst['account_id']}",headers=auth(owner),json={'role':'read_only_analyst'});assert r.status_code==200
 r=c.get('/v1/platform/dashboard',headers=auth(analyst));assert r.status_code==200 and r.json()['role']=='read_only_analyst'
 r=c.get('/v1/platform/members',headers=auth(analyst));assert r.status_code==403
def test_finance_dashboard_has_finance_scope_without_private_content_scope():
 owner=account('owner-fin'); fin=account('finance-recovery');runtime.platform_governance.bootstrap_owner(owner['account_id'])
 c=TestClient(app);assert c.put(f"/v1/platform/members/{fin['account_id']}",headers=auth(owner),json={'role':'finance_commercial'}).status_code==200
 d=c.get('/v1/platform/dashboard',headers=auth(fin)).json();assert 'payments' in d['sections'];assert 'platform.content.read' not in d['permissions']
def test_optimistic_lock_blocks_stale_role_update():
 owner=account('owner-lock'); user=account('role-lock');runtime.platform_governance.bootstrap_owner(owner['account_id']);c=TestClient(app)
 assert c.put(f"/v1/platform/members/{user['account_id']}",headers=auth(owner),json={'role':'support_operator'}).status_code==200
 assert c.put(f"/v1/platform/members/{user['account_id']}",headers=auth(owner),json={'role':'security_audit','expected_version':1}).status_code==200
 r=c.put(f"/v1/platform/members/{user['account_id']}",headers=auth(owner),json={'role':'platform_admin','expected_version':1});assert r.status_code==409
def test_owner_cannot_self_deactivate():
 owner=account('owner-self');runtime.platform_governance.bootstrap_owner(owner['account_id']);c=TestClient(app)
 r=c.post(f"/v1/platform/members/{owner['account_id']}/deactivate",headers=auth(owner),json={'expected_version':1});assert r.status_code==422


def test_last_owner_cannot_demote_self():
 owner=account('owner-last-demote');runtime.platform_governance.bootstrap_owner(owner['account_id']);c=TestClient(app)
 r=c.put(f"/v1/platform/members/{owner['account_id']}",headers=auth(owner),json={'role':'read_only_analyst','expected_version':1});assert r.status_code==422 and r.json()['detail']=='owner_cannot_self_demote'

def test_owner_can_transfer_control_after_second_owner_exists():
 first=account('owner-transfer-a');second=account('owner-transfer-b');runtime.platform_governance.bootstrap_owner(first['account_id']);c=TestClient(app)
 r=c.put(f"/v1/platform/members/{second['account_id']}",headers=auth(first),json={'role':'owner'});assert r.status_code==200
 r=c.put(f"/v1/platform/members/{first['account_id']}",headers=auth(second),json={'role':'read_only_analyst','expected_version':1});assert r.status_code==200 and r.json()['role']=='read_only_analyst'

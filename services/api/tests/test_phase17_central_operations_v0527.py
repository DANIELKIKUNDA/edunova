from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.identity.application.service import RegisterInput
from app.modules.platform_governance.domain.model import PlatformRole


def register():
    name='central-'+uuid4().hex[:14]
    account,tokens=runtime.identity.register(RegisterInput(display_name=name,email=name+'@example.test',phone_number=None,password='Password123!',device_name='pytest'))
    return account.id,{'Authorization':'Bearer '+tokens.access_token}


def test_admin_invitation_revocation_isolation_and_version():
    owner,owner_auth=register();target,_=register();stranger,stranger_auth=register()
    runtime.platform_governance.bootstrap_owner(owner)
    campus=runtime.campus.create_institution(stranger,name='Campus '+uuid4().hex[:9],slug='camp-'+uuid4().hex[:9])
    client=TestClient(app);url=f'/v1/platform/institutions/{campus.id}/administrators'
    assert client.get(url,headers=stranger_auth).status_code==403
    assert client.put(url,headers=stranger_auth,json={'account_id':target,'role':'admin'}).status_code==403
    result=client.put(url,headers=owner_auth,json={'account_id':target,'role':'admin'})
    assert result.status_code==200,result.text
    assert result.json()['state']=='invited'
    assert len(client.get(url,headers=owner_auth).json())==1
    assert client.put(url,headers=owner_auth,json={'account_id':target,'role':'rector','expected_version':1}).status_code==422
    assert client.put(url,headers=owner_auth,json={'account_id':target,'role':'academic_admin','expected_version':99}).status_code==409
    assert client.put(url,headers=owner_auth,json={'account_id':target,'role':'academic_admin','expected_version':1}).status_code==200
    revoke=client.post(url+'/'+target+'/revoke',headers=owner_auth,json={'expected_version':2})
    assert revoke.status_code==200,revoke.text
    assert revoke.json()['state']=='revoked'
    assert client.post(url+'/'+target+'/revoke',headers=owner_auth,json={'expected_version':2}).status_code==409
    # Central operations must not expose student/financial data.
    assert set(revoke.json())=={'id','institution_id','account_id','role','state','invited_by','row_version'}


def test_support_lifecycle_rbac_and_conflict():
    owner,owner_auth=register();stranger,stranger_auth=register()
    runtime.platform_governance.bootstrap_owner(owner)
    campus=runtime.campus.create_institution(stranger,name='Campus '+uuid4().hex[:9],slug='camp-'+uuid4().hex[:9])
    client=TestClient(app);url='/v1/platform/support/tickets'
    assert client.get(url,headers=stranger_auth).status_code==403
    body={'institution_id':campus.id,'title':'Problème de connexion','description':'Le portail administratif affiche une erreur 503.','priority':'high'}
    assert client.post(url,headers=stranger_auth,json=body).status_code==403
    created=client.post(url,headers=owner_auth,json=body)
    assert created.status_code==201,created.text
    ticket=created.json();assert ticket['row_version']==1
    assert client.get(url,headers=owner_auth,params={'institution_id':campus.id}).json()['total']>=1
    assert client.put(url+'/'+ticket['id'],headers=owner_auth,json={'state':'resolved','expected_version':99}).status_code==409
    updated=client.put(url+'/'+ticket['id'],headers=owner_auth,json={'state':'in_progress','expected_version':1})
    assert updated.status_code==200,updated.text
    assert updated.json()['row_version']==2
    assert client.put(url+'/'+ticket['id'],headers=owner_auth,json={'state':'closed','expected_version':2}).status_code==422
    assert client.put(url+'/'+ticket['id'],headers=owner_auth,json={'state':'resolved','expected_version':2}).status_code==200
    assert client.put(url+'/'+ticket['id'],headers=owner_auth,json={'state':'closed','expected_version':3}).status_code==200
    assert client.put(url+'/'+ticket['id'],headers=owner_auth,json={'state':'open','expected_version':4}).status_code==422
    assert client.get(url,headers=owner_auth,params={'state':'unknown'}).status_code==422


def test_platform_role_least_privilege():
    owner,_=register();runtime.platform_governance.bootstrap_owner(owner)
    member,_=register();runtime.platform_governance.grant(owner,member,PlatformRole.SUPPORT_OPERATOR)
    permissions=runtime.platform_governance.membership(member).permissions
    assert 'platform.support.manage' in permissions
    assert 'platform.assignments.manage' not in permissions
    assert 'platform.roles.manage' not in permissions

from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.identity.application.service import RegisterInput


def make_account():
    name='control-'+uuid4().hex[:14]
    a,t=runtime.identity.register(RegisterInput(display_name=name,email=f'{name}@example.test',phone_number=None,password='Password123!',device_name='pytest'))
    return a.id,{'Authorization':f'Bearer {t.access_token}'}


def test_institution_control_requires_platform_scope_and_changes_canonical_state():
    owner,oh=make_account(); other,sh=make_account()
    runtime.platform_governance.bootstrap_owner(owner)
    inst=runtime.campus.create_institution(other,name='Campus contrôlé',slug='ctrl-'+uuid4().hex[:12])
    client=TestClient(app);url=f'/v1/platform/institutions/{inst.id}/control'
    assert client.get('/v1/platform/institutions/controls',headers=sh).status_code==403
    assert client.put(url,headers=sh,json={'state':'suspended','reason':'Suspension administrative contrôlée'}).status_code==403
    result=client.put(url,headers=oh,json={'state':'suspended','reason':'Suspension administrative contrôlée'})
    assert result.status_code==200,result.text
    assert result.json()['row_version']==1
    assert runtime.campus_repo.institution(inst.id).state.value=='suspended'
    assert client.put(url,headers=oh,json={'state':'active','reason':'Réactivation administrative contrôlée','expected_version':0}).status_code==422
    assert client.put(url,headers=oh,json={'state':'active','reason':'Réactivation administrative contrôlée','expected_version':1}).status_code==200
    assert runtime.campus_repo.institution(inst.id).state.value=='active'
    assert client.put(url,headers=oh,json={'state':'suspended','reason':'Ancienne requête concurrente','expected_version':1}).status_code==409
    assert runtime.campus_repo.institution(inst.id).state.value=='active'


def test_institution_control_rejects_unknown_institution_and_invalid_reason():
    owner,headers=make_account();runtime.platform_governance.bootstrap_owner(owner)
    client=TestClient(app)
    assert client.put('/v1/platform/institutions/missing/control',headers=headers,json={'state':'suspended','reason':'Motif suffisamment long'}).status_code==422
    assert client.put('/v1/platform/institutions/missing/control',headers=headers,json={'state':'deleted','reason':'Motif suffisamment long'}).status_code==422

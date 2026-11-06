from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.identity.application.service import RegisterInput


def account():
    name = 'directory-' + uuid4().hex[:12]
    obj, tokens = runtime.identity.register(RegisterInput(display_name=name, email=name+'@example.test', phone_number=None, password='Password123!', device_name='pytest'))
    return obj.id, {'Authorization': 'Bearer ' + tokens.access_token}


def test_directory_authorization_pagination_filter_and_minimal_projection():
    owner, auth = account()
    stranger, other_auth = account()
    runtime.platform_governance.bootstrap_owner(owner)
    unique = uuid4().hex[:12]
    inst = runtime.campus.create_institution(stranger, name='Campus '+unique, slug='directory-'+unique)
    client = TestClient(app)
    url = '/v1/platform/institutions/directory'
    assert client.get(url, headers=other_auth).status_code == 403
    response = client.get(url, headers=auth, params={'search':unique,'limit':1,'offset':0})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['total'] == 1 and len(data['items']) == 1
    row = data['items'][0]
    assert row['institution_id'] == inst.id
    assert set(row) == {'institution_id','name','slug','country_code','city','state','row_version'}
    assert client.get(url, headers=auth, params={'search':unique,'offset':1}).json()['items'] == []
    assert client.get(url, headers=auth, params={'state':'bad'}).status_code == 422
    assert client.get(url, headers=auth, params={'limit':101}).status_code == 422
    assert client.get(url, headers=auth, params={'offset':-1}).status_code == 422
    assert client.get(url, headers=auth, params={'search':unique,'state':'suspended'}).json()['total'] == 0

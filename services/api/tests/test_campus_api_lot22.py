from fastapi.testclient import TestClient
from app.main import app
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
client=TestClient(app)
def test_campus_api_tenant_isolation_and_overview():
 app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='lot22-owner-a')
 try:
  r=client.post('/v1/campus/institutions',json={'name':'Université LOT22 A','slug':'lot22-a','country_code':'CD'});assert r.status_code==200,r.text;iid=r.json()['id']
  assert client.get(f'/v1/campus/institutions/{iid}/overview').status_code==200
  assert client.post(f'/v1/campus/institutions/{iid}/units',json={'kind':'faculty','name':'Médecine','code':'MED'}).status_code==200
  app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='lot22-outsider')
  denied=client.get(f'/v1/campus/institutions/{iid}');assert denied.status_code==403
 finally:app.dependency_overrides.pop(current_auth,None)
def test_campus_api_invitation_requires_acceptance():
 app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='lot22-owner-b')
 try:
  r=client.post('/v1/campus/institutions',json={'name':'Université LOT22 B','slug':'lot22-b','country_code':'CD'});assert r.status_code==200;iid=r.json()['id']
  r=client.post(f'/v1/campus/institutions/{iid}/members/invitations',json={'account_id':'lot22-student','role':'student'});assert r.status_code==200 and r.json()['state']=='invited'
  app.dependency_overrides[current_auth]=lambda:AuthContext(account_id='lot22-student')
  r=client.post(f'/v1/campus/institutions/{iid}/members/accept');assert r.status_code==200 and r.json()['state']=='active'
 finally:app.dependency_overrides.pop(current_auth,None)

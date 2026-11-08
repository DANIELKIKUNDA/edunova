from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.editorial.domain.model import EditorialMember,EditorialRole

def _token(account_id):
    # tests use an existing account created via identity endpoint
    r=TestClient(app).post('/v1/identity/register',json={'display_name':'Ed','email':f'{account_id}@example.com','password':'StrongPass123!','device_name':'test'})
    return r.json()['access_token'], r.json()['account_id']

def test_editorial_end_to_end_api():
    c=TestClient(app); tok,aid=_token('lot11editor'); runtime.editorial_repository.save_member(EditorialMember(aid,EditorialRole.OWNER))
    h={'Authorization':f'Bearer {tok}'}
    r=c.post('/v1/editorial/items',headers=h,json={'kind':'course','title':'Anatomie','faculty_domain':'Médecine','program':'Médecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','source_fingerprint':'src'}); assert r.status_code==200; iid=r.json()['id']
    assert c.post(f'/v1/editorial/items/{iid}/revisions',headers=h,json={'payload':{'summary':'test'},'source_fingerprint':'src','ai_generated':True,'prompt_version':'v1'}).status_code==200
    assert c.post(f'/v1/editorial/items/{iid}/submit-review',headers=h).status_code==200
    # owner bypasses role, but four-eyes still prevents self-review of medical item
    assert c.post(f'/v1/editorial/items/{iid}/review',headers=h,json={'approve':True,'comment':'ok'}).status_code==422

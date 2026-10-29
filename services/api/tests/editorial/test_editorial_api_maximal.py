from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.editorial.domain.model import EditorialMember,EditorialRole


def _owner(prefix='lot11max'):
    c=TestClient(app)
    r=c.post('/v1/identity/register',json={'display_name':'Owner','email':f'{prefix}@example.com','password':'StrongPass123!','device_name':'studio'})
    assert r.status_code==201, r.text
    aid=r.json()['account_id']; runtime.editorial_repository.save_member(EditorialMember(aid,EditorialRole.OWNER))
    return c,{'Authorization':f"Bearer {r.json()['access_token']}"}


def test_editorial_detail_search_and_optimistic_conflict():
    c,h=_owner()
    r=c.post('/v1/editorial/items',headers=h,json={'kind':'assessment','title':'Interrogation Physiologie','faculty_domain':'Médecine','program':'Médecine humaine','level':'BAC1','semester':'S1','risk':'standard','rights_status':'authorized','source_fingerprint':'src'})
    assert r.status_code==200; item=r.json(); iid=item['id']; assert item['row_version']==1
    r=c.patch(f'/v1/editorial/items/{iid}',headers=h,json={'title':'Interrogation Physiologie I','expected_version':1}); assert r.status_code==200 and r.json()['row_version']==2
    stale=c.patch(f'/v1/editorial/items/{iid}',headers=h,json={'title':'Ancien titre','expected_version':1}); assert stale.status_code==409
    rv=c.post(f'/v1/editorial/items/{iid}/revisions',headers=h,json={'payload':{'questions':[{'q':'Q1'}]},'source_fingerprint':'src','expected_version':2}); assert rv.status_code==200
    sr=c.get('/v1/editorial/items/search?q=physiologie&kind=assessment',headers=h); assert sr.status_code==200 and sr.json()['total']>=1
    d=c.get(f'/v1/editorial/items/{iid}',headers=h); assert d.status_code==200 and d.json()['item']['row_version']==3 and len(d.json()['audit'])>=2
    assert c.post(f'/v1/editorial/items/{iid}/submit-review',headers=h,json={'expected_version':3}).status_code==200
    rr=c.post(f'/v1/editorial/items/{iid}/review',headers=h,json={'approve':True,'checklist':{'source_traceability':True,'structure_quality':True,'rights_checked':True},'quality_score':100,'expected_version':4}); assert rr.status_code==200
    pub=c.post(f'/v1/editorial/items/{iid}/publish',headers=h,json={'changelog':'Publication initiale','expected_version':5}); assert pub.status_code==200 and pub.json()['state']=='published'
    d2=c.get(f'/v1/editorial/items/{iid}',headers=h).json(); assert len(d2['publications'])==1 and d2['publish_gates']

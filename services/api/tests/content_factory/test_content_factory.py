import io,uuid
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from app.main import app
from app.runtime import runtime
from app.modules.editorial.domain.model import EditorialMember,EditorialRole
from app.modules.identity.application.service import RegisterInput
client=TestClient(app)
def pdf_bytes(text):
 b=io.BytesIO(); c=canvas.Canvas(b); c.drawString(72,760,text); c.drawString(72,730,'La membrane cellulaire controle les echanges et maintient homeostasie.'); c.showPage(); c.save(); return b.getvalue()
def account():
 email=f'factory-{uuid.uuid4().hex[:8]}@example.com'; acc,tokens=runtime.identity.register(RegisterInput(display_name='Factory Owner',password='StrongPass!123',email=email,phone_number=None,device_name='studio')); aid=acc.id; runtime.editorial_repository.save_member(EditorialMember(aid,EditorialRole.OWNER,True)); return aid,{'Authorization':f'Bearer {tokens.access_token}'}
def processed(h):
 b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
def test_factory_end_to_end_ready_for_review_with_evidence():
 _,h=account(); did=processed(h); cr=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did}); assert cr.status_code==200,cr.text; rid=cr.json()['id']; pr=client.post(f'/v1/content-factory/runs/{rid}/process',headers=h); assert pr.status_code==200,pr.text; assert pr.json()['state']=='ready_for_review'; detail=client.get(f'/v1/content-factory/runs/{rid}',headers=h).json(); assert detail['assets']; assert len(detail['assets'])==len(detail['evidence']); assert all(e['page_start']>=1 for e in detail['evidence']); assert any(g['code']=='provenance_complete' and g['passed'] for g in detail['quality_gates'])
def test_factory_create_is_idempotent_for_same_source_and_asset_contract():
 _,h=account(); did=processed(h); body={'document_id':did,'requested_assets':['summary_express','rag_chunk']}; a=client.post('/v1/content-factory/runs',headers=h,json=body).json(); b=client.post('/v1/content-factory/runs',headers=h,json=body).json(); assert a['id']==b['id']
def test_factory_rejects_unknown_asset_family():
 _,h=account(); did=processed(h); r=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['telepathy']}); assert r.status_code==422
def test_factory_never_publishes_and_exposes_quality_score():
 _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['summary_express','quiz']}).json(); out=client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h).json(); assert out['state']=='ready_for_review'; assert 0<=out['quality_score']<=100; assert 'published' not in out['state']
def test_factory_final_quality_gates_include_grounding_integrity():
 _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['summary_express','quiz']}).json(); client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h); detail=client.get(f"/v1/content-factory/runs/{run['id']}",headers=h).json(); gates={g['code']:g for g in detail['quality_gates']}; assert gates['evidence_quote_grounded']['passed']; assert gates['evidence_hash_integrity']['passed']; assert gates['numeric_claim_grounding']['passed']
def test_factory_queued_run_can_be_cancelled_and_not_processed():
 _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['rag_chunk']}).json(); out=client.post(f"/v1/content-factory/runs/{run['id']}/cancel",headers=h); assert out.status_code==200; assert out.json()['state']=='cancelled'; pr=client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h); assert pr.status_code==422
def test_factory_review_package_pairs_every_asset_with_source_evidence_and_blocks_publication():
 _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['summary_express','quiz']}).json(); client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h); r=client.get(f"/v1/content-factory/runs/{run['id']}/review-package",headers=h); assert r.status_code==200; body=r.json(); assert body['publication_allowed'] is False; assert body['required_next_state']=='human_review'; assert body['items'] and all(x['evidence'] for x in body['items'])

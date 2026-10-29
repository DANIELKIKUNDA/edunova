from __future__ import annotations

from uuid import uuid4
import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.runtime import runtime
from app.modules.editorial.domain.model import EditorialMember,EditorialRole
from app.modules.identity.application.service import RegisterInput

client=TestClient(app)


def pdf_bytes(text='Cours de physiologie — Potentiel action sodium membrane'):
    doc=fitz.open(); page=doc.new_page(); page.insert_text((72,72),text); payload=doc.tobytes(); doc.close(); return payload


def account(role=EditorialRole.OWNER):
    email=f'ing-{uuid4().hex}@test.local'
    acc,tokens=runtime.identity.register(RegisterInput(display_name='Ingestion User',password='StrongPass123!',email=email,phone_number=None,device_name='studio'))
    aid=acc.id; runtime.editorial_repository.save_member(EditorialMember(aid,role,True))
    return aid,{'Authorization':f"Bearer {tokens.access_token}"}


def create_batch(h,name='BAC1 septembre'):
    r=client.post('/v1/ingestion/batches',headers=h,json={'name':name,'defaults':{'content_kind':'course','faculty_domain':'Médecine','program':'Médecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'Pilote'}})
    assert r.status_code==200,r.text
    return r.json()


def test_batch_upload_idempotency_freeze_worker_and_editorial_projection():
    _,h=account(); batch=create_batch(h); bid=batch['id']; payload=pdf_bytes()
    files={'file':('physio.pdf',payload,'application/pdf')}
    r=client.post(f'/v1/ingestion/batches/{bid}/files',headers={**h,'Idempotency-Key':'u-1'},files=files)
    assert r.status_code==200,r.text; doc=r.json(); assert doc['preflight_status']=='passed'
    r2=client.post(f'/v1/ingestion/batches/{bid}/files',headers={**h,'Idempotency-Key':'u-1'},files=files)
    assert r2.status_code==200 and r2.json()['id']==doc['id']
    start=client.post(f'/v1/ingestion/batches/{bid}/start',headers=h,json={'priority':80}); assert start.status_code==200 and start.json()['manifest_sha256']
    blocked=client.post(f'/v1/ingestion/batches/{bid}/files',headers={**h,'Idempotency-Key':'u-2'},files={'file':('x.pdf',pdf_bytes('autre'),'application/pdf')})
    assert blocked.status_code==409
    job=runtime.ingestion.claim_job(worker_id='pytest-worker'); assert job is not None
    result=runtime.ingestion.process_job(worker_id='pytest-worker',job_id=job.id)
    assert result.editorial_item_id and len(result.artifact_sha256)==64 and result.pipeline_version=='document-engine-v1'
    detail=client.get(f'/v1/ingestion/batches/{bid}',headers=h).json()
    assert detail['batch']['state']=='completed' and detail['metrics']['succeeded']==1
    ed=client.get(f"/v1/editorial/items/{result.editorial_item_id}",headers=h); assert ed.status_code==200
    assert ed.json()['item']['source_fingerprint']==doc['checksum_sha256']


def test_bad_file_is_rejected_but_auditable():
    _,h=account(); bid=create_batch(h,'Lot mauvais')['id']
    r=client.post(f'/v1/ingestion/batches/{bid}/files',headers={**h,'Idempotency-Key':'bad-1'},files={'file':('fake.pdf',b'hello world','application/pdf')})
    assert r.status_code==200; j=r.json(); assert j['state']=='rejected' and j['rejection_code']
    assert client.post(f'/v1/ingestion/batches/{bid}/start',headers=h,json={}).status_code==422


def test_reviewer_cannot_create_ingestion_batch():
    _,h=account(EditorialRole.REVIEWER)
    r=client.post('/v1/ingestion/batches',headers=h,json={'name':'Interdit','defaults':{'content_kind':'course','faculty_domain':'Médecine','program':'Médecine','level':'BAC1','risk':'standard','rights_status':'authorized'}})
    assert r.status_code==403


def test_remove_file_only_before_manifest_freeze():
    _,h=account(); bid=create_batch(h,'Suppression')['id']; payload=pdf_bytes('temp')
    r=client.post(f'/v1/ingestion/batches/{bid}/files',headers={**h,'Idempotency-Key':'rm'},files={'file':('tmp.pdf',payload,'application/pdf')}); did=r.json()['id']
    assert client.delete(f'/v1/ingestion/batches/{bid}/files/{did}',headers=h).status_code==204


def test_report_contains_operational_metrics():
    _,h=account(); bid=create_batch(h,'Rapport')['id']
    client.post(f'/v1/ingestion/batches/{bid}/files',headers={**h,'Idempotency-Key':'r1'},files={'file':('x.pdf',pdf_bytes(),'application/pdf')})
    report=client.get(f'/v1/ingestion/batches/{bid}/report',headers=h)
    assert report.status_code==200 and report.json()['metrics']['total_documents']==1

def test_global_dedup_reuses_already_processed_document_without_second_ocr():
    _,h=account(); payload=pdf_bytes('Document global unique ' + uuid4().hex)
    b1=create_batch(h,'Premier lot'); d1=client.post(f"/v1/ingestion/batches/{b1['id']}/files",headers={**h,'Idempotency-Key':'g1'},files={'file':('g.pdf',payload,'application/pdf')}).json()
    client.post(f"/v1/ingestion/batches/{b1['id']}/start",headers=h,json={})
    j=runtime.ingestion.claim_job(worker_id='dedup-worker'); r1=runtime.ingestion.process_job(worker_id='dedup-worker',job_id=j.id)
    b2=create_batch(h,'Deuxième lot'); d2=client.post(f"/v1/ingestion/batches/{b2['id']}/files",headers={**h,'Idempotency-Key':'g2'},files={'file':('same.pdf',payload,'application/pdf')}).json()
    assert d2['state']=='succeeded' and d2['editorial_item_id']==r1.editorial_item_id and d2['id']!=d1['id']
    started=client.post(f"/v1/ingestion/batches/{b2['id']}/start",headers=h,json={}).json()
    assert started['state']=='completed'
    assert runtime.ingestion_repository.list_jobs(b2['id'])==()


def test_preview_and_global_dashboard_after_processing():
    _,h=account(); payload=pdf_bytes('Question 1. Définir la membrane cellulaire. ' + uuid4().hex)
    b=create_batch(h,'Preview lot'); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'p1'},files={'file':('preview.pdf',payload,'application/pdf')}).json()
    client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='preview-worker'); runtime.ingestion.process_job(worker_id='preview-worker',job_id=j.id)
    prev=client.get(f"/v1/ingestion/documents/{d['id']}/preview?page=1",headers=h); assert prev.status_code==200 and prev.json()['page']['number']==1
    dash=client.get('/v1/ingestion/dashboard',headers=h); assert dash.status_code==200 and 'backlog_jobs' in dash.json()

def test_ingestion_detail_contains_audit_trail():
    _,h=account(); bid=create_batch(h,'Audit lot')['id']
    client.post(f'/v1/ingestion/batches/{bid}/files',headers={**h,'Idempotency-Key':'a1'},files={'file':('a.pdf',pdf_bytes('audit'),'application/pdf')})
    d=client.get(f'/v1/ingestion/batches/{bid}',headers=h).json()
    actions={x['action'] for x in d['audit']}
    assert 'ingestion.batch.created' in actions and 'ingestion.document.accepted' in actions

def test_multi_page_image_bundle_becomes_one_logical_pdf():
    import io
    from PIL import Image
    _,h=account(); bid=create_batch(h,'Bundle photos')['id']
    def img(text_color):
        b=io.BytesIO(); Image.new('RGB',(300,200),text_color).save(b,format='JPEG'); return b.getvalue()
    files=[('files',('p1.jpg',img('white'),'image/jpeg')),('files',('p2.jpg',img('gray'),'image/jpeg'))]
    r=client.post(f'/v1/ingestion/batches/{bid}/image-bundles?bundle_name=Interrogation%20Anatomie',headers={**h,'Idempotency-Key':'bundle-1'},files=files)
    assert r.status_code==200,r.text
    j=r.json(); assert j['detected_mime_type']=='application/pdf' and j['page_count']==2 and j['filename'].endswith('.pdf')

def test_global_dedup_never_reuses_rights_or_academic_context_silently():
    _,h=account(); payload=pdf_bytes('Same bytes different rights ' + uuid4().hex)
    b1=create_batch(h,'Contexte A'); client.post(f"/v1/ingestion/batches/{b1['id']}/files",headers={**h,'Idempotency-Key':'cx1'},files={'file':('same.pdf',payload,'application/pdf')}); client.post(f"/v1/ingestion/batches/{b1['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='ctx-worker'); runtime.ingestion.process_job(worker_id='ctx-worker',job_id=j.id)
    r=client.post('/v1/ingestion/batches',headers=h,json={'name':'Contexte B','defaults':{'content_kind':'course','faculty_domain':'Médecine','program':'Médecine humaine','level':'BAC2','semester':'S1','risk':'medical','rights_status':'unknown','rights_note':''}}); b2=r.json()
    d=client.post(f"/v1/ingestion/batches/{b2['id']}/files",headers={**h,'Idempotency-Key':'cx2'},files={'file':('same.pdf',payload,'application/pdf')}).json()
    assert d['state']=='rejected' and d['rejection_code']=='duplicate_source_different_context'


def test_frozen_manifest_snapshot_is_persisted_and_verifiable():
    _,h=account(); bid=create_batch(h,'Manifest integrity')['id']
    payload=pdf_bytes('Manifest immutable ' + uuid4().hex)
    client.post(f'/v1/ingestion/batches/{bid}/files',headers={**h,'Idempotency-Key':'manifest-1'},files={'file':('manifest.pdf',payload,'application/pdf')})
    started=client.post(f'/v1/ingestion/batches/{bid}/start',headers=h,json={'priority':70})
    assert started.status_code==200 and started.json()['manifest_snapshot_available'] is True
    verify=client.get(f'/v1/ingestion/batches/{bid}/manifest/verify',headers=h)
    assert verify.status_code==200,verify.text
    body=verify.json(); assert body['valid'] is True and body['hash_valid'] is True and body['documents_valid'] is True and body['document_count']==1
    report=client.get(f'/v1/ingestion/batches/{bid}/report',headers=h).json()
    assert report['manifest_integrity']['valid'] is True
    job=runtime.ingestion.claim_job(worker_id='manifest-worker'); assert job
    runtime.ingestion.process_job(worker_id='manifest-worker',job_id=job.id)


def test_bulk_dead_letter_retry_is_owner_controlled():
    from dataclasses import replace
    from app.modules.ingestion.domain.model import JobState,DocumentState
    _,h=account(); bid=create_batch(h,'Bulk retry')['id']
    client.post(f'/v1/ingestion/batches/{bid}/files',headers={**h,'Idempotency-Key':'bulk-1'},files={'file':('bulk.pdf',pdf_bytes('bulk retry'),'application/pdf')})
    client.post(f'/v1/ingestion/batches/{bid}/start',headers=h,json={})
    job=runtime.ingestion_repository.list_jobs(bid)[0]
    # Force a terminal failure deterministically without depending on OCR behavior.
    dead=replace(job,state=JobState.DEAD_LETTER,attempt=job.max_attempts,lease_owner=None,lease_expires_at=None,heartbeat_at=None,last_error='forced',completed_at=job.updated_at)
    runtime.ingestion_repository.save_job(dead)
    doc=runtime.ingestion_repository.get_document(job.document_id)
    runtime.ingestion_repository.save_document(replace(doc,state=DocumentState.DEAD_LETTER,rejection_code='processing_failed'))
    r=client.post(f'/v1/ingestion/batches/{bid}/dead-letters/retry',headers=h)
    assert r.status_code==200,r.text
    assert r.json()['retried']==1
    retried=runtime.ingestion_repository.get_job(job.id)
    assert retried.state==JobState.RETRY and retried.attempt==0
    client.post(f'/v1/ingestion/batches/{bid}/cancel',headers=h)

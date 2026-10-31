# Annexe des échecs et corrections

Les traces complètes sont conservées dans les XML et journaux cités. Les anciennes tentatives ne sont pas des échecs résiduels si une reprise correspondante a réussi.

## backend-final-previous-1793433709429319500 — test_batch_upload_idempotency_freeze_worker_and_editorial_projection

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_batch_upload_idempotency_freeze_worker_and_editorial_projection'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
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
>       result=runtime.ingestion.process_job(worker_id='pytest-worker',job_id=job.id)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\ingestion\test_ingestion_api.py:43: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmpgzvny26d.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       PermissionError: [Errno 13] Permission denied: 'C:\\Users\\cs-ap\\AppData\\Local\\Temp\\tmpgzvny26d.pdf'

..\..\..\AppData\Local\Programs\Python\Python313\Lib\pathlib\_local.py:537: PermissionError
```

## backend-final-previous-1793433709429319500 — test_global_dedup_reuses_already_processed_document_without_second_ocr

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_global_dedup_reuses_already_processed_document_without_second_ocr'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_global_dedup_reuses_already_processed_document_without_second_ocr():
        _,h=account(); payload=pdf_bytes('Document global unique ' + uuid4().hex)
        b1=create_batch(h,'Premier lot'); d1=client.post(f"/v1/ingestion/batches/{b1['id']}/files",headers={**h,'Idempotency-Key':'g1'},files={'file':('g.pdf',payload,'application/pdf')}).json()
        client.post(f"/v1/ingestion/batches/{b1['id']}/start",headers=h,json={})
>       j=runtime.ingestion.claim_job(worker_id='dedup-worker'); r1=runtime.ingestion.process_job(worker_id='dedup-worker',job_id=j.id)
                                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\ingestion\test_ingestion_api.py:80: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmphm25sdt_.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       PermissionError: [Errno 13] Permission denied: 'C:\\Users\\cs-ap\\AppData\\Local\\Temp\\tmphm25sdt_.pdf'

..\..\..\AppData\Local\Programs\Python\Python313\Lib\pathlib\_local.py:537: PermissionError
```

## backend-final-previous-1793433709429319500 — test_preview_and_global_dashboard_after_processing

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_preview_and_global_dashboard_after_processing'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_preview_and_global_dashboard_after_processing():
        _,h=account(); payload=pdf_bytes('Question 1. Définir la membrane cellulaire. ' + uuid4().hex)
        b=create_batch(h,'Preview lot'); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'p1'},files={'file':('preview.pdf',payload,'application/pdf')}).json()
>       client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='preview-worker'); runtime.ingestion.process_job(worker_id='preview-worker',job_id=j.id)
                                                                                                                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\ingestion\test_ingestion_api.py:91: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmpcq8lvkn1.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       PermissionError: [Errno 13] Permission denied: 'C:\\Users\\cs-ap\\AppData\\Local\\Temp\\tmpcq8lvkn1.pdf'

..\..\..\AppData\Local\Programs\Python\Python313\Lib\pathlib\_local.py:537: PermissionError
```

## backend-final-previous-1793433709429319500 — test_global_dedup_never_reuses_rights_or_academic_context_silently

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_global_dedup_never_reuses_rights_or_academic_context_silently'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_global_dedup_never_reuses_rights_or_academic_context_silently():
        _,h=account(); payload=pdf_bytes('Same bytes different rights ' + uuid4().hex)
>       b1=create_batch(h,'Contexte A'); client.post(f"/v1/ingestion/batches/{b1['id']}/files",headers={**h,'Idempotency-Key':'cx1'},files={'file':('same.pdf',payload,'application/pdf')}); client.post(f"/v1/ingestion/batches/{b1['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='ctx-worker'); runtime.ingestion.process_job(worker_id='ctx-worker',job_id=j.id)
                                                                                                                                                                                                                                                                                                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\ingestion\test_ingestion_api.py:115: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmphwun1rr3.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       PermissionError: [Errno 13] Permission denied: 'C:\\Users\\cs-ap\\AppData\\Local\\Temp\\tmphwun1rr3.pdf'

..\..\..\AppData\Local\Programs\Python\Python313\Lib\pathlib\_local.py:537: PermissionError
```

## backend-final-previous-1793433709429319500 — test_frozen_manifest_snapshot_is_persisted_and_verifiable

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_frozen_manifest_snapshot_is_persisted_and_verifiable'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
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
>       runtime.ingestion.process_job(worker_id='manifest-worker',job_id=job.id)

services\api\tests\ingestion\test_ingestion_api.py:133: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmpfd6i72j2.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       PermissionError: [Errno 13] Permission denied: 'C:\\Users\\cs-ap\\AppData\\Local\\Temp\\tmpfd6i72j2.pdf'

..\..\..\AppData\Local\Programs\Python\Python313\Lib\pathlib\_local.py:537: PermissionError
```

## backend-final-previous-1793433709429319500 — test_factory_end_to_end_ready_for_review_with_evidence

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_end_to_end_ready_for_review_with_evidence'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_factory_end_to_end_ready_for_review_with_evidence():
>    _,h=account(); did=processed(h); cr=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did}); assert cr.status_code==200,cr.text; rid=cr.json()['id']; pr=client.post(f'/v1/content-factory/runs/{rid}/process',headers=h); assert pr.status_code==200,pr.text; assert pr.json()['state']=='ready_for_review'; detail=client.get(f'/v1/content-factory/runs/{rid}',headers=h).json(); assert detail['assets']; assert len(detail['assets'])==len(detail['evidence']); assert all(e['page_start']>=1 for e in detail['evidence']); assert any(g['code']=='provenance_complete' and g['passed'] for g in detail['quality_gates'])
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:16: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmphkufy4ye.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(e
```

## backend-final-previous-1793433709429319500 — test_factory_create_is_idempotent_for_same_source_and_asset_contract

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_create_is_idempotent_for_same_source_and_asset_contract'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_factory_create_is_idempotent_for_same_source_and_asset_contract():
>    _,h=account(); did=processed(h); body={'document_id':did,'requested_assets':['summary_express','rag_chunk']}; a=client.post('/v1/content-factory/runs',headers=h,json=body).json(); b=client.post('/v1/content-factory/runs',headers=h,json=body).json(); assert a['id']==b['id']
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:18: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmpd5rhwytg.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       PermissionError: [Errno 13] Permission denied: 'C:\\Users\\cs-ap\\AppData\\Local\\Temp\\tmpd5rhwytg.pdf'

..\..\..\AppData\Local\Programs\Python\Python313\Lib\pathlib\_local.p
```

## backend-final-previous-1793433709429319500 — test_factory_rejects_unknown_asset_family

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_rejects_unknown_asset_family'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_factory_rejects_unknown_asset_family():
>    _,h=account(); did=processed(h); r=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['telepathy']}); assert r.status_code==422
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:20: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmpobc9k5pt.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       PermissionError: [Errno 13] Permission denied: 'C:\\Users\\cs-ap\\AppData\\Local\\Temp\\tmpobc9k5pt.pdf'

..\..\..\AppData\Local\Programs\Python\Python313\Lib\pathlib\_local.py:537: PermissionError
```

## backend-final-previous-1793433709429319500 — test_factory_never_publishes_and_exposes_quality_score

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_never_publishes_and_exposes_quality_score'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_factory_never_publishes_and_exposes_quality_score():
>    _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['summary_express','quiz']}).json(); out=client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h).json(); assert out['state']=='ready_for_review'; assert 0<=out['quality_score']<=100; assert 'published' not in out['state']
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:22: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmp5ojoz65a.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       PermissionError: [Errno 13] Permission denied: 'C:\\Users\\cs-ap\\AppData\\Local\\Temp\\tmp5ojoz6
```

## backend-final-previous-1793433709429319500 — test_factory_final_quality_gates_include_grounding_integrity

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_final_quality_gates_include_grounding_integrity'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_factory_final_quality_gates_include_grounding_integrity():
>    _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['summary_express','quiz']}).json(); client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h); detail=client.get(f"/v1/content-factory/runs/{run['id']}",headers=h).json(); gates={g['code']:g for g in detail['quality_gates']}; assert gates['evidence_quote_grounded']['passed']; assert gates['evidence_hash_integrity']['passed']; assert gates['numeric_claim_grounding']['passed']
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:24: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmphqojmsvb.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^
```

## backend-final-previous-1793433709429319500 — test_factory_queued_run_can_be_cancelled_and_not_processed

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_queued_run_can_be_cancelled_and_not_processed'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_factory_queued_run_can_be_cancelled_and_not_processed():
>    _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['rag_chunk']}).json(); out=client.post(f"/v1/content-factory/runs/{run['id']}/cancel",headers=h); assert out.status_code==200; assert out.json()['state']=='cancelled'; pr=client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h); assert pr.status_code==422
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:26: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmpbkmsfoao.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       PermissionError: [Errno 13] Permission denied: 'C:\\Users\\
```

## backend-final-previous-1793433709429319500 — test_factory_review_package_pairs_every_asset_with_source_evidence_and_blocks_publication

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_review_package_pairs_every_asset_with_source_evidence_and_blocks_publication'`.

Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_factory_review_package_pairs_every_asset_with_source_evidence_and_blocks_publication():
>    _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['summary_express','quiz']}).json(); client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h); r=client.get(f"/v1/content-factory/runs/{run['id']}/review-package",headers=h); assert r.status_code==200; body=r.json(); assert body['publication_allowed'] is False; assert body['required_next_state']=='human_review'; assert body['items'] and all(x['evidence'] for x in body['items'])
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:28: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:35: in process
    fingerprint = _sha256(path)
                  ^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:71: in _sha256
    with path.open("rb") as handle:
         ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/tmpto9hrxz2.pdf')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """
        Open the file pointed to by this path and return a file object, as
        the built-in open() function does.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, er
```

## backend-final-previous-1793433709429319500 — test_question_candidates_from_interrogation_photo

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/document_engine/test_pipeline.py::test_question_candidates_from_interrogation_photo'`.

Police de test Linux absente sous Windows. Correctif : police Windows ou repli redimensionné Pillow.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
tmp_path = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/pytest-of-cs-ap/pytest-102/popen-gw2/test_question_candidates_from_0')

    def test_question_candidates_from_interrogation_photo(tmp_path: Path) -> None:
        from PIL import Image, ImageDraw, ImageFont
    
        image = Image.new('RGB', (1800, 760), 'white')
        draw = ImageDraw.Draw(image)
>       font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 52)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\document_engine\test_pipeline.py:88: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
.venv\Lib\site-packages\PIL\ImageFont.py:880: in truetype
    return freetype(font)
           ^^^^^^^^^^^^^^
.venv\Lib\site-packages\PIL\ImageFont.py:877: in freetype
    return FreeTypeFont(font, size, index, encoding, layout_engine)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <PIL.ImageFont.FreeTypeFont object at 0x0000021BF436C190>
font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size = 52, index = 0
encoding = '', layout_engine = <Layout.RAQM: 1>

    def __init__(
        self,
        font: StrOrBytesPath | BinaryIO,
        size: float = 10,
        index: int = 0,
        encoding: str = "",
        layout_engine: Layout | None = None,
    ) -> None:
        # FIXME: use service provider instead
    
        if isinstance(core, DeferredError):
            raise core.ex
    
        if size <= 0:
            msg = f"font size must be greater than 0, not {size}"
            raise ValueError(msg)
    
        self.path = font
        self.size = size
        self.index = index
        self.encoding = encoding
    
        try:
            from packaging.version import parse as parse_version
        except ImportError:
            pass
        else:
            if freetype_version := features.version_module("freetype2"):
                if parse_version(freetype_version) < parse_version("2.9.1"):
                    warnings.warn(
                        "Support for FreeType 2.9.0 is deprecated and will be removed "
                        "in Pillow 12 (2025-10-15). Please upgrade to FreeType 2.9.1 "
                        "or newer, preferably FreeType 2.10.4 which fixes "
                        "CVE-2020-15999.",
                        DeprecationWarning,
                    )
    
        if layout_engine not in (Layout.BASIC, Layout.RAQM):
            layout_engine = Layout.BASIC
            if core.HAVE_RAQM:
                layout_engine = Layout.RAQM
        elif layout_engine == Layout.RAQM and not core.HAVE_RAQM:
            warnings.warn(
                "Raqm layout was requested, but Raqm is not available. "
                "Falling back to basic layout."
            )
            layout_engine = Layout.BASIC
    
        self.layout_engine = layout_engine
    
        def load_from_bytes(f: IO[bytes]) -> None:
            self.font_bytes = f.read()
            self.font = core.getfont(
                "", size, index, encoding, self.font_bytes, layout_engine
            )
    
        if is_path(font):
            font = os.fspath(font)
            if sys.platform == "win32":
                font_bytes_path = font if isinstance(font, bytes) else font.encode()
                try:
                    font_bytes_path.decode("ascii")
```

## backend-final-previous-1793433709429319500 — test_cash_payment_allocates_oldest_charge_and_receipt_is_idempotent

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/test_student_finance_phase6.py::test_cash_payment_allocates_oldest_charge_and_receipt_is_idempotent'`.

Allocation atomique par identifiant plutôt que par échéance. Correctif : ordre des verrous conservé, allocation triée par échéance.

Trace complète : [backend-final-previous-1793433709429319500.xml](backend-final-previous-1793433709429319500.xml).

```text
def test_cash_payment_allocates_oldest_charge_and_receipt_is_idempotent():
     a,i,app,s,r,sch,c=finance_student('pay');runtime.student_finance.open_cash(a,i.id,'CDF',0);receipt=runtime.student_finance.payment(a,i.id,s.id,150000,'CDF','cash','CASH-001','Guichet central')
     same=runtime.student_finance.payment(a,i.id,s.id,150000,'CDF','cash','CASH-001','retry');assert same.id==receipt.id
     st=runtime.student_finance.statement(a,i.id,s.id);assert st['balance_minor']==150000
>    cc=runtime.student_finance_repo.charges(s.id);assert cc[0].state.value=='paid' and cc[1].paid_minor==50000
                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E    AssertionError: assert ('open' == 'paid'
E      
E      - paid
E      + open)

services\api\tests\test_student_finance_phase6.py:23: AssertionError
```

## backend — test_factory_end_to_end_ready_for_review_with_evidence

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_end_to_end_ready_for_review_with_evidence'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_factory_end_to_end_ready_for_review_with_evidence():
>    _,h=account(); did=processed(h); cr=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did}); assert cr.status_code==200,cr.text; rid=cr.json()['id']; pr=client.post(f'/v1/content-factory/runs/{rid}/process',headers=h); assert pr.status_code==200,pr.text; assert pr.json()['state']=='ready_for_review'; detail=client.get(f'/v1/content-factory/runs/{rid}',headers=h).json(); assert detail['assets']; assert len(detail['assets'])==len(detail['evidence']); assert all(e['page_start']>=1 for e in detail['evidence']); assert any(g['code']=='provenance_complete' and g['passed'] for g in detail['quality_gates'])
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:16: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F34B2900>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_factory_create_is_idempotent_for_same_source_and_asset_contract

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_create_is_idempotent_for_same_source_and_asset_contract'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_factory_create_is_idempotent_for_same_source_and_asset_contract():
>    _,h=account(); did=processed(h); body={'document_id':did,'requested_assets':['summary_express','rag_chunk']}; a=client.post('/v1/content-factory/runs',headers=h,json=body).json(); b=client.post('/v1/content-factory/runs',headers=h,json=body).json(); assert a['id']==b['id']
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:18: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F38C42D0>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_factory_rejects_unknown_asset_family

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_rejects_unknown_asset_family'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_factory_rejects_unknown_asset_family():
>    _,h=account(); did=processed(h); r=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['telepathy']}); assert r.status_code==422
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:20: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F38C4F50>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_factory_never_publishes_and_exposes_quality_score

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_never_publishes_and_exposes_quality_score'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_factory_never_publishes_and_exposes_quality_score():
>    _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['summary_express','quiz']}).json(); out=client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h).json(); assert out['state']=='ready_for_review'; assert 0<=out['quality_score']<=100; assert 'published' not in out['state']
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:22: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F2F608A0>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_factory_final_quality_gates_include_grounding_integrity

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_final_quality_gates_include_grounding_integrity'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_factory_final_quality_gates_include_grounding_integrity():
>    _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['summary_express','quiz']}).json(); client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h); detail=client.get(f"/v1/content-factory/runs/{run['id']}",headers=h).json(); gates={g['code']:g for g in detail['quality_gates']}; assert gates['evidence_quote_grounded']['passed']; assert gates['evidence_hash_integrity']['passed']; assert gates['numeric_claim_grounding']['passed']
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:24: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F36A8770>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_factory_queued_run_can_be_cancelled_and_not_processed

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_queued_run_can_be_cancelled_and_not_processed'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_factory_queued_run_can_be_cancelled_and_not_processed():
>    _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['rag_chunk']}).json(); out=client.post(f"/v1/content-factory/runs/{run['id']}/cancel",headers=h); assert out.status_code==200; assert out.json()['state']=='cancelled'; pr=client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h); assert pr.status_code==422
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:26: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F36A6450>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_factory_review_package_pairs_every_asset_with_source_evidence_and_blocks_publication

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/content_factory/test_content_factory.py::test_factory_review_package_pairs_every_asset_with_source_evidence_and_blocks_publication'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_factory_review_package_pairs_every_asset_with_source_evidence_and_blocks_publication():
>    _,h=account(); did=processed(h); run=client.post('/v1/content-factory/runs',headers=h,json={'document_id':did,'requested_assets':['summary_express','quiz']}).json(); client.post(f"/v1/content-factory/runs/{run['id']}/process",headers=h); r=client.get(f"/v1/content-factory/runs/{run['id']}/review-package",headers=h); assert r.status_code==200; body=r.json(); assert body['publication_allowed'] is False; assert body['required_next_state']=='human_review'; assert body['items'] and all(x['evidence'] for x in body['items'])
                        ^^^^^^^^^^^^

services\api\tests\content_factory\test_content_factory.py:28: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\tests\content_factory\test_content_factory.py:14: in processed
    b=client.post('/v1/ingestion/batches',headers=h,json={'name':'Factory source','defaults':{'content_kind':'course','faculty_domain':'Medecine','program':'Medecine humaine','level':'BAC1','semester':'S1','risk':'medical','rights_status':'authorized','rights_note':'test'}}).json(); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'factory-source'},files={'file':('cours.pdf',pdf_bytes('Introduction a la cellule et physiologie.'),'application/pdf')}).json(); client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='factory-ingestion'); runtime.ingestion.process_job(worker_id='factory-ingestion',job_id=j.id); return d['id']
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F35086B0>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_ocr_photo_pipeline

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/document_engine/test_pipeline.py::test_ocr_photo_pipeline'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
tmp_path = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/pytest-of-cs-ap/pytest-101/test_ocr_photo_pipeline0')

    def test_ocr_photo_pipeline(tmp_path: Path) -> None:
        from PIL import Image, ImageDraw, ImageFont
    
        image = Image.new('RGB', (1800, 700), 'white')
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 58)
        except OSError:
            font = ImageFont.load_default()
        draw.text((80, 120), 'INTERROGATION DE CHIMIE', fill='black', font=font)
        draw.text((80, 250), '1. Calculer la quantite de matiere.', fill='black', font=font)
        draw.text((80, 360), '2. Donner la formule de concentration molaire.', fill='black', font=font)
        path = tmp_path / 'interro.jpg'
        image.save(path, quality=95)
    
>       document = PremiumDocumentPipeline(enable_ocr=True, ocr_languages='fra+eng').process(path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\document_engine\test_pipeline.py:77: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F350B460>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_question_candidates_from_interrogation_photo

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/document_engine/test_pipeline.py::test_question_candidates_from_interrogation_photo'`.

Police de test Linux absente sous Windows. Correctif : police Windows ou repli redimensionné Pillow.

Trace complète : [backend.xml](backend.xml).

```text
tmp_path = WindowsPath('C:/Users/cs-ap/AppData/Local/Temp/pytest-of-cs-ap/pytest-101/test_question_candidates_from_0')

    def test_question_candidates_from_interrogation_photo(tmp_path: Path) -> None:
        from PIL import Image, ImageDraw, ImageFont
    
        image = Image.new('RGB', (1800, 760), 'white')
        draw = ImageDraw.Draw(image)
>       font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 52)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\document_engine\test_pipeline.py:88: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
.venv\Lib\site-packages\PIL\ImageFont.py:880: in truetype
    return freetype(font)
           ^^^^^^^^^^^^^^
.venv\Lib\site-packages\PIL\ImageFont.py:877: in freetype
    return FreeTypeFont(font, size, index, encoding, layout_engine)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <PIL.ImageFont.FreeTypeFont object at 0x00000157F38C6990>
font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size = 52, index = 0
encoding = '', layout_engine = <Layout.BASIC: 0>

    def __init__(
        self,
        font: StrOrBytesPath | BinaryIO,
        size: float = 10,
        index: int = 0,
        encoding: str = "",
        layout_engine: Layout | None = None,
    ) -> None:
        # FIXME: use service provider instead
    
        if isinstance(core, DeferredError):
            raise core.ex
    
        if size <= 0:
            msg = f"font size must be greater than 0, not {size}"
            raise ValueError(msg)
    
        self.path = font
        self.size = size
        self.index = index
        self.encoding = encoding
    
        try:
            from packaging.version import parse as parse_version
        except ImportError:
            pass
        else:
            if freetype_version := features.version_module("freetype2"):
                if parse_version(freetype_version) < parse_version("2.9.1"):
                    warnings.warn(
                        "Support for FreeType 2.9.0 is deprecated and will be removed "
                        "in Pillow 12 (2025-10-15). Please upgrade to FreeType 2.9.1 "
                        "or newer, preferably FreeType 2.10.4 which fixes "
                        "CVE-2020-15999.",
                        DeprecationWarning,
                    )
    
        if layout_engine not in (Layout.BASIC, Layout.RAQM):
            layout_engine = Layout.BASIC
            if core.HAVE_RAQM:
                layout_engine = Layout.RAQM
        elif layout_engine == Layout.RAQM and not core.HAVE_RAQM:
            warnings.warn(
                "Raqm layout was requested, but Raqm is not available. "
                "Falling back to basic layout."
            )
            layout_engine = Layout.BASIC
    
        self.layout_engine = layout_engine
    
        def load_from_bytes(f: IO[bytes]) -> None:
            self.font_bytes = f.read()
            self.font = core.getfont(
                "", size, index, encoding, self.font_bytes, layout_engine
            )
    
        if is_path(font):
            font = os.fspath(font)
            if sys.platform == "win32":
                font_bytes_path = font if isinstance(font, bytes) else font.encode()
                try:
                    font_bytes_path.decode("ascii")
        
```

## backend — test_batch_upload_idempotency_freeze_worker_and_editorial_projection

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_batch_upload_idempotency_freeze_worker_and_editorial_projection'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
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
>       result=runtime.ingestion.process_job(worker_id='pytest-worker',job_id=job.id)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\ingestion\test_ingestion_api.py:43: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F3AE8850>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_global_dedup_reuses_already_processed_document_without_second_ocr

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_global_dedup_reuses_already_processed_document_without_second_ocr'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_global_dedup_reuses_already_processed_document_without_second_ocr():
        _,h=account(); payload=pdf_bytes('Document global unique ' + uuid4().hex)
        b1=create_batch(h,'Premier lot'); d1=client.post(f"/v1/ingestion/batches/{b1['id']}/files",headers={**h,'Idempotency-Key':'g1'},files={'file':('g.pdf',payload,'application/pdf')}).json()
        client.post(f"/v1/ingestion/batches/{b1['id']}/start",headers=h,json={})
>       j=runtime.ingestion.claim_job(worker_id='dedup-worker'); r1=runtime.ingestion.process_job(worker_id='dedup-worker',job_id=j.id)
                                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\ingestion\test_ingestion_api.py:80: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F3B2C650>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_preview_and_global_dashboard_after_processing

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_preview_and_global_dashboard_after_processing'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_preview_and_global_dashboard_after_processing():
        _,h=account(); payload=pdf_bytes('Question 1. Définir la membrane cellulaire. ' + uuid4().hex)
        b=create_batch(h,'Preview lot'); d=client.post(f"/v1/ingestion/batches/{b['id']}/files",headers={**h,'Idempotency-Key':'p1'},files={'file':('preview.pdf',payload,'application/pdf')}).json()
>       client.post(f"/v1/ingestion/batches/{b['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='preview-worker'); runtime.ingestion.process_job(worker_id='preview-worker',job_id=j.id)
                                                                                                                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\ingestion\test_ingestion_api.py:91: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F3A65310>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_global_dedup_never_reuses_rights_or_academic_context_silently

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_global_dedup_never_reuses_rights_or_academic_context_silently'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
def test_global_dedup_never_reuses_rights_or_academic_context_silently():
        _,h=account(); payload=pdf_bytes('Same bytes different rights ' + uuid4().hex)
>       b1=create_batch(h,'Contexte A'); client.post(f"/v1/ingestion/batches/{b1['id']}/files",headers={**h,'Idempotency-Key':'cx1'},files={'file':('same.pdf',payload,'application/pdf')}); client.post(f"/v1/ingestion/batches/{b1['id']}/start",headers=h,json={}); j=runtime.ingestion.claim_job(worker_id='ctx-worker'); runtime.ingestion.process_job(worker_id='ctx-worker',job_id=j.id)
                                                                                                                                                                                                                                                                                                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

services\api\tests\ingestion\test_ingestion_api.py:115: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F3ACAD50>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_frozen_manifest_snapshot_is_persisted_and_verifiable

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_ingestion_api.py::test_frozen_manifest_snapshot_is_persisted_and_verifiable'`.

Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.

Trace complète : [backend.xml](backend.xml).

```text
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
>       runtime.ingestion.process_job(worker_id='manifest-worker',job_id=job.id)

services\api\tests\ingestion\test_ingestion_api.py:133: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
services\api\app\modules\ingestion\application\service.py:251: in process_job
    processed=(pipeline or PremiumDocumentPipeline()).process(Path(tmp.name),title=Path(doc.filename).stem)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^
services\api\app\modules\document_engine\application\pipeline.py:29: in __init__
    self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <app.modules.document_engine.infrastructure.ocr.TesseractOcr object at 0x00000157F3BA49F0>
languages = 'fra+eng'

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
>           raise RuntimeError("tesseract binary not found")
E           RuntimeError: tesseract binary not found

services\api\app\modules\document_engine\infrastructure\ocr.py:26: RuntimeError
```

## backend — test_repository_lease_heartbeat_and_recovery

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/ingestion/test_jobs.py::test_repository_lease_heartbeat_and_recovery'`.

Voir trace. Reproduire le cas isolément et réconcilier le contrat avant de modifier les assertions.

Trace complète : [backend.xml](backend.xml).

```text
def test_repository_lease_heartbeat_and_recovery():
        now=datetime.now(UTC); bid=f'b-{uuid4()}'; did=f'd-{uuid4()}'; jid=f'j-{uuid4()}'
        # Repository-level contract does not need the parent rows for SQLite because there are no FKs.
        runtime.ingestion_repository.save_job(IngestionJob(jid,bid,did,JobState.PENDING,50,0,3,now,None,None,None,None,None,None,now,now))
        claimed=runtime.ingestion_repository.claim_next_job(worker_id='w1',now=now,lease_seconds=10)
>       assert claimed and claimed.id==jid and claimed.state==JobState.LEASED and claimed.attempt==1
E       AssertionError: assert (IngestionJob(id='c5db5c74-2ba2-4872-8959-c8fd17739b97', batch_id='05f16024-9b65-4bd6-9028-9b0af85a5f06', document_id='...o=datetime.timezone.utc), updated_at=datetime.datetime(2026, 10, 30, 20, 25, 44, 715735, tzinfo=datetime.timezone.utc)) and 'c5db5c74-2ba...-c8fd17739b97' == 'j-1e42aa6e-4...-fb3f29630351'
E         
E         - j-1e42aa6e-4da2-4cf2-9122-fb3f29630351
E         + c5db5c74-2ba2-4872-8959-c8fd17739b97)

services\api\tests\ingestion\test_jobs.py:15: AssertionError
```

## backend — test_cash_payment_allocates_oldest_charge_and_receipt_is_idempotent

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/test_student_finance_phase6.py::test_cash_payment_allocates_oldest_charge_and_receipt_is_idempotent'`.

Allocation atomique par identifiant plutôt que par échéance. Correctif : ordre des verrous conservé, allocation triée par échéance.

Trace complète : [backend.xml](backend.xml).

```text
def test_cash_payment_allocates_oldest_charge_and_receipt_is_idempotent():
     a,i,app,s,r,sch,c=finance_student('pay');runtime.student_finance.open_cash(a,i.id,'CDF',0);receipt=runtime.student_finance.payment(a,i.id,s.id,150000,'CDF','cash','CASH-001','Guichet central')
     same=runtime.student_finance.payment(a,i.id,s.id,150000,'CDF','cash','CASH-001','retry');assert same.id==receipt.id
     st=runtime.student_finance.statement(a,i.id,s.id);assert st['balance_minor']==150000
>    cc=runtime.student_finance_repo.charges(s.id);assert cc[0].state.value=='paid' and cc[1].paid_minor==50000
                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E    AssertionError: assert ('open' == 'paid'
E      
E      - paid
E      + open)

services\api\tests\test_student_finance_phase6.py:23: AssertionError
```

## backend — test_compaction_waits_for_all_active_devices_before_advancing_floor

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/test_sync_lot7.py::test_compaction_waits_for_all_active_devices_before_advancing_floor'`.

Cause probable : pollution de contexte/limitation dans la suite séquentielle. Reproduire isolément ; la régression finale complète doit être consultée séparément.

Trace complète : [backend.xml](backend.xml).

```text
def test_compaction_waits_for_all_active_devices_before_advancing_floor():
        _, headers = _account("sync-compaction-two-devices")
        a = _device(headers, f"dev-a-{uuid4().hex}")
        b = _device(headers, f"dev-b-{uuid4().hex}")
        base = None
        latest = 0
        for i in range(65):
>           out = client.post(
                "/v1/sync/push",
                headers=headers,
                json={"device_id": a, "mutations": [_mutation("planning_preferences", "default", base_version=base, payload=_prefs(30 + (i % 30)))]},
            ).json()["outcomes"][0]
E           KeyError: 'outcomes'

services\api\tests\test_sync_lot7.py:273: KeyError
```

## postgres-before-fix — test_callback_racing_stale_terminal_save_cannot_erase_settlement[expired]

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/test_phase19_postgres_concurrency.py::test_callback_racing_stale_terminal_save_cannot_erase_settlement[expired]'`.

Écriture terminale obsolète après callback. Correctif : revérification sous verrou avant sauvegarde.

Trace complète : [postgres-before-fix.xml](postgres-before-fix.xml).

```text
repositories = (sessionmaker(class_='Session', bind=Engine(postgresql+psycopg://edunova_cert@127.0.0.1:55439/edunova_phase19_test), a...ntFinanceRepository object at 0x000002B316669BD0>, datetime.datetime(2026, 10, 30, 0, 0, tzinfo=datetime.timezone.utc))
terminal = 'expired'

    @pytest.mark.parametrize('terminal', ['expired', 'cancelled'])
    def test_callback_racing_stale_terminal_save_cannot_erase_settlement(repositories, terminal):
        sf, gateway, finance, now = repositories
        from app.modules.payment_gateway.application.service import PaymentGatewayService
        read, committed = Event(), Event()
        original_get = gateway.get
        def delayed_get(intent_id):
            stale = original_get(intent_id)
            read.set()
            assert committed.wait(timeout=15)
            return stale
        gateway.get = delayed_get
        service = PaymentGatewayService(gateway, Mock(), Mock(), Mock(), lambda: now)
        def callback():
            assert read.wait(timeout=15)
            try:
                return settle(gateway, finance, now)
            finally:
                committed.set()
        operation = (lambda: service.expire('intent-1')) if terminal == 'expired' else (lambda: service.cancel('student-a', 'institution-a', 'intent-1', 'test cancellation'))
        results = simultaneous(callback, operation)
        with sf() as s:
            intent = s.get(PaymentIntentRow, 'intent-1')
            receipts, ledger = counts(sf)
            if receipts:
>               assert intent.status == 'succeeded' and intent.receipt_id is not None, (terminal, intent.status, results)
E               AssertionError: ('expired', 'expired', [PaymentIntent(id='intent-1', institution_id='institution-a', student_id='student-a', amount_mi...me(2026, 10, 30, 2, 0, tzinfo=zoneinfo.ZoneInfo(key='Africa/Johannesburg')), failure_code='expired', receipt_id=None)])
E               assert ('expired' == 'succeeded'
E                 
E                 - succeeded
E                 + expired)

services\api\tests\test_phase19_postgres_concurrency.py:101: AssertionError
```

## postgres-before-fix — test_callback_racing_stale_terminal_save_cannot_erase_settlement[cancelled]

Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q 'services/api/tests/test_phase19_postgres_concurrency.py::test_callback_racing_stale_terminal_save_cannot_erase_settlement[cancelled]'`.

Écriture terminale obsolète après callback. Correctif : revérification sous verrou avant sauvegarde.

Trace complète : [postgres-before-fix.xml](postgres-before-fix.xml).

```text
repositories = (sessionmaker(class_='Session', bind=Engine(postgresql+psycopg://edunova_cert@127.0.0.1:55439/edunova_phase19_test), a...ntFinanceRepository object at 0x000002B3168CBF50>, datetime.datetime(2026, 10, 30, 0, 0, tzinfo=datetime.timezone.utc))
terminal = 'cancelled'

    @pytest.mark.parametrize('terminal', ['expired', 'cancelled'])
    def test_callback_racing_stale_terminal_save_cannot_erase_settlement(repositories, terminal):
        sf, gateway, finance, now = repositories
        from app.modules.payment_gateway.application.service import PaymentGatewayService
        read, committed = Event(), Event()
        original_get = gateway.get
        def delayed_get(intent_id):
            stale = original_get(intent_id)
            read.set()
            assert committed.wait(timeout=15)
            return stale
        gateway.get = delayed_get
        service = PaymentGatewayService(gateway, Mock(), Mock(), Mock(), lambda: now)
        def callback():
            assert read.wait(timeout=15)
            try:
                return settle(gateway, finance, now)
            finally:
                committed.set()
        operation = (lambda: service.expire('intent-1')) if terminal == 'expired' else (lambda: service.cancel('student-a', 'institution-a', 'intent-1', 'test cancellation'))
        results = simultaneous(callback, operation)
        with sf() as s:
            intent = s.get(PaymentIntentRow, 'intent-1')
            receipts, ledger = counts(sf)
            if receipts:
>               assert intent.status == 'succeeded' and intent.receipt_id is not None, (terminal, intent.status, results)
E               AssertionError: ('cancelled', 'cancelled', [PaymentIntent(id='intent-1', institution_id='institution-a', student_id='student-a', amoun...0, tzinfo=zoneinfo.ZoneInfo(key='Africa/Johannesburg')), failure_code='cancelled:test cancellation', receipt_id=None)])
E               assert ('cancelled' == 'succeeded'
E                 
E                 - succeeded
E                 + cancelled)

services\api\tests\test_phase19_postgres_concurrency.py:101: AssertionError
```

## Flutter — 00:00 +0 -1: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/admin` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Revoir les imports, contrats d’interface et fixtures indiqués dans la trace ; réexécuter les mêmes assertions après correction. Les résultats des reprises sont séparés.

Trace complète : [admin-test-previous-1793436624137805600.log](admin-test-previous-1793436624137805600.log). Extrait du flux de test :

```text
children:[for(final r in rows.reversed)ListTile(contentPadding:EdgeInsets.zero,leading:Icon(r['decision']=='approved'?Icons.check_circle:Icons.change_circle,color:r['decision']=='approved'?Colors.green:Colors.orange),title:Text('${r['decision']=='approved'?'Approuvé':'Corrections demandées'} • ${r['reviewer_id']}'),subtitle:Text('${r['comment']?.toString().isEmpty==false?r['comment']:'Sans commentaire'}\n${formatDate(r['created_at'])}${r['quality_score']!=null?' • qualité ${r['quality_score']} %':''}'),isThreeLine:true)]))]);}}
                                                                                          ^
lib/src/features/editorial/content_detail_page.dart:34:1393: Error: Unexpected token ';'.
class _ReviewTab extends StatelessWidget{final Map<String,dynamic> data;const _ReviewTab({required this.data});@override Widget build(BuildContext c){final rows=data['reviews'] as List<dynamic>;final assignments=data['assignments'] as List<dynamic>;return ListView(padding:const EdgeInsets.all(24),children:[StudioSection(title:'Affectations',child:assignments.isEmpty?const Text('Aucune affectation explicite.'):Column(children:[for(final a in assignments.where((x)=>(x as Map)['active']==true))ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.assignment_ind_outlined),title:Text('${a['stage']} • ${a['assignee_id']}'),subtitle:Text(a['due_at']==null?'Sans échéance':'Échéance ${formatDate(a['due_at'])}')]))),const SizedBox(height:14),StudioSection(title:'Décisions de revue',child:rows.isEmpty?const Text('Aucune décision enregistrée.'):Column(children:[for(final r in rows.reversed)ListTile(contentPadding:EdgeInsets.zero,leading:Icon(r['decision']=='approved'?Icons.check_circle:Icons.change_circle,color:r['decision']=='approved'?Colors.green:Colors.orange),title:Text('${r['decision']=='approved'?'Approuvé':'Corrections demandées'} • ${r['reviewer_id']}'),subtitle:Text('${r['comment']?.toString().isEmpty==false?r['comment']:'Sans commentaire'}\n${formatDate(r['created_at'])}${r['quality_score']!=null?' • qualité ${r['quality_score']} %':''}'),isThreeLine:true)]))]);}}
                                                                                          ^
00:00 +0 -1: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart: lib/src/features/editorial/content_detail_page.dart:34:505: Error: Can't find ')' to match '('.
  class _ReviewTab extends StatelessWidget{final Map<String,dynamic> data;const _ReviewTab({required this.data});@override Widget build(BuildContext c){final rows=data['reviews'] as List<dynamic>;final assignments=data['assignments'] as List<dynamic>;return ListView(padding:const EdgeInsets.all(24),children:[StudioSection(title:'Affectations',child:assignments.isEmpty?const Text('Aucune affectation explicite.'):Column(children:[for(final a in assignments.where((x)=>(x as Map)['active']==true))ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.assignment_ind_outlined),title:Text('${a['stage']} • ${a['assignee_id']}'),subtitle:Text(a['due_at']==null?'Sans échéance':'Échéance ${formatDate(a['due_at'])}')]))),const SizedBox(height:14),StudioSection(title:'Décisions de revue',child:rows.isEmpty?const Text('Aucune décision enregistrée.'):Column(children:[for(final r in rows.reversed)ListTile(contentPadding:EdgeInsets.zero,leading:Icon(r['decision']=='approved'?Icons.check_circle:Icons.change_circle,color:r['decision']=='approved'?Colors.green:Colors.orange),title:Text('${r['decision']=='approved'?'Approuvé':'Corrections demandées'} • ${r['reviewer_id']}'),subtitle:Text('${r['comment']?.toString().isEmpty==false?r['comment']:'Sans commentaire'}\n${formatDate(r['created_at'])}${r['quality_score']!=null?' • qualité ${r['quality_score']} %':''}'),isThreeLine:true)]))]);}}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ^
```

## Flutter — 00:02 +0 -1: EduNova Studio affiche la connexion [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/admin` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Ancien libellé et restauration de session asynchrone non attendue. Simuler un stockage sécurisé vide, attendre le démarrage et vérifier les libellés Administration actuels.

Trace complète : [admin-test-previous-1793439552265020100.log](admin-test-previous-1793439552265020100.log). Extrait du flux de test :

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart
00:00 +0: EduNova Studio affiche la connexion
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "EduNova Studio": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart:3:126)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart line 3
The test description was:
  EduNova Studio affiche la connexion
════════════════════════════════════════════════════════════════════════════════════════════════════
00:02 +0 -1: EduNova Studio affiche la connexion [E]
  Test failed. See exception logs above.
  The test description was: EduNova Studio affiche la connexion
  
00:02 +0 -1: Some tests failed.
```

## Flutter — 00:41 +17 -1: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Revoir les imports, contrats d’interface et fixtures indiqués dans la trace ; réexécuter les mêmes assertions après correction. Les résultats des reprises sont séparés.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
Error: Expected ')' before this.
    ]));
    ^
lib/src/features/campus/presentation/campus_page.dart:26:20: Error: Too many positional arguments: 0 allowed, but 8 found.
Try removing the extra positional arguments.
    return Scaffold(appBar: AppBar(title: const Text('Mon université'), actions: [
                   ^
../../../../flutter/packages/flutter/lib/src/material/scaffold.dart:1696:9: Context: Found this candidate, but the arguments don't match.
  const Scaffold({
        ^^^^^^^^
lib/src/features/campus/presentation/campus_page.dart:154:6: Error: Expected ';' after this.
    ]));
     ^
lib/src/features/campus/presentation/campus_page.dart:154:7: Error: Expected an identifier, but got ')'.
Try inserting an identifier before ')'.
    ]));
      ^
lib/src/features/campus/presentation/campus_page.dart:154:7: Error: Unexpected token ';'.
    ]));
      ^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
lib/src/features/campus_intelligence/presentation/institution_intelligence_page.dart:41:51: Error: A value of type 'Map<String, dynamic>?' can't be assigned to a variable of type 'bool'.
 - 'Map' is from 'dart:core'.
  String? get _unit => _role == 'faculty_admin' ? _membership?['unit_id']?.toString() : null;
                                                  ^
lib/src/features/delivery/application/delivery_repository.dart:56:90: Error: 'DownloadResource' isn't a type.
  final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
                                                                                         ^^^^^^^^^^^^^^^^
lib/src/features/delivery/application/download_resource.dart:30:25: Error: Not a constant expression.
        final ids=const CacheEvictionPlanner().plan(candidates:await local.cacheCandidates(),currentBytes:currentCache,targetBytes:(policy.maxCacheBytes-grant.sizeBytes).clamp(0,policy.maxCacheBytes).toInt(),keepFollowed:policy.keepFollowedCourses);
                        ^^^^^^^^^^^^^^^^^^^^
lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:45:29: Error: Too many positional arguments: 0 allowed, but 1 found.
Try removing the extra positional arguments.
    await _plugin.initialize(
                            ^
lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:78:32: Error: Too many positional arguments: 0 allowed, but 5 found.
Try removing the extra positional arguments.
    await _plugin.zonedSchedule(_id(n.id),n.title,n.body,tz.TZDateTime.from(n.fireAt.toUtc(),tz.UTC),details,androidScheduleMode:AndroidScheduleMode.inexactAllowWhileIdle,payload:payload);
                               ^
lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:81:91: Error: Too many positional arguments: 0 allowed, but 1 found.
Try removing the extra positional arguments.
  @override Future<void> cancel(String id) async {await initialize(); await _plugin.cancel(_id(id));}
                                                                                          ^
lib/src/features/identity/infrastructure/legacy_offline_files_native.dart:11:45: Error: The getter 'isNotEmpty' isn't defined for the type 'Stream<FileSystemEntity>'.
 - 'Stream' is from 'dart:async'.
 - 'FileSystemEntity' is from 'dart:io'.
Try correcting the name to the name of an existing getter, or defining a getter or field named 'isNotEmpty'.
  return directory.list(followLinks: false).isNotEmpty;
                                            ^^^^^^^^^^
00:41 +17 -1: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: lib/src/features/campus/presentation/campus_page.dart:30:69: Error: Can't find ']' to match '['.
      ]), body: ListView(padding: const EdgeInsets.all(18), children: [
                                                                      ^
```

## Flutter — 00:57 +17 -2: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Revoir les imports, contrats d’interface et fixtures indiqués dans la trace ; réexécuter les mêmes assertions après correction. Les résultats des reprises sont séparés.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
  lib/src/features/campus/presentation/campus_page.dart:154:7: Error: Unexpected token ';'.
      ]));
        ^
  lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
   - 'Map' is from 'dart:core'.
   - 'Future' is from 'dart:async'.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
      ^
  lib/src/features/campus_intelligence/presentation/institution_intelligence_page.dart:41:51: Error: A value of type 'Map<String, dynamic>?' can't be assigned to a variable of type 'bool'.
   - 'Map' is from 'dart:core'.
    String? get _unit => _role == 'faculty_admin' ? _membership?['unit_id']?.toString() : null;
                                                    ^
  lib/src/features/delivery/application/delivery_repository.dart:56:90: Error: 'DownloadResource' isn't a type.
    final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
                                                                                           ^^^^^^^^^^^^^^^^
  lib/src/features/delivery/application/download_resource.dart:30:25: Error: Not a constant expression.
          final ids=const CacheEvictionPlanner().plan(candidates:await local.cacheCandidates(),currentBytes:currentCache,targetBytes:(policy.maxCacheBytes-grant.sizeBytes).clamp(0,policy.maxCacheBytes).toInt(),keepFollowed:policy.keepFollowedCourses);
                          ^^^^^^^^^^^^^^^^^^^^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:45:29: Error: Too many positional arguments: 0 allowed, but 1 found.
  Try removing the extra positional arguments.
      await _plugin.initialize(
                              ^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:78:32: Error: Too many positional arguments: 0 allowed, but 5 found.
  Try removing the extra positional arguments.
      await _plugin.zonedSchedule(_id(n.id),n.title,n.body,tz.TZDateTime.from(n.fireAt.toUtc(),tz.UTC),details,androidScheduleMode:AndroidScheduleMode.inexactAllowWhileIdle,payload:payload);
                                 ^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:81:91: Error: Too many positional arguments: 0 allowed, but 1 found.
  Try removing the extra positional arguments.
    @override Future<void> cancel(String id) async {await initialize(); await _plugin.cancel(_id(id));}
                                                                                            ^
  lib/src/features/identity/infrastructure/legacy_offline_files_native.dart:11:45: Error: The getter 'isNotEmpty' isn't defined for the type 'Stream<FileSystemEntity>'.
   - 'Stream' is from 'dart:async'.
   - 'FileSystemEntity' is from 'dart:io'.
  Try correcting the name to the name of an existing getter, or defining a getter or field named 'isNotEmpty'.
    return directory.list(followLinks: false).isNotEmpty;
                                              ^^^^^^^^^^
  .
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
00:57 +17 -2: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
```

## Flutter — 01:12 +17 -3: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Revoir les imports, contrats d’interface et fixtures indiqués dans la trace ; réexécuter les mêmes assertions après correction. Les résultats des reprises sont séparés.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
e.dart:45:29: Error: Too many positional arguments: 0 allowed, but 1 found.
  Try removing the extra positional arguments.
      await _plugin.initialize(
                              ^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:78:32: Error: Too many positional arguments: 0 allowed, but 5 found.
  Try removing the extra positional arguments.
      await _plugin.zonedSchedule(_id(n.id),n.title,n.body,tz.TZDateTime.from(n.fireAt.toUtc(),tz.UTC),details,androidScheduleMode:AndroidScheduleMode.inexactAllowWhileIdle,payload:payload);
                                 ^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:81:91: Error: Too many positional arguments: 0 allowed, but 1 found.
  Try removing the extra positional arguments.
    @override Future<void> cancel(String id) async {await initialize(); await _plugin.cancel(_id(id));}
                                                                                            ^
  lib/src/features/identity/infrastructure/legacy_offline_files_native.dart:11:45: Error: The getter 'isNotEmpty' isn't defined for the type 'Stream<FileSystemEntity>'.
   - 'Stream' is from 'dart:async'.
   - 'FileSystemEntity' is from 'dart:io'.
  Try correcting the name to the name of an existing getter, or defining a getter or field named 'isNotEmpty'.
    return directory.list(followLinks: false).isNotEmpty;
                                              ^^^^^^^^^^
  .
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
00:57 +17 -2: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
  lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
   - 'Map' is from 'dart:core'.
   - 'Future' is from 'dart:async'.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
      ^
  .
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
01:12 +17 -3: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
```

## Flutter — 01:22 +17 -4: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Les paramètres encodés dans une URI n’étaient pas exposés dans queryParameters. Utiliser les paramètres GET/POST explicites de Dio en conservant auth, scope et no-store.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
et('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
00:57 +17 -2: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
  lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
   - 'Map' is from 'dart:core'.
   - 'Future' is from 'dart:async'.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
      ^
  .
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
01:12 +17 -3: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
  lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
   - 'Map' is from 'dart:core'.
   - 'Future' is from 'dart:async'.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
      ^
  .
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
01:22 +17 -4: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
```

## Flutter — 01:31 +17 -5: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_governance_gateway_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Les paramètres encodés dans une URI n’étaient pas exposés dans queryParameters. Utiliser les paramètres GET/POST explicites de Dio en conservant auth, scope et no-store.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
ait _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
01:12 +17 -3: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
  lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
   - 'Map' is from 'dart:core'.
   - 'Future' is from 'dart:async'.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
      ^
  .
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
01:22 +17 -4: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
  lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
   - 'Map' is from 'dart:core'.
   - 'Future' is from 'dart:async'.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
      ^
  .
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
01:31 +17 -5: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_governance_gateway_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_governance_gateway_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_governance_gateway_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
```

## Flutter — 01:59 +17 -6: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_tenant_transition_widget_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Revoir les imports, contrats d’interface et fixtures indiqués dans la trace ; réexécuter les mêmes assertions après correction. Les résultats des reprises sont séparés.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
d']?.toString() : null;
                                                                                          ^
lib/src/features/campus_intelligence/presentation/institution_intelligence_page.dart:41:93: Error: Expected an identifier, but got ';'.
Try inserting an identifier before ';'.
  String? get _unit => _role == 'faculty_admin' ? _membership?['unit_id']?.toString() : null;
                                                                                          ^
lib/src/features/delivery/application/delivery_repository.dart:56:90: Error: Type 'DownloadResource' not found.
  final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
                                                                                         ^^^^^^^^^^^^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
lib/src/features/campus_intelligence/presentation/institution_intelligence_page.dart:41:51: Error: A value of type 'Map<String, dynamic>?' can't be assigned to a variable of type 'bool'.
 - 'Map' is from 'dart:core'.
  String? get _unit => _role == 'faculty_admin' ? _membership?['unit_id']?.toString() : null;
                                                  ^
lib/src/features/delivery/application/delivery_repository.dart:56:90: Error: 'DownloadResource' isn't a type.
  final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
                                                                                         ^^^^^^^^^^^^^^^^
lib/src/features/delivery/application/download_resource.dart:30:25: Error: Not a constant expression.
        final ids=const CacheEvictionPlanner().plan(candidates:await local.cacheCandidates(),currentBytes:currentCache,targetBytes:(policy.maxCacheBytes-grant.sizeBytes).clamp(0,policy.maxCacheBytes).toInt(),keepFollowed:policy.keepFollowedCourses);
                        ^^^^^^^^^^^^^^^^^^^^
lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:45:29: Error: Too many positional arguments: 0 allowed, but 1 found.
Try removing the extra positional arguments.
    await _plugin.initialize(
                            ^
lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:78:32: Error: Too many positional arguments: 0 allowed, but 5 found.
Try removing the extra positional arguments.
    await _plugin.zonedSchedule(_id(n.id),n.title,n.body,tz.TZDateTime.from(n.fireAt.toUtc(),tz.UTC),details,androidScheduleMode:AndroidScheduleMode.inexactAllowWhileIdle,payload:payload);
                               ^
lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:81:91: Error: Too many positional arguments: 0 allowed, but 1 found.
Try removing the extra positional arguments.
  @override Future<void> cancel(String id) async {await initialize(); await _plugin.cancel(_id(id));}
                                                                                          ^
lib/src/features/identity/infrastructure/legacy_offline_files_native.dart:11:45: Error: The getter 'isNotEmpty' isn't defined for the type 'Stream<FileSystemEntity>'.
 - 'Stream' is from 'dart:async'.
 - 'FileSystemEntity' is from 'dart:io'.
Try correcting the name to the name of an existing getter, or defining a getter or field named 'isNotEmpty'.
  return directory.list(followLinks: false).isNotEmpty;
                                            ^^^^^^^^^^
01:59 +17 -6: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_tenant_transition_widget_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_tenant_transition_widget_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_tenant_transition_widget_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
```

## Flutter — 02:18 +17 -7: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/cloud_sync_use_case_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Revoir les imports, contrats d’interface et fixtures indiqués dans la trace ; réexécuter les mêmes assertions après correction. Les résultats des reprises sont séparés.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
t:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
   - 'Map' is from 'dart:core'.
   - 'Future' is from 'dart:async'.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
      ^
  lib/src/features/campus_intelligence/presentation/institution_intelligence_page.dart:41:51: Error: A value of type 'Map<String, dynamic>?' can't be assigned to a variable of type 'bool'.
   - 'Map' is from 'dart:core'.
    String? get _unit => _role == 'faculty_admin' ? _membership?['unit_id']?.toString() : null;
                                                    ^
  lib/src/features/delivery/application/delivery_repository.dart:56:90: Error: 'DownloadResource' isn't a type.
    final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
                                                                                           ^^^^^^^^^^^^^^^^
  lib/src/features/delivery/application/download_resource.dart:30:25: Error: Not a constant expression.
          final ids=const CacheEvictionPlanner().plan(candidates:await local.cacheCandidates(),currentBytes:currentCache,targetBytes:(policy.maxCacheBytes-grant.sizeBytes).clamp(0,policy.maxCacheBytes).toInt(),keepFollowed:policy.keepFollowedCourses);
                          ^^^^^^^^^^^^^^^^^^^^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:45:29: Error: Too many positional arguments: 0 allowed, but 1 found.
  Try removing the extra positional arguments.
      await _plugin.initialize(
                              ^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:78:32: Error: Too many positional arguments: 0 allowed, but 5 found.
  Try removing the extra positional arguments.
      await _plugin.zonedSchedule(_id(n.id),n.title,n.body,tz.TZDateTime.from(n.fireAt.toUtc(),tz.UTC),details,androidScheduleMode:AndroidScheduleMode.inexactAllowWhileIdle,payload:payload);
                                 ^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:81:91: Error: Too many positional arguments: 0 allowed, but 1 found.
  Try removing the extra positional arguments.
    @override Future<void> cancel(String id) async {await initialize(); await _plugin.cancel(_id(id));}
                                                                                            ^
  lib/src/features/identity/infrastructure/legacy_offline_files_native.dart:11:45: Error: The getter 'isNotEmpty' isn't defined for the type 'Stream<FileSystemEntity>'.
   - 'Stream' is from 'dart:async'.
   - 'FileSystemEntity' is from 'dart:io'.
  Try correcting the name to the name of an existing getter, or defining a getter or field named 'isNotEmpty'.
    return directory.list(followLinks: false).isNotEmpty;
                                              ^^^^^^^^^^
  .
test/cloud_sync_use_case_test.dart:6:7: Error: The non-abstract class 'FakeLocal' is missing implementations for these members:
 - CloudSyncLocalRepository.recordSyncError
 - CloudSyncLocalRepository.watchDiagnostics
Try to either
 - provide an implementation,
 - inherit an implementation from a superclass or mixin,
 - mark the class as abstract, or
 - provide a 'noSuchMethod' implementation.

class FakeLocal implements CloudSyncLocalRepository {
      ^^^^^^^^^
lib/src/features/sync/application/cloud_sync_repository.dart:15:16: Context: 'CloudSyncLocalRepository.recordSyncError' is defined here.
  Future<void> recordSyncError(String accountId, String error) async {
               ^^^^^^^^^^^^^^^
lib/src/features/sync/application/cloud_sync_repository.dart:29:27: Context: 'CloudSyncLocalRepository.watchDiagnostics' is defined here.
  Stream<SyncDiagnostics> watchDiagnostics(String accountId);
                          ^^^^^^^^^^^^^^^^
02:18 +17 -7: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/cloud_sync_use_case_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/cloud_sync_use_case_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/cloud_sync_use_case_test.dart: test/cloud_sync_use_case_test.dart:6:7: Error: The non-abstract class 'FakeLocal' is missing implementations for these members:
   - CloudSyncLocalRepository.recordSyncError
   - CloudSyncLocalRepository.watchDiagnostics
```

## Flutter — 02:43 +35 -8: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Revoir les imports, contrats d’interface et fixtures indiqués dans la trace ; réexécuter les mêmes assertions après correction. Les résultats des reprises sont séparés.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
> recordSyncError(String accountId, String error) async {
                 ^^^^^^^^^^^^^^^
  lib/src/features/sync/application/cloud_sync_repository.dart:29:27: Context: 'CloudSyncLocalRepository.watchDiagnostics' is defined here.
    Stream<SyncDiagnostics> watchDiagnostics(String accountId);
                            ^^^^^^^^^^^^^^^^
  .
02:35 +17 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Ressources, réservations et annulation restent liées à une institution
02:35 +18 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Identifiants chemin malformés et absence de session sont refusés
02:35 +19 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Bibliothèque physique : prêts, retours et exemplaires authentifiés
02:35 +20 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Prolongations : identité issue du token et version anti-rejeu
02:35 +21 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Politique de bibliothèque : lecture et sauvegarde avec CAS
02:35 +22 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Politique : interdiction de chemin interuniversitaire invalide
02:35 +23 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Identifiants emprunts malformés et session manquante sont rejetés
02:35 +24 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Incidents : perte et détérioration versionnées, même université
02:35 +25 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Incidents : restauration versionnée et entrée falsifiée refusée
02:35 +26 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Maintenance : signalement et transition avec isolation institutionnelle
02:35 +27 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Maintenance : chemins malformés et action inconnue refusés
02:36 +28 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/combined_access_test.dart: Campus does not grant personal Premium
02:37 +29 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/combined_access_test.dart: Suspended Campus does not remove personal Premium
02:37 +30 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/commerce_domain_test.dart: offline premium requires both lease and subscription to be valid
02:37 +31 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/commerce_domain_test.dart: payment terminal states are explicit
02:39 +32 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/engagement/engagement_domain_test.dart: preferences copyWith preserves untouched values
02:39 +33 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/engagement/engagement_domain_test.dart: notification model keeps priority and expiry
test/library_catalog_refresh_test.dart:18:7: Error: The non-abstract class 'FakeLocalLibrary' is missing implementations for these members:
 - LibraryLocalRepository.setCourseFollowed
Try to either
 - provide an implementation,
 - inherit an implementation from a superclass or mixin,
 - mark the class as abstract, or
 - provide a 'noSuchMethod' implementation.

class FakeLocalLibrary implements LibraryLocalRepository {
      ^^^^^^^^^^^^^^^^
lib/src/features/library/application/library_repository.dart:9:16: Context: 'LibraryLocalRepository.setCourseFollowed' is defined here.
  Future<void> setCourseFollowed(String courseId, bool followed);
               ^^^^^^^^^^^^^^^^^
02:41 +34 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/import_personal_document_test.dart: personal import persists metadata and queues outbox event
02:43 +35 -8: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart: test/library_catalog_refresh_test.dart:18:7: Error: The non-abstract class 'FakeLocalLibrary' is missing implementations for these members:
   - LibraryLocalRepository.setCourseFollowed
  Try to either
```

## Flutter — 02:58 +39 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Attente arithmétique incorrecte du test : 32,5 est arrondi à 33 par Dart. Corriger la valeur attendue sans changer le planificateur.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
us_services_gateway_test.dart: Identifiants emprunts malformés et session manquante sont rejetés
02:35 +24 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Incidents : perte et détérioration versionnées, même université
02:35 +25 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Incidents : restauration versionnée et entrée falsifiée refusée
02:35 +26 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Maintenance : signalement et transition avec isolation institutionnelle
02:35 +27 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_services_gateway_test.dart: Maintenance : chemins malformés et action inconnue refusés
02:36 +28 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/combined_access_test.dart: Campus does not grant personal Premium
02:37 +29 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/combined_access_test.dart: Suspended Campus does not remove personal Premium
02:37 +30 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/commerce_domain_test.dart: offline premium requires both lease and subscription to be valid
02:37 +31 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/commerce_domain_test.dart: payment terminal states are explicit
02:39 +32 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/engagement/engagement_domain_test.dart: preferences copyWith preserves untouched values
02:39 +33 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/engagement/engagement_domain_test.dart: notification model keeps priority and expiry
test/library_catalog_refresh_test.dart:18:7: Error: The non-abstract class 'FakeLocalLibrary' is missing implementations for these members:
 - LibraryLocalRepository.setCourseFollowed
Try to either
 - provide an implementation,
 - inherit an implementation from a superclass or mixin,
 - mark the class as abstract, or
 - provide a 'noSuchMethod' implementation.

class FakeLocalLibrary implements LibraryLocalRepository {
      ^^^^^^^^^^^^^^^^
lib/src/features/library/application/library_repository.dart:9:16: Context: 'LibraryLocalRepository.setCourseFollowed' is defined here.
  Future<void> setCourseFollowed(String courseId, bool followed);
               ^^^^^^^^^^^^^^^^^
02:41 +34 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/import_personal_document_test.dart: personal import persists metadata and queues outbox event
02:43 +35 -8: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart: test/library_catalog_refresh_test.dart:18:7: Error: The non-abstract class 'FakeLocalLibrary' is missing implementations for these members:
   - LibraryLocalRepository.setCourseFollowed
  Try to either
   - provide an implementation,
   - inherit an implementation from a superclass or mixin,
   - mark the class as abstract, or
   - provide a 'noSuchMethod' implementation.
  
  class FakeLocalLibrary implements LibraryLocalRepository {
        ^^^^^^^^^^^^^^^^
  lib/src/features/library/application/library_repository.dart:9:16: Context: 'LibraryLocalRepository.setCourseFollowed' is defined here.
    Future<void> setCourseFollowed(String courseId, bool followed);
                 ^^^^^^^^^^^^^^^^^
  .
02:53 +35 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/local_quiz_evaluator_test.dart: multiple choice partial scoring penalizes guessing
02:53 +36 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/local_quiz_evaluator_test.dart: numeric supports absolute tolerance
02:53 +37 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/local_quiz_evaluator_test.dart: free text supports accepted variants
02:58 +38 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: again resets repetition and records a lapse
02:58 +39 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval
02:58 +39 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]
  Expected: <32>
    Actual: <33>
  
  package:matcher                                     expect
```

## Flutter — 03:02 +46 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
tation,
 - inherit an implementation from a superclass or mixin,
 - mark the class as abstract, or
 - provide a 'noSuchMethod' implementation.

class FakeLocalLibrary implements LibraryLocalRepository {
      ^^^^^^^^^^^^^^^^
lib/src/features/library/application/library_repository.dart:9:16: Context: 'LibraryLocalRepository.setCourseFollowed' is defined here.
  Future<void> setCourseFollowed(String courseId, bool followed);
               ^^^^^^^^^^^^^^^^^
02:41 +34 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/import_personal_document_test.dart: personal import persists metadata and queues outbox event
02:43 +35 -8: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart: test/library_catalog_refresh_test.dart:18:7: Error: The non-abstract class 'FakeLocalLibrary' is missing implementations for these members:
   - LibraryLocalRepository.setCourseFollowed
  Try to either
   - provide an implementation,
   - inherit an implementation from a superclass or mixin,
   - mark the class as abstract, or
   - provide a 'noSuchMethod' implementation.
  
  class FakeLocalLibrary implements LibraryLocalRepository {
        ^^^^^^^^^^^^^^^^
  lib/src/features/library/application/library_repository.dart:9:16: Context: 'LibraryLocalRepository.setCourseFollowed' is defined here.
    Future<void> setCourseFollowed(String courseId, bool followed);
                 ^^^^^^^^^^^^^^^^^
  .
02:53 +35 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/local_quiz_evaluator_test.dart: multiple choice partial scoring penalizes guessing
02:53 +36 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/local_quiz_evaluator_test.dart: numeric supports absolute tolerance
02:53 +37 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/local_quiz_evaluator_test.dart: free text supports accepted variants
02:58 +38 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: again resets repetition and records a lapse
02:58 +39 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval
02:58 +39 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]
  Expected: <32>
    Actual: <33>
  
  package:matcher                                     expect
  package:flutter_test/src/widget_tester.dart 473:18  expect
  test\pedagogy_scheduler_test.dart 26:5              main.<fn>
  
02:59 +39 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/planning_engine_test.dart: planning engine prioritizes imminent weak course and respects budget
02:59 +40 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/planning_engine_test.dart: emergency plan consumes requested budget
03:00 +41 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/schedule_text_parser_test.dart: parses French OCR timetable rows conservatively
03:02 +42 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/secure_session_account_ownership_test.dart: logout retains ownership and blocks another account
03:02 +43 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
03:02 +44 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
03:02 +45 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
03:02 +46 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
03:02 +46 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'unknown_push_disposition'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:02 +46 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
 C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: again resets repetition and records a lapse
02:58 +39 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval
02:58 +39 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]
  Expected: <32>
    Actual: <33>
  
  package:matcher                                     expect
  package:flutter_test/src/widget_tester.dart 473:18  expect
  test\pedagogy_scheduler_test.dart 26:5              main.<fn>
  
02:59 +39 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/planning_engine_test.dart: planning engine prioritizes imminent weak course and respects budget
02:59 +40 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/planning_engine_test.dart: emergency plan consumes requested budget
03:00 +41 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/schedule_text_parser_test.dart: parses French OCR timetable rows conservatively
03:02 +42 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/secure_session_account_ownership_test.dart: logout retains ownership and blocks another account
03:02 +43 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
03:02 +44 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
03:02 +45 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
03:02 +46 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
03:02 +46 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'unknown_push_disposition'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: unknown_push_disposition")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 94:11                                  main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 94:11           main.<fn>
  
03:02 +46 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox
03:02 +46 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'missing_canonical_conflict'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:03 +46 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
_disposition'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: unknown_push_disposition")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 94:11                                  main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 94:11           main.<fn>
  
03:02 +46 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox
03:02 +46 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'missing_canonical_conflict'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: missing_canonical_conflict")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 100:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 100:11          main.<fn>
  
03:02 +46 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity
03:03 +46 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:03 +46 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
sage`: 'missing_canonical_conflict'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: missing_canonical_conflict")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 100:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 100:11          main.<fn>
  
03:02 +46 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity
03:03 +46 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 106:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 106:11          main.<fn>
  
03:03 +46 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes
03:03 +46 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:03 +46 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
d: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 106:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 106:11          main.<fn>
  
03:03 +46 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes
03:03 +46 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 114:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 114:11          main.<fn>
  
03:03 +46 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes
03:03 +46 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:03 +46 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text

  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 114:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 114:11          main.<fn>
  
03:03 +46 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes
03:03 +46 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 122:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 122:11          main.<fn>
  
03:03 +46 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement
03:03 +46 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:03 +46 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
rsion is rejected before writes
03:03 +46 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 122:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 122:11          main.<fn>
  
03:03 +46 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement
03:03 +46 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_pull_cursor")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 134:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 134:11          main.<fn>
  
03:03 +46 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected
03:03 +46 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:03 +46 -17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
st\sync_push_integrity_test.dart 122:11          main.<fn>
  
03:03 +46 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement
03:03 +46 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_pull_cursor")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 134:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 134:11          main.<fn>
  
03:03 +46 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected
03:03 +46 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_pull_cursor")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 143:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 143:11          main.<fn>
  
03:03 +46 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox
03:03 +46 -17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'incomplete_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:03 +46 -18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
paginated pull cursor is rejected
03:03 +46 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_pull_cursor")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 143:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 143:11          main.<fn>
  
03:03 +46 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox
03:03 +46 -17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'incomplete_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: incomplete_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 147:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 147:11          main.<fn>
  
03:03 +46 -17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox
03:03 +46 -18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:03 +46 -19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text

  Expected: throws <Instance of 'StateError'> with `message`: 'incomplete_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: incomplete_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 147:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 147:11          main.<fn>
  
03:03 +46 -17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox
03:03 +46 -18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 150:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 150:11          main.<fn>
  
03:03 +46 -18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox
03:03 +46 -19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:03 +47 -20: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: simultaneous triggers share a single push and release lock after failure [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
hMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 150:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 150:11          main.<fn>
  
03:03 +46 -18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox
03:03 +46 -19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 156:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 156:11          main.<fn>
  
03:03 +46 -19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: account switch during push cannot commit old account outcomes
03:03 +47 -19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: simultaneous triggers share a single push and release lock after failure
03:03 +47 -20: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: simultaneous triggers share a single push and release lock after failure [E]
  Expected: throws <Instance of 'StateError'>
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 03:23 +49 -21: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Revoir les imports, contrats d’interface et fixtures indiqués dans la trace ; réexécuter les mêmes assertions après correction. Les résultats des reprises sont séparés.

Trace complète : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log). Extrait du flux de test :

```text
               expectLater
                  test\sync_push_integrity_test.dart 197:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 197:11          main.<fn>
  
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
         ^^^^^
03:07 +47 -20: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
03:11 +48 -20: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: EmptyStateCard exposes clear title and action
lib/src/features/delivery/application/delivery_repository.dart:56:90: Error: Type 'DownloadResource' not found.
  final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
                                                                                         ^^^^^^^^^^^^^^^^
lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
 - 'Map' is from 'dart:core'.
 - 'Future' is from 'dart:async'.
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
    ^
lib/src/features/delivery/application/delivery_repository.dart:56:90: Error: 'DownloadResource' isn't a type.
  final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
                                                                                         ^^^^^^^^^^^^^^^^
lib/src/features/delivery/application/download_resource.dart:30:25: Error: Not a constant expression.
        final ids=const CacheEvictionPlanner().plan(candidates:await local.cacheCandidates(),currentBytes:currentCache,targetBytes:(policy.maxCacheBytes-grant.sizeBytes).clamp(0,policy.maxCacheBytes).toInt(),keepFollowed:policy.keepFollowedCourses);
                        ^^^^^^^^^^^^^^^^^^^^
lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:45:29: Error: Too many positional arguments: 0 allowed, but 1 found.
Try removing the extra positional arguments.
    await _plugin.initialize(
                            ^
lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:78:32: Error: Too many positional arguments: 0 allowed, but 5 found.
Try removing the extra positional arguments.
    await _plugin.zonedSchedule(_id(n.id),n.title,n.body,tz.TZDateTime.from(n.fireAt.toUtc(),tz.UTC),details,androidScheduleMode:AndroidScheduleMode.inexactAllowWhileIdle,payload:payload);
                               ^
lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:81:91: Error: Too many positional arguments: 0 allowed, but 1 found.
Try removing the extra positional arguments.
  @override Future<void> cancel(String id) async {await initialize(); await _plugin.cancel(_id(id));}
                                                                                          ^
lib/src/features/identity/infrastructure/legacy_offline_files_native.dart:11:45: Error: The getter 'isNotEmpty' isn't defined for the type 'Stream<FileSystemEntity>'.
 - 'Stream' is from 'dart:async'.
 - 'FileSystemEntity' is from 'dart:io'.
Try correcting the name to the name of an existing getter, or defining a getter or field named 'isNotEmpty'.
  return directory.list(followLinks: false).isNotEmpty;
                                            ^^^^^^^^^^
03:23 +49 -21: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart [E]
  Failed to load "C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart":
  Compilation failed for testPath=C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:10: Error: 'await' can only be used in 'async' or 'async*' methods.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
           ^^^^^
```

## Flutter — 00:52 +21 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart: API institutionnelle authentifiée selection, scope, jeton et absence de mutation [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Les paramètres encodés dans une URI n’étaient pas exposés dans queryParameters. Utiliser les paramètres GET/POST explicites de Dio en conservant auth, scope et no-store.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart
00:00 +0: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: momentum is explainable and improving
00:00 +1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: high cognitive work is skipped in low energy window
00:00 +2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: urgent low readiness course is prioritized
00:00 +3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: planner respects study capacity and breaks
00:00 +4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: recommendations remain diversified
00:00 +5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: deferred work gains explicit priority reason
00:00 +6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: activity timeline is preserved for premium UI
00:00 +7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: course insight exposes drilldown dimensions
00:00 +8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: course recommendation links keep the human title
00:04 +9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Affection d’un événement du calendrier, libération CAS, tenant
00:04 +10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Réconciliation des séances et découverte Alumni vérifiée, sans cache
00:04 +11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Alumni : consentement explicite, validation et opportunités gouvernées
00:04 +12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Isolation du chemin d’université et absence de session
00:06 +13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Alertes personnelles : GET scellé au tenant, bearer, no-cache
00:06 +14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Réponses malformées et doublons ne doivent pas être affichés
00:09 +15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Événements : routes scellées au tenant et au bearer; versions conservées
00:10 +16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Identifiants de tenants dangereux rejetés sans requête réseau
00:34 +17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:49 +18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:50 +19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:51 +20: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:52 +21: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:52 +21 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:52 +21 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart: API institutionnelle authentifiée selection, scope, jeton et absence de mutation [E]
  Expected: 'fac-1'
    Actual: <null>
     Which: not an <Instance of 'String'>
  
```

## Flutter — 00:58 +27 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_governance_gateway_test.dart: ph15 archives: périmètre faculté, export volatil, historique gouverné [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Les paramètres encodés dans une URI n’étaient pas exposés dans queryParameters. Utiliser les paramètres GET/POST explicites de Dio en conservant auth, scope et no-store.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
dart: activity timeline is preserved for premium UI
00:00 +7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: course insight exposes drilldown dimensions
00:00 +8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: course recommendation links keep the human title
00:04 +9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Affection d’un événement du calendrier, libération CAS, tenant
00:04 +10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Réconciliation des séances et découverte Alumni vérifiée, sans cache
00:04 +11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Alumni : consentement explicite, validation et opportunités gouvernées
00:04 +12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Isolation du chemin d’université et absence de session
00:06 +13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Alertes personnelles : GET scellé au tenant, bearer, no-cache
00:06 +14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Réponses malformées et doublons ne doivent pas être affichés
00:09 +15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Événements : routes scellées au tenant et au bearer; versions conservées
00:10 +16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Identifiants de tenants dangereux rejetés sans requête réseau
00:34 +17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:49 +18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:50 +19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:51 +20: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:52 +21: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:52 +21 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:52 +21 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_gateway_test.dart: API institutionnelle authentifiée selection, scope, jeton et absence de mutation [E]
  Expected: 'fac-1'
    Actual: <null>
     Which: not an <Instance of 'String'>
  
  package:matcher                                     expect
  package:flutter_test/src/widget_tester.dart 473:18  expect
  test\campus_intelligence_gateway_test.dart 76:7     main.<fn>.<fn>
  
00:52 +22 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:52 +23 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:55 +24 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:56 +25 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:57 +26 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:58 +27 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:58 +27 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:58 +27 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_governance_gateway_test.dart: ph15 archives: périmètre faculté, export volatil, historique gouverné [E]
  Expected: 'academic_unit'
    Actual: <null>
     Which: not an <Instance of 'String'>
  
```

## Flutter — 01:13 +54 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Un nouveau fournisseur Alumni réel restait en attente dans la fixture. Le remplacer par une réponse vide contrôlée ; conserver les assertions RBAC.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
_test.dart: membre étudiant : aucun accès aux analyses
01:04 +37 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:04 +38 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:04 +39 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:05 +40 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:05 +41 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:05 +42 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:05 +43 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:05 +44 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:05 +45 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:05 +46 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:05 +47 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:07 +48 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:07 +49 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:09 +50 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:09 +51 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:09 +52 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:09 +53 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:10 +54 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following assertion was thrown running a test:
pumpAndSettle timed out

When the exception was thrown, this was the stack:
#0      WidgetTester.pumpAndSettle.<anonymous closure> (package:flutter_test/src/widget_tester.dart:717:11)
<asynchronous suspension>
#1      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#2      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:75:5)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  membre étudiant : aucun accès aux analyses
════════════════════════════════════════════════════════════════════════════════════════════════════
01:13 +54 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses [E]
  Test failed. See exception logs above.
  The test description was: membre étudiant : aucun accès aux analyses
  
01:13 +54 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
```

## Flutter — 01:22 +64 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Attente arithmétique incorrecte du test : 32,5 est arrondi à 33 par Dart. Corriger la valeur attendue sans changer le planificateur.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
alyses
01:07 +49 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:09 +50 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:09 +51 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:09 +52 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:09 +53 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
01:10 +54 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following assertion was thrown running a test:
pumpAndSettle timed out

When the exception was thrown, this was the stack:
#0      WidgetTester.pumpAndSettle.<anonymous closure> (package:flutter_test/src/widget_tester.dart:717:11)
<asynchronous suspension>
#1      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#2      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:75:5)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  membre étudiant : aucun accès aux analyses
════════════════════════════════════════════════════════════════════════════════════════════════════
01:13 +54 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses [E]
  Test failed. See exception logs above.
  The test description was: membre étudiant : aucun accès aux analyses
  
01:13 +54 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:16 +55 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:16 +56 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:17 +57 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:20 +58 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:20 +59 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:20 +60 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:21 +61 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:21 +62 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:21 +63 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +64 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +64 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +64 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]
  Expected: <32>
    Actual: <33>
  
  package:matcher                                     expect
```

## Flutter — 01:24 +66 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Un nouveau fournisseur Alumni réel restait en attente dans la fixture. Le remplacer par une réponse vide contrôlée ; conserver les assertions RBAC.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
igence_access_widget_test.dart: membre étudiant : aucun accès aux analyses [E]
  Test failed. See exception logs above.
  The test description was: membre étudiant : aucun accès aux analyses
  
01:13 +54 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:16 +55 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:16 +56 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:17 +57 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:20 +58 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:20 +59 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:20 +60 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:21 +61 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:21 +62 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:21 +63 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +64 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +64 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +64 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]
  Expected: <32>
    Actual: <33>
  
  package:matcher                                     expect
  package:flutter_test/src/widget_tester.dart 473:18  expect
  test\pedagogy_scheduler_test.dart 26:5              main.<fn>
  
01:22 +65 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +66 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following assertion was thrown running a test:
pumpAndSettle timed out

When the exception was thrown, this was the stack:
#0      WidgetTester.pumpAndSettle.<anonymous closure> (package:flutter_test/src/widget_tester.dart:717:11)
<asynchronous suspension>
#1      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#2      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:84:5)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  invitation non acceptée : accès interdit
════════════════════════════════════════════════════════════════════════════════════════════════════
01:24 +66 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/schedule_text_parser_test.dart: parses French OCR timetable rows conservatively
01:24 +66 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit [E]
  Test failed. See exception logs above.
  The test description was: invitation non acceptée : accès interdit
  
01:24 +67 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
```

## Flutter — 01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
t.dart: invitation non acceptée : accès interdit
01:22 +64 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +64 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +64 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]
  Expected: <32>
    Actual: <33>
  
  package:matcher                                     expect
  package:flutter_test/src/widget_tester.dart 473:18  expect
  test\pedagogy_scheduler_test.dart 26:5              main.<fn>
  
01:22 +65 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
01:22 +66 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following assertion was thrown running a test:
pumpAndSettle timed out

When the exception was thrown, this was the stack:
#0      WidgetTester.pumpAndSettle.<anonymous closure> (package:flutter_test/src/widget_tester.dart:717:11)
<asynchronous suspension>
#1      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#2      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:84:5)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  invitation non acceptée : accès interdit
════════════════════════════════════════════════════════════════════════════════════════════════════
01:24 +66 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/schedule_text_parser_test.dart: parses French OCR timetable rows conservatively
01:24 +66 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit [E]
  Test failed. See exception logs above.
  The test description was: invitation non acceptée : accès interdit
  
01:24 +67 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
01:25 +68 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
01:25 +69 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
01:25 +70 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
01:25 +71 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
01:25 +72 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: auditeur actif : accès aux indicateurs, pas à la gestion pédagogique
01:27 +73 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'unknown_push_disposition'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +73 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Revoir les imports, contrats d’interface et fixtures indiqués dans la trace ; réexécuter les mêmes assertions après correction. Les résultats des reprises sont séparés.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
e analytique
01:25 +72 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: auditeur actif : accès aux indicateurs, pas à la gestion pédagogique
01:27 +73 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'unknown_push_disposition'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: unknown_push_disposition")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 94:11                                  main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 94:11           main.<fn>
  
01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Masqué / non disponible": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:117:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart line 117
The test description was:
  direction : masque les pourcentages supprimés
════════════════════════════════════════════════════════════════════════════════════════════════════
01:29 +73 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox
01:29 +73 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]
  Test failed. See exception logs above.
  The test description was: direction : masque les pourcentages supprimés
  
01:29 +73 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox [E]
```

## Flutter — 01:29 +73 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
que les pourcentages supprimés
01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'unknown_push_disposition'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: unknown_push_disposition")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 94:11                                  main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 94:11           main.<fn>
  
01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Masqué / non disponible": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:117:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart line 117
The test description was:
  direction : masque les pourcentages supprimés
════════════════════════════════════════════════════════════════════════════════════════════════════
01:29 +73 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox
01:29 +73 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]
  Test failed. See exception logs above.
  The test description was: direction : masque les pourcentages supprimés
  
01:29 +73 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'missing_canonical_conflict'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +73 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
      main.<fn>
  
01:29 +73 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Masqué / non disponible": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:117:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart line 117
The test description was:
  direction : masque les pourcentages supprimés
════════════════════════════════════════════════════════════════════════════════════════════════════
01:29 +73 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox
01:29 +73 -7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]
  Test failed. See exception logs above.
  The test description was: direction : masque les pourcentages supprimés
  
01:29 +73 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'missing_canonical_conflict'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: missing_canonical_conflict")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 100:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 100:11          main.<fn>
  
01:29 +73 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity
01:29 +73 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +73 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
message`: 'missing_canonical_conflict'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: missing_canonical_conflict")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 100:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 100:11          main.<fn>
  
01:29 +73 -8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity
01:29 +73 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 106:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 106:11          main.<fn>
  
01:29 +73 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes
01:29 +73 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +73 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
ed: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 106:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 106:11          main.<fn>
  
01:29 +73 -9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes
01:29 +73 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 114:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 114:11          main.<fn>
  
01:29 +73 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes
01:29 +73 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +73 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text

  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 114:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 114:11          main.<fn>
  
01:29 +73 -10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes
01:29 +73 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 122:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 122:11          main.<fn>
  
01:29 +73 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement
01:29 +73 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +73 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
rsion is rejected before writes
01:29 +73 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_record'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_record")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 122:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 122:11          main.<fn>
  
01:29 +73 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement
01:29 +73 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_pull_cursor")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 134:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 134:11          main.<fn>
  
01:29 +73 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected
01:29 +73 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +73 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
st\sync_push_integrity_test.dart 122:11          main.<fn>
  
01:29 +73 -11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement
01:29 +73 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_pull_cursor")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 134:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 134:11          main.<fn>
  
01:29 +73 -12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected
01:29 +73 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_pull_cursor")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 143:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 143:11          main.<fn>
  
01:29 +73 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox
01:29 +73 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'incomplete_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +73 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
paginated pull cursor is rejected
01:29 +73 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_pull_cursor'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_pull_cursor")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 143:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 143:11          main.<fn>
  
01:29 +73 -13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox
01:29 +73 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'incomplete_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: incomplete_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 147:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 147:11          main.<fn>
  
01:29 +73 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox
01:29 +73 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +73 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text

  Expected: throws <Instance of 'StateError'> with `message`: 'incomplete_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: incomplete_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 147:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 147:11          main.<fn>
  
01:29 +73 -14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox
01:29 +73 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 150:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 150:11          main.<fn>
  
01:29 +73 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox
01:29 +73 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:29 +74 -17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: simultaneous triggers share a single push and release lock after failure [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Le faux dépôt ne fournissait pas recordSyncError : l’erreur d’interface masquait la StateError attendue. Correctif : compléter le faux dépôt ; conserver les assertions de rejet des payloads et de non-écriture partielle.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
hMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 150:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 150:11          main.<fn>
  
01:29 +73 -15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox
01:29 +73 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox [E]
  Expected: throws <Instance of 'StateError'> with `message`: 'invalid_push_outcomes'
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
                  Tried calling: recordSyncError("account", "Bad state: invalid_push_outcomes")
                  Found: recordSyncError(String, String) => Future<void>>
            stack dart:core                                                                 Object.noSuchMethod
                  test\sync_push_integrity_test.dart 55:56                                  _Local.noSuchMethod
                  test\sync_push_integrity_test.dart 7:7                                    _Local.recordSyncError
                  package:edunova/src/features/sync/application/run_cloud_sync.dart 165:21  RunCloudSync._run
                  ===== asynchronous gap ===========================
                  package:matcher                                                           expectLater
                  package:flutter_test/src/widget_tester.dart 507:8                         expectLater
                  test\sync_push_integrity_test.dart 87:11                                  main.verifyRejected
                  test\sync_push_integrity_test.dart 156:11                                 main.<fn>
                  
            which is not an instance of 'StateError'
  
  package:matcher                                    expectLater
  package:flutter_test/src/widget_tester.dart 507:8  expectLater
  test\sync_push_integrity_test.dart 87:11           main.verifyRejected
  test\sync_push_integrity_test.dart 156:11          main.<fn>
  
01:29 +73 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: account switch during push cannot commit old account outcomes
01:29 +74 -16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: simultaneous triggers share a single push and release lock after failure
01:29 +74 -17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: simultaneous triggers share a single push and release lock after failure [E]
  Expected: throws <Instance of 'StateError'>
    Actual: <Instance of 'Future<SyncRunResult>'>
     Which: threw NoSuchMethodError:<NoSuchMethodError: Class '_Local' has no instance method 'recordSyncError' with matching arguments.
                  Receiver: Instance of '_Local'
```

## Flutter — 01:35 +76 -18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders premium preparation card [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Fixture d’accueil obsolète : ProviderScope absent et attente de données de démonstration. Fournir un compte local vide contrôlé et vérifier son vrai parcours de préparation.

Trace complète : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log). Extrait du flux de test :

```text
435:7)
#759    StatelessElement.update (package:flutter/src/widgets/framework.dart:5797:5)
#760    Element.updateChild (package:flutter/src/widgets/framework.dart:3982:15)
#761    ComponentElement.performRebuild (package:flutter/src/widgets/framework.dart:5747:16)
#762    StatefulElement.performRebuild (package:flutter/src/widgets/framework.dart:5884:11)
#763    Element.rebuild (package:flutter/src/widgets/framework.dart:5435:7)
#764    StatefulElement.update (package:flutter/src/widgets/framework.dart:5909:5)
#765    Element.updateChild (package:flutter/src/widgets/framework.dart:3982:15)
#766    RootElement._rebuild (package:flutter/src/widgets/binding.dart:1716:16)
#767    RootElement.update (package:flutter/src/widgets/binding.dart:1694:5)
#768    RootElement.performRebuild (package:flutter/src/widgets/binding.dart:1708:7)
#769    Element.rebuild (package:flutter/src/widgets/framework.dart:5435:7)
#770    BuildScope._tryRebuild (package:flutter/src/widgets/framework.dart:2695:15)
#771    BuildScope._flushDirtyElements (package:flutter/src/widgets/framework.dart:2752:11)
#772    BuildOwner.buildScope (package:flutter/src/widgets/framework.dart:3056:18)
#773    AutomatedTestWidgetsFlutterBinding.drawFrame (package:flutter_test/src/binding.dart:1506:19)
#774    RendererBinding._handlePersistentFrameCallback (package:flutter/src/rendering/binding.dart:495:5)
#775    SchedulerBinding._invokeFrameCallback (package:flutter/src/scheduler/binding.dart:1434:15)
#776    SchedulerBinding.handleDrawFrame (package:flutter/src/scheduler/binding.dart:1347:9)
#777    AutomatedTestWidgetsFlutterBinding.pump.<anonymous closure> (package:flutter_test/src/binding.dart:1335:9)
#780    TestAsyncUtils.guard (package:flutter_test/src/test_async_utils.dart:74:41)
#781    AutomatedTestWidgetsFlutterBinding.pump (package:flutter_test/src/binding.dart:1324:27)
#782    WidgetTester.pumpWidget.<anonymous closure> (package:flutter_test/src/widget_tester.dart:598:22)
#785    TestAsyncUtils.guard (package:flutter_test/src/test_async_utils.dart:74:41)
#786    WidgetTester.pumpWidget (package:flutter_test/src/widget_tester.dart:595:27)
#787    main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart:8:18)
#788    testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:29)
<asynchronous suspension>
#789    TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 5 frames from dart:async and package:stack_trace)

════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: at least one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Biochimie": []>
   Which: means none were found but some were expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart:9:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart line 9
The test description was:
  home renders premium preparation card
════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following message was thrown:
Multiple exceptions (2) were detected during the running of the current test, and at least one was
unexpected.
════════════════════════════════════════════════════════════════════════════════════════════════════
01:35 +76 -18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders premium preparation card [E]
  Test failed. See exception logs above.
  The test description was: home renders premium preparation card
  
01:35 +76 -18: Some tests failed.
```

## Flutter — 00:27 +24 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_governance_gateway_test.dart: ph15 archives: périmètre faculté, export volatil, historique gouverné [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Les paramètres encodés dans une URI n’étaient pas exposés dans queryParameters. Utiliser les paramètres GET/POST explicites de Dio en conservant auth, scope et no-store.

Trace complète : [mobile-test-previous-1793436711215236100.log](mobile-test-previous-1793436711215236100.log). Extrait du flux de test :

```text
ter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart
00:00 +0: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: high cognitive work is skipped in low energy window
00:00 +1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: planner respects study capacity and breaks
00:00 +2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: deferred work gains explicit priority reason
00:01 +3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: momentum is explainable and improving
00:01 +4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: urgent low readiness course is prioritized
00:01 +5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: recommendations remain diversified
00:01 +6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: activity timeline is preserved for premium UI
00:01 +7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: course insight exposes drilldown dimensions
00:01 +8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: course recommendation links keep the human title
00:04 +9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Affection d’un événement du calendrier, libération CAS, tenant
00:05 +10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Réconciliation des séances et découverte Alumni vérifiée, sans cache
00:05 +11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Alumni : consentement explicite, validation et opportunités gouvernées
00:05 +12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Isolation du chemin d’université et absence de session
00:06 +13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Alertes personnelles : GET scellé au tenant, bearer, no-cache
00:06 +14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Réponses malformées et doublons ne doivent pas être affichés
00:08 +15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Événements : routes scellées au tenant et au bearer; versions conservées
00:08 +16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Identifiants de tenants dangereux rejetés sans requête réseau
00:14 +17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:21 +18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:21 +19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:21 +20: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:21 +21: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:26 +22: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:27 +23: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:27 +24: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:27 +24 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:27 +24 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_governance_gateway_test.dart: ph15 archives: périmètre faculté, export volatil, historique gouverné [E]
  Expected: 'fac1'
    Actual: <null>
     Which: not an <Instance of 'String'>
  
```

## Flutter — 00:34 +33 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Un nouveau fournisseur Alumni réel restait en attente dans la fixture. Le remplacer par une réponse vide contrôlée ; conserver les assertions RBAC.

Trace complète : [mobile-test-previous-1793436711215236100.log](mobile-test-previous-1793436711215236100.log). Extrait du flux de test :

```text
alyses
00:21 +21: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:26 +22: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:27 +23: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:27 +24: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:27 +24 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:27 +24 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_governance_gateway_test.dart: ph15 archives: périmètre faculté, export volatil, historique gouverné [E]
  Expected: 'fac1'
    Actual: <null>
     Which: not an <Instance of 'String'>
  
  package:matcher                                             expect
  package:flutter_test/src/widget_tester.dart 473:18          expect
  test\campus_intelligence_governance_gateway_test.dart 75:5  main.<fn>
  
00:27 +25 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:27 +26 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:28 +27 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:28 +28 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:28 +29 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:34 +30 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:34 +31 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:34 +32 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:34 +33 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following assertion was thrown running a test:
pumpAndSettle timed out

When the exception was thrown, this was the stack:
#0      WidgetTester.pumpAndSettle.<anonymous closure> (package:flutter_test/src/widget_tester.dart:717:11)
<asynchronous suspension>
#1      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#2      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:75:5)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  membre étudiant : aucun accès aux analyses
════════════════════════════════════════════════════════════════════════════════════════════════════
00:34 +33 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_tenant_transition_widget_test.dart: référence de cours ambiguë : aucune analyse exécutée
00:34 +33 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses [E]
  Test failed. See exception logs above.
  The test description was: membre étudiant : aucun accès aux analyses
  
00:34 +34 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_tenant_transition_widget_test.dart: référence de cours ambiguë : aucune analyse exécutée
```

## Flutter — 00:45 +56 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Un nouveau fournisseur Alumni réel restait en attente dans la fixture. Le remplacer par une réponse vide contrôlée ; conserver les assertions RBAC.

Trace complète : [mobile-test-previous-1793436711215236100.log](mobile-test-previous-1793436711215236100.log). Extrait du flux de test :

```text
 référence de cours ambiguë : aucune analyse exécutée
00:34 +40 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_tenant_transition_widget_test.dart: référence de cours ambiguë : aucune analyse exécutée
00:35 +41 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:38 +42 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:38 +43 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:38 +44 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:38 +45 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:38 +46 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:38 +47 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:38 +48 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:39 +49 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:39 +50 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:39 +51 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:39 +52 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:41 +53 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:43 +54 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:43 +55 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:45 +56 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following assertion was thrown running a test:
pumpAndSettle timed out

When the exception was thrown, this was the stack:
#0      WidgetTester.pumpAndSettle.<anonymous closure> (package:flutter_test/src/widget_tester.dart:717:11)
<asynchronous suspension>
#1      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#2      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:84:5)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  invitation non acceptée : accès interdit
════════════════════════════════════════════════════════════════════════════════════════════════════
00:45 +56 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/engagement/engagement_domain_test.dart: notification model keeps priority and expiry
00:45 +56 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit [E]
  Test failed. See exception logs above.
  The test description was: invitation non acceptée : accès interdit
  
00:45 +57 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
```

## Flutter — 00:48 +60 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Un nouveau fournisseur Alumni réel restait en attente dans la fixture. Le remplacer par une réponse vide contrôlée ; conserver les assertions RBAC.

Trace complète : [mobile-test-previous-1793436711215236100.log](mobile-test-previous-1793436711215236100.log). Extrait du flux de test :

```text
_access_widget_test.dart: invitation non acceptée : accès interdit
00:43 +54 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:43 +55 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:45 +56 -2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following assertion was thrown running a test:
pumpAndSettle timed out

When the exception was thrown, this was the stack:
#0      WidgetTester.pumpAndSettle.<anonymous closure> (package:flutter_test/src/widget_tester.dart:717:11)
<asynchronous suspension>
#1      TestAsyncUtils.guard.<anonymous closure> (package:flutter_test/src/test_async_utils.dart:130:27)
<asynchronous suspension>
#2      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:84:5)
<asynchronous suspension>
#3      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  invitation non acceptée : accès interdit
════════════════════════════════════════════════════════════════════════════════════════════════════
00:45 +56 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/engagement/engagement_domain_test.dart: notification model keeps priority and expiry
00:45 +56 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit [E]
  Test failed. See exception logs above.
  The test description was: invitation non acceptée : accès interdit
  
00:45 +57 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
00:45 +58 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: auditeur actif : accès aux indicateurs, pas à la gestion pédagogique
00:46 +59 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
00:47 +60 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Masqué / non disponible": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:117:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart line 117
The test description was:
  direction : masque les pourcentages supprimés
════════════════════════════════════════════════════════════════════════════════════════════════════
00:48 +60 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]
  Test failed. See exception logs above.
  The test description was: direction : masque les pourcentages supprimés
  
00:49 +60 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart: complete paginated catalog is reconciled atomically
```

## Flutter — 00:51 +67 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Attente arithmétique incorrecte du test : 32,5 est arrondi à 33 par Dart. Corriger la valeur attendue sans changer le planificateur.

Trace complète : [mobile-test-previous-1793436711215236100.log](mobile-test-previous-1793436711215236100.log). Extrait du flux de test :

```text
losure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#4      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

The test description was:
  invitation non acceptée : accès interdit
════════════════════════════════════════════════════════════════════════════════════════════════════
00:45 +56 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/engagement/engagement_domain_test.dart: notification model keeps priority and expiry
00:45 +56 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit [E]
  Test failed. See exception logs above.
  The test description was: invitation non acceptée : accès interdit
  
00:45 +57 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
00:45 +58 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: auditeur actif : accès aux indicateurs, pas à la gestion pédagogique
00:46 +59 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
00:47 +60 -3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Masqué / non disponible": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:117:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart line 117
The test description was:
  direction : masque les pourcentages supprimés
════════════════════════════════════════════════════════════════════════════════════════════════════
00:48 +60 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]
  Test failed. See exception logs above.
  The test description was: direction : masque les pourcentages supprimés
  
00:49 +60 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart: complete paginated catalog is reconciled atomically
00:49 +61 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart: etag change during pagination keeps previous cache untouched
00:49 +62 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/library_catalog_refresh_test.dart: 304 does not rewrite local catalog
00:49 +63 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/local_quiz_evaluator_test.dart: multiple choice partial scoring penalizes guessing
00:49 +64 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/local_quiz_evaluator_test.dart: numeric supports absolute tolerance
00:49 +65 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/local_quiz_evaluator_test.dart: free text supports accepted variants
00:50 +66 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: again resets repetition and records a lapse
00:51 +67 -4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval
00:51 +67 -5: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/pedagogy_scheduler_test.dart: easy accelerates interval [E]
  Expected: <32>
    Actual: <33>
  
  package:matcher                                     expect
```

## Flutter — 01:06 +88 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders premium preparation card [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Fixture d’accueil obsolète : ProviderScope absent et attente de données de démonstration. Fournir un compte local vide contrôlé et vérifier son vrai parcours de préparation.

Trace complète : [mobile-test-previous-1793436711215236100.log](mobile-test-previous-1793436711215236100.log). Extrait du flux de test :

```text
:5435:7)
#759    StatelessElement.update (package:flutter/src/widgets/framework.dart:5797:5)
#760    Element.updateChild (package:flutter/src/widgets/framework.dart:3982:15)
#761    ComponentElement.performRebuild (package:flutter/src/widgets/framework.dart:5747:16)
#762    StatefulElement.performRebuild (package:flutter/src/widgets/framework.dart:5884:11)
#763    Element.rebuild (package:flutter/src/widgets/framework.dart:5435:7)
#764    StatefulElement.update (package:flutter/src/widgets/framework.dart:5909:5)
#765    Element.updateChild (package:flutter/src/widgets/framework.dart:3982:15)
#766    RootElement._rebuild (package:flutter/src/widgets/binding.dart:1716:16)
#767    RootElement.update (package:flutter/src/widgets/binding.dart:1694:5)
#768    RootElement.performRebuild (package:flutter/src/widgets/binding.dart:1708:7)
#769    Element.rebuild (package:flutter/src/widgets/framework.dart:5435:7)
#770    BuildScope._tryRebuild (package:flutter/src/widgets/framework.dart:2695:15)
#771    BuildScope._flushDirtyElements (package:flutter/src/widgets/framework.dart:2752:11)
#772    BuildOwner.buildScope (package:flutter/src/widgets/framework.dart:3056:18)
#773    AutomatedTestWidgetsFlutterBinding.drawFrame (package:flutter_test/src/binding.dart:1506:19)
#774    RendererBinding._handlePersistentFrameCallback (package:flutter/src/rendering/binding.dart:495:5)
#775    SchedulerBinding._invokeFrameCallback (package:flutter/src/scheduler/binding.dart:1434:15)
#776    SchedulerBinding.handleDrawFrame (package:flutter/src/scheduler/binding.dart:1347:9)
#777    AutomatedTestWidgetsFlutterBinding.pump.<anonymous closure> (package:flutter_test/src/binding.dart:1335:9)
#780    TestAsyncUtils.guard (package:flutter_test/src/test_async_utils.dart:74:41)
#781    AutomatedTestWidgetsFlutterBinding.pump (package:flutter_test/src/binding.dart:1324:27)
#782    WidgetTester.pumpWidget.<anonymous closure> (package:flutter_test/src/widget_tester.dart:598:22)
#785    TestAsyncUtils.guard (package:flutter_test/src/test_async_utils.dart:74:41)
#786    WidgetTester.pumpWidget (package:flutter_test/src/widget_tester.dart:595:27)
#787    main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart:8:18)
#788    testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:29)
<asynchronous suspension>
#789    TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 5 frames from dart:async and package:stack_trace)

════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: at least one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Biochimie": []>
   Which: means none were found but some were expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart:9:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart line 9
The test description was:
  home renders premium preparation card
════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following message was thrown:
Multiple exceptions (2) were detected during the running of the current test, and at least one was
unexpected.
════════════════════════════════════════════════════════════════════════════════════════════════════
01:06 +88 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders premium preparation card [E]
  Test failed. See exception logs above.
  The test description was: home renders premium preparation card
  
01:06 +88 -6: Some tests failed.
```

## Flutter — 00:09 +21 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Ciblage ambigu ou absent du widget défilant. Sélectionner le premier Scrollable institutionnel et rendre l’indicateur visible avant les mêmes assertions de masquage.

Trace complète : [mobile-test-previous-1793439446720879300.log](mobile-test-previous-1793439446720879300.log). Extrait du flux de test :

```text
: recommendations remain diversified
00:00 +6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: activity timeline is preserved for premium UI
00:00 +7: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: course insight exposes drilldown dimensions
00:00 +8: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: course recommendation links keep the human title
00:01 +9: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Affection d’un événement du calendrier, libération CAS, tenant
00:01 +10: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Réconciliation des séances et découverte Alumni vérifiée, sans cache
00:01 +11: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Alumni : consentement explicite, validation et opportunités gouvernées
00:01 +12: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Isolation du chemin d’université et absence de session
00:02 +13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Alertes personnelles : GET scellé au tenant, bearer, no-cache
00:02 +14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Réponses malformées et doublons ne doivent pas être affichés
00:02 +15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Événements : routes scellées au tenant et au bearer; versions conservées
00:02 +16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Identifiants de tenants dangereux rejetés sans requête réseau
00:04 +17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:06 +18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: invitation non acceptée : accès interdit
00:06 +19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: URL directe vers autre université : aucune requête analytique
00:07 +20: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: auditeur actif : accès aux indicateurs, pas à la gestion pédagogique
00:07 +21: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following StateError was thrown running a test:
Bad state: No element

When the exception was thrown, this was the stack:
#0      Iterable.last (dart:core/iterable.dart:679:7)
#1      _LastFinderMixin.filter (package:flutter_test/src/finders.dart:1359:28)
#3      Iterable.isEmpty (dart:core/iterable.dart:560:33)
#4      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2008:18)
#5      WidgetController.getCenter (package:flutter_test/src/controller.dart:1861:12)
#6      WidgetController.tap (package:flutter_test/src/controller.dart:1041:7)
#7      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:118:18)
<asynchronous suspension>
#8      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#9      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 2 frames from dart:async-patch and package:stack_trace)

The test description was:
  direction : masque les pourcentages supprimés
════════════════════════════════════════════════════════════════════════════════════════════════════
00:09 +21 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]
  Test failed. See exception logs above.
  The test description was: direction : masque les pourcentages supprimés
  
00:14 +21 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart: ph14: formulaire lié au vrai cours sans altération des notes
```

## Flutter — 00:33 +25 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]

Commande : `flutter test --no-pub --reporter=expanded` dans `apps/mobile` ; les options exactes de cette tentative figurent dans COMMANDS.md.

Ciblage ambigu ou absent du widget défilant. Sélectionner le premier Scrollable institutionnel et rendre l’indicateur visible avant les mêmes assertions de masquage.

Trace complète : [mobile-test-previous-1793443731860620100.log](mobile-test-previous-1793443731860620100.log). Extrait du flux de test :

```text
ev/edusync-web/edunova/apps/mobile/test/campus_academic_alumni_gateway_test.dart: Isolation du chemin d’université et absence de session
00:02 +13: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Alertes personnelles : GET scellé au tenant, bearer, no-cache
00:02 +14: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_alerts_gateway_test.dart: Réponses malformées et doublons ne doivent pas être affichés
00:04 +15: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Événements : routes scellées au tenant et au bearer; versions conservées
00:04 +16: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_events_gateway_test.dart: Identifiants de tenants dangereux rejetés sans requête réseau
00:13 +17: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:24 +18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:24 +19: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:24 +20: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:24 +21: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: membre étudiant : aucun accès aux analyses
00:26 +22: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart: une réponse CSV périmée ne réapparaît pas après changement de période
00:27 +23: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart: une réponse CSV périmée ne réapparaît pas après changement de période
00:27 +24: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart: une réponse CSV périmée ne réapparaît pas après changement de période
00:29 +25: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart: une réponse CSV périmée ne réapparaît pas après changement de période
00:33 +25: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following StateError was thrown running a test:
Bad state: Too many elements

When the exception was thrown, this was the stack:
#0      Iterable.single (dart:core/iterable.dart:696:24)
#1      WidgetController.widget (package:flutter_test/src/controller.dart:804:30)
#2      WidgetController.scrollUntilVisible.<anonymous closure> (package:flutter_test/src/controller.dart:2341:15)
#5      TestAsyncUtils.guard (package:flutter_test/src/test_async_utils.dart:74:41)
#6      WidgetController.scrollUntilVisible (package:flutter_test/src/controller.dart:2339:27)
#7      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart:118:18)
<asynchronous suspension>
#8      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#9      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 3 frames from dart:async and package:stack_trace)

The test description was:
  direction : masque les pourcentages supprimés
════════════════════════════════════════════════════════════════════════════════════════════════════
00:33 +25 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart: une réponse CSV périmée ne réapparaît pas après changement de période
00:33 +25 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_access_widget_test.dart: direction : masque les pourcentages supprimés [E]
  Test failed. See exception logs above.
  The test description was: direction : masque les pourcentages supprimés
  
00:34 +26 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/campus_intelligence_completion_widget_test.dart: ph14: formulaire lié au vrai cours sans altération des notes
```

## Audit structurel — scripts\audit_lot10_uiux_maximal.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot10_uiux_maximal.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
home_uses_analytics_provider: PASS
home_no_static_progress_cta: PASS
course_titles_in_deeplinks: PASS
course_insight_dimensions_domain: PASS
course_insight_context: PASS
generated_at_report: PASS
local_engine_no_ai: PASS
provider_local_engine: PASS
max_recommendations_5: PASS
recommendation_diversity: PASS
limited_evidence_caution: PASS
no_grade_prediction_engine: PASS
dark_theme_friendly: PASS
no_hardcoded_demo_course: PASS
touch_target_buttons: PASS
bottom_sheet_safe_area: PASS
course_action_plan: PASS
status_pills: PASS
progress_ring: PASS
chart_accessible_labels: PASS
responsive_readability: PASS
privacy_statement: PASS
snapshot_persistence: PASS
feedback_persistence: PASS
failed: version_mobile_0111
```

## Audit structurel — scripts\audit_lot11_maximal.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot11_maximal.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
PASS dart_balance:login_page.dart:{
PASS dart_balance:publication_center_page.dart:(
PASS dart_balance:publication_center_page.dart:[
PASS dart_balance:publication_center_page.dart:{
PASS dart_balance:question_factory_page.dart:(
PASS dart_balance:question_factory_page.dart:[
PASS dart_balance:question_factory_page.dart:{
PASS dart_balance:studio_session.dart:(
PASS dart_balance:studio_session.dart:[
PASS dart_balance:studio_session.dart:{
PASS dart_balance:studio_widgets.dart:(
PASS dart_balance:studio_widgets.dart:[
PASS dart_balance:studio_widgets.dart:{
PASS dart_balance:team_page.dart:(
PASS dart_balance:team_page.dart:[
PASS dart_balance:team_page.dart:{
PASS dart_balance:platform_shell.dart:(
PASS dart_balance:platform_shell.dart:[
PASS dart_balance:platform_shell.dart:{
PASS dart_balance:knowledge_graph_studio_page.dart:(
PASS dart_balance:knowledge_graph_studio_page.dart:[
PASS dart_balance:knowledge_graph_studio_page.dart:{
PASS no_core_stubs
RESULT 69/70 PASS
FAILED: api_version_0_12_1
```

## Audit structurel — scripts\audit_lot12_ingestion.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot12_ingestion.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
PASS studio_ocr_quality
PASS studio_preview
PASS studio_role_aware
PASS api_client_idempotency
PASS tests_ingestion_present
PASS docs_architecture
PASS docs_runbook
PASS docs_acceptance
PASS docs_machine_cert
PASS dart_balance:ingestion_page.dart:(
PASS dart_balance:ingestion_page.dart:[
PASS dart_balance:ingestion_page.dart:{
PASS dart_balance:editorial_api.dart:(
PASS dart_balance:editorial_api.dart:[
PASS dart_balance:editorial_api.dart:{
PASS dart_balance:editorial_shell.dart:(
PASS dart_balance:editorial_shell.dart:[
PASS dart_balance:editorial_shell.dart:{
PASS no_lot12_core_stubs
PASS migration_0010_manifest_integrity
PASS manifest_snapshot_persisted
PASS manifest_verify_api
PASS bulk_dead_letter_retry
RESULT 61/64 PASS
FAILED: api_version_0_13_1, mobile_version_0_13_1, admin_version_0_13_1
```

## Audit structurel — scripts\audit_lot13_final.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot13_final.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
FAIL api 0.14.1
FAIL admin 0.14.1+21
FAIL mobile 0.14.1+21
PASS quality module
PASS quote grounding
PASS hash integrity
PASS numeric grounding
PASS duplicate guard
PASS review package
PASS publication blocked
PASS cancel endpoint
FAIL source compare UI
PASS final acceptance
PASS no TODO core
10/14 PASS
```

## Audit structurel — scripts\audit_lot13_uiux_premium.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot13_uiux_premium.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
FAIL admin 0.14.2+22
FAIL mobile 0.14.2+22
FAIL api 0.14.2
PASS kpi responsive
PASS search
PASS state filters
PASS quality sorting
PASS master detail
PASS mobile review sheet
PASS review tabs
PASS source evidence
PASS asset filtering
PASS loading state
PASS empty state
PASS no results state
PASS error retry
PASS human governance
PASS no auto publish
PASS accessibility semantics
PASS selectable evidence
PASS pull refresh
PASS doc
PASS acceptance
20/23 PASS
```

## Audit structurel — scripts\audit_lot14_final.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot14_final.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
FAIL api 0.15.1
FAIL admin 0.15.1+24
FAIL mobile 0.15.1+24
PASS migration 0013
PASS rollout DB check
PASS due scheduler index
PASS publish re-preflight
PASS placement contract
PASS audience contract
PASS schedule contract
PASS snapshot verify service
PASS snapshot verify route
PASS ui search
PASS ui master detail
PASS ui mobile sheet
PASS ui integrity
PASS ui empty state
PASS ui error state
PASS branding
PASS ADR 016
PASS final doc
PASS publication tests
19/22 PASS
```

## Audit structurel — scripts\audit_lot15_final.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot15_final.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
FAIL api 0.16.1
FAIL mobile 0.16.1+26
FAIL admin 0.16.1+26
PASS migration 0015
PASS exam plans
PASS error review
PASS recommendations
PASS constraints
FAIL exam UI
PASS mastery UI
PASS machine gate
7/11 PASS
```

## Audit structurel — scripts\audit_lot15_learning_experience.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot15_learning_experience.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
FAIL api_0_16
PASS migration_0014
PASS hex_domain
PASS hex_service
PASS hex_repo
PASS api_router
PASS study_modes
PASS mastery_semantics
PASS spaced_repetition
PASS error_bank
PASS one_open_session
PASS optimistic_lock
PASS home_resume
PASS workspace_ui
FAIL responsive_ui
FAIL focus_mode
FAIL offline_affordance
FAIL mobile_version
PASS tests
14/19 PASS
```

## Audit structurel — scripts\audit_lot15_student_delight.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot15_student_delight.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
PASS mobile adaptive navigation
PASS desktop three-zone workspace
PASS focus mode
PASS mastery journey
PASS flashcard delight
PASS quiz progressive CTA
PASS exam mode
PASS micro-interaction
PASS offline affordance
PASS accessibility semantics
PASS home greeting
PASS home daily goal
PASS home deadline hero
PASS onboarding academic personalization
PASS optional university
FAIL version mobile
FAIL version admin
FAIL api version
PASS student delight documentation

16/19 PASS
```

## Audit structurel — scripts\audit_lot16_adaptive.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot16_adaptive.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
Traceback (most recent call last):
  File "C:\Users\cs-ap\dev\edusync-web\edunova\scripts\audit_lot16_adaptive.py", line 4, in <module>
    assert '0.17.0' in (p/'services/api/app/main.py').read_text();assert 'adaptive-learning' in (p/'services/api/app/main.py').read_text();print('LOT16 AUDIT: 10/10 PASS')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

## Audit structurel — scripts\audit_lot16_final.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot16_final.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
FAIL v0.17.1 API
PASS adaptive v2
PASS confidence band
PASS knowledge gaps
PASS exam readiness
PASS exam focus
PASS evidence
PASS history endpoint
PASS history repo
PASS migration 0017
FAIL mobile 0.17.1
FAIL admin 0.17.1
PASS premium metrics
PASS exam UI
PASS gaps UI
PASS explainability UI
PASS Volcano Tech
PASS final tests
PASS final docs
PASS no mastery certainty
17/20 PASS
```

## Audit structurel — scripts\audit_lot17_planner.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot17_planner.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
FAIL api_0_18
PASS router
PASS bounded_context
PASS migration_0018
PASS preferences
PASS busy_blocks
PASS capacity_guard
PASS overflow
PASS priority
PASS optimistic_lock
PASS replan
PASS weekend
PASS ui_route
PASS ui_day_week
PASS ui_explain
PASS ui_offline
PASS ui_non_punitive
PASS brand
PASS lot17_tests
18/19 PASS
```

## Audit structurel — scripts\audit_lot21_tutor.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot21_tutor.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
Traceback (most recent call last):
  File "C:\Users\cs-ap\dev\edusync-web\edunova\scripts\audit_lot21_tutor.py", line 17, in <module>
    main=(R/'services/api/app/main.py').read_text();assert '0.22.0' in main and '/v1/tutor' in main
                                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

## Audit structurel — scripts\audit_lot22.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot22.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
PASS campus_domain services\api\app\modules\campus\domain\model.py
PASS campus_service services\api\app\modules\campus\application\service.py
PASS campus_repository services\api\app\modules\campus\infrastructure\sqlalchemy_repo.py
PASS campus_api services\api\app\modules\campus\api\router.py
PASS migration_0031 services\api\migrations\0031_campus_core_v0_23_0.sql
PASS adr_031 docs\ADR-031-campus-multitenancy-boundary.md
PASS lot22_doc docs\LOT22_CAMPUS_CORE_v0.23.0.md
PASS campus_ui apps\mobile\lib\src\features\campus\presentation\campus_page.dart
PASS tests services\api\tests\test_campus_lot22.py
FAIL version_0_23_0
PASS campus_router
PASS runtime_wiring
PASS tenant_columns
PASS brand_signature
```

## Audit structurel — scripts\audit_lot22_deep.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot22_deep.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
PASS service scope guard
PASS role escalation guard
PASS institution write gate
PASS period hierarchy
PASS role endpoint
PASS scoped listing
PASS hardening migration
PASS fk defense
PASS check defense
PASS hardening tests
PASS adr 032
PASS lot22 hardening doc
FAIL api version
FAIL mobile version
FAIL admin version
12/15 PASS
```

## Audit structurel — scripts\audit_lot26.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot26.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
Traceback (most recent call last):
  File "C:\Users\cs-ap\dev\edusync-web\edunova\scripts\audit_lot26.py", line 16, in <module>
    assert '0.27.0' in main and 'campus_operations_router' in main
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

## Audit structurel — scripts\audit_lot26_closure.py

Commande : `.venv/Scripts/python.exe -X utf8 scripts\audit_lot26_closure.py` ; sortie 1.

Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.

```text
PASS migration_0044
PASS adr_044
PASS announcements
PASS absence_workflow
PASS calendar
PASS operations_dashboard
PASS auto_absent
PASS notifications
PASS api_routes
FAIL version_api
FAIL version_mobile
FAIL version_admin
```

## Tentative non réussie — admin-analyze-previous-1793435236217334100

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Résolution des paquets non terminée au moment de cette première analyse : imports en cascade indisponibles. Terminer pub get et la génération Drift, puis réanalyser avant de conclure sur le code.

Trace intégrale : [admin-analyze-previous-1793435236217334100.log](admin-analyze-previous-1793435236217334100.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Analyzing admin...                                              

warning - The include file 'package:flutter_lints/flutter.yaml' in 'C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\analysis_options.yaml' can't be found when analyzing 'C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin' - analysis_options.yaml:1:10 - include_file_not_found
  error - Target of URI doesn't exist: 'package:flutter/material.dart' - lib\main.dart:1:8 - uri_does_not_exist
  error - The function 'runApp' isn't defined - lib\main.dart:3:14 - undefined_function
  error - Target of URI doesn't exist: 'package:flutter/material.dart' - lib\src\app\admin_app.dart:1:8 - uri_does_not_exist
  error - Classes can only extend other classes - lib\src\app\admin_app.dart:8:31 - extends_non_class
  error - No associated named super constructor parameter - lib\src\app\admin_app.dart:8:77 - super_formal
[extrait ; trace intégrale dans le journal]
shell.dart:208:903 - undefined_identifier
  error - The method 'Text' isn't defined for the type '_PlatformShellState' - lib\src\features\platform\platform_shell.dart:208:930 - undefined_method
  error - The method 'IconButton' isn't defined for the type '_PlatformShellState' - lib\src\features\platform\platform_shell.dart:208:963 - undefined_method
  error - The name 'Icon' isn't a class - lib\src\features\platform\platform_shell.dart:208:1015 - creation_with_non_type
  error - Undefined name 'Icons' - lib\src\features\platform\platform_shell.dart:208:1020 - undefined_identifier
  error - The name 'SizedBox' isn't a class - lib\src\features\platform\platform_shell.dart:209:13 - creation_with_non_type
  error - The method 'Card' isn't defined for the type '_PlatformShellState' - lib\src\features\platform\platform_shell.dart:209:33 - undefined_method
  error - The method 'Padding' isn't defined for the type '_PlatformShellState' - lib\src\features\platform\platform_shell.dart:209:44 - undefined_method
  error - The name 'all' isn't a class - lib\src\features\platform\platform_shell.dart:209:66 - creation_with_non_type
  error - The method 'Row' isn't defined for the type '_PlatformShellState' - lib\src\features\platform\platform_shell.dart:209:91 - undefined_method
  error - The name 'Icon' isn't a class - lib\src\features\platform\platform_shell.dart:209:111 - creation_with_non_type
  error - Undefined name 'Icons' - lib\src\features\platform\platform_shell.dart:209:116 - undefined_identifier
  error - The name 'SizedBox' isn't a class - lib\src\features\platform\platform_shell.dart:209:152 - creation_with_non_type
  error - The method 'Expanded' isn't defined for the type '_PlatformShellState' - lib\src\features\platform\platform_shell.dart:209:171 - undefined_method
  error - The method 'Text' isn't defined for the type '_PlatformShellState' - lib\src\features\platform\platform_shell.dart:209:186 - undefined_method
  error - Target of URI doesn't exist: 'package:flutter_test/flutter_test.dart' - test\smoke_test.dart:1:8 - uri_does_not_exist
  error - Target of URI doesn't exist: 'package:edunova_admin/src/app/admin_app.dart' - test\smoke_test.dart:2:8 - uri_does_not_exist
  error - The function 'testWidgets' isn't defined - test\smoke_test.dart:3:13 - undefined_function
  error - The name 'EduNovaAdminApp' isn't a class - test\smoke_test.dart:3:107 - creation_with_non_type
  error - The function 'expect' isn't defined - test\smoke_test.dart:3:126 - undefined_function
  error - Undefined name 'find' - test\smoke_test.dart:3:133 - undefined_identifier
  error - Undefined name 'findsOneWidget' - test\smoke_test.dart:3:161 - undefined_identifier
  error - The function 'expect' isn't defined - test\smoke_test.dart:3:177 - undefined_function
  error - Undefined name 'find' - test\smoke_test.dart:3:184 - undefined_identifier
  error - Undefined name 'findsOneWidget' - test\smoke_test.dart:3:214 - undefined_identifier

3322 issues found. (ran in 9.8s)

```

## Tentative non réussie — admin-analyze-previous-1793436605821027600

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.

Trace intégrale : [admin-analyze-previous-1793436605821027600.log](admin-analyze-previous-1793436605821027600.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Analyzing admin...                                              

warning - Unnecessary cast - lib\src\features\editorial\content_detail_page.dart:9:130 - unnecessary_cast
  error - Expected to find ')' - lib\src\features\editorial\content_detail_page.dart:34:723 - expected_token
  error - Expected to find ';' - lib\src\features\editorial\content_detail_page.dart:34:726 - expected_token
  error - Expected to find ']' - lib\src\features\editorial\content_detail_page.dart:34:726 - expected_token
warning - Dead code - lib\src\features\editorial\content_detail_page.dart:34:727 - dead_code
  error - Expected an identifier - lib\src\features\editorial\content_detail_page.dart:34:727 - missing_identifier
  error - Unexpected text ';' - lib\src\features\editorial\content_detail_page.dart:34:727 - unexpected_token
  error - Expected to find ';' - lib\src\features\editorial
[extrait ; trace intégrale dans le journal]
use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_list_page.dart:54:1702 - deprecated_member_use
   info - Don't use 'BuildContext's across async gaps - lib\src\features\editorial\ingestion_page.dart:211:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\editorial\ingestion_page.dart:263:251 - use_build_context_synchronously
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:300:29 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:301:58 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:301:421 - deprecated_member_use
warning - Unnecessary cast - lib\src\features\editorial\publication_center_page.dart:14:310 - unnecessary_cast
warning - Unnecessary cast - lib\src\features\editorial\publication_center_page.dart:14:348 - unnecessary_cast
   info - The variable name '_K' isn't a lowerCamelCase identifier - lib\src\features\editorial\publication_center_page.dart:26:10 - non_constant_identifier_names
  error - Conditions must have a static type of 'bool' - lib\src\features\editorial\publication_center_page.dart:28:312 - non_bool_condition
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\question_factory_page.dart:4:1292 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\team_page.dart:12:686 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\platform\platform_shell.dart:59:41 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\platform\platform_shell.dart:94:41 - deprecated_member_use

42 issues found. (ran in 10.4s)

```

## Tentative non réussie — admin-analyze-previous-1793475138899995300

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.

Trace intégrale : [admin-analyze-previous-1793475138899995300.log](admin-analyze-previous-1793475138899995300.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Analyzing admin...                                              

warning - Unnecessary cast - lib\src\features\editorial\content_detail_page.dart:9:130 - unnecessary_cast
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_detail_page.dart:74:614 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_detail_page.dart:74:965 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v
[extrait ; trace intégrale dans le journal]
 form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_list_page.dart:54:853 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_list_page.dart:54:1702 - deprecated_member_use
   info - Don't use 'BuildContext's across async gaps - lib\src\features\editorial\ingestion_page.dart:211:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\editorial\ingestion_page.dart:263:251 - use_build_context_synchronously
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:300:29 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:301:58 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:301:421 - deprecated_member_use
warning - Unnecessary cast - lib\src\features\editorial\publication_center_page.dart:14:310 - unnecessary_cast
warning - Unnecessary cast - lib\src\features\editorial\publication_center_page.dart:14:348 - unnecessary_cast
   info - The variable name '_K' isn't a lowerCamelCase identifier - lib\src\features\editorial\publication_center_page.dart:26:10 - non_constant_identifier_names
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\question_factory_page.dart:4:1292 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\team_page.dart:12:686 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\platform\platform_shell.dart:59:41 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\platform\platform_shell.dart:94:41 - deprecated_member_use

25 issues found. (ran in 9.1s)

```

## Tentative non réussie — admin-analyze-previous-1793475521116471300

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.

Trace intégrale : [admin-analyze-previous-1793475521116471300.log](admin-analyze-previous-1793475521116471300.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Analyzing admin...                                              

warning - Unnecessary cast - lib\src\features\editorial\content_detail_page.dart:9:130 - unnecessary_cast
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_detail_page.dart:74:614 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_detail_page.dart:74:965 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v
[extrait ; trace intégrale dans le journal]
form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_list_page.dart:54:853 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_list_page.dart:54:1702 - deprecated_member_use
   info - Don't use 'BuildContext's across async gaps - lib\src\features\editorial\ingestion_page.dart:211:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\editorial\ingestion_page.dart:263:251 - use_build_context_synchronously
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:300:29 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:301:58 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:301:421 - deprecated_member_use
warning - Unnecessary cast - lib\src\features\editorial\publication_center_page.dart:14:310 - unnecessary_cast
warning - Unnecessary cast - lib\src\features\editorial\publication_center_page.dart:14:348 - unnecessary_cast
   info - The variable name '_K' isn't a lowerCamelCase identifier - lib\src\features\editorial\publication_center_page.dart:26:10 - non_constant_identifier_names
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\question_factory_page.dart:4:1292 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\team_page.dart:12:686 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\platform\platform_shell.dart:59:41 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\platform\platform_shell.dart:94:41 - deprecated_member_use

25 issues found. (ran in 10.3s)

```

## Tentative non réussie — admin-analyze

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.

Trace intégrale : [admin-analyze.log](admin-analyze.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Analyzing admin...                                              

warning - Unnecessary cast - lib\src\features\editorial\content_detail_page.dart:9:130 - unnecessary_cast
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_detail_page.dart:74:614 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_detail_page.dart:74:965 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v
[extrait ; trace intégrale dans le journal]
 form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_list_page.dart:54:853 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\content_list_page.dart:54:1702 - deprecated_member_use
   info - Don't use 'BuildContext's across async gaps - lib\src\features\editorial\ingestion_page.dart:211:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\editorial\ingestion_page.dart:263:251 - use_build_context_synchronously
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:300:29 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:301:58 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\ingestion_page.dart:301:421 - deprecated_member_use
warning - Unnecessary cast - lib\src\features\editorial\publication_center_page.dart:14:310 - unnecessary_cast
warning - Unnecessary cast - lib\src\features\editorial\publication_center_page.dart:14:348 - unnecessary_cast
   info - The variable name '_K' isn't a lowerCamelCase identifier - lib\src\features\editorial\publication_center_page.dart:26:10 - non_constant_identifier_names
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\question_factory_page.dart:4:1292 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\editorial\team_page.dart:12:686 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\platform\platform_shell.dart:59:41 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\platform\platform_shell.dart:94:41 - deprecated_member_use

25 issues found. (ran in 7.7s)

```

## Tentative non réussie — admin-android-previous-1793438019670976300

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Build Android non certifié pour cette tentative. Examiner le téléchargement SDK/NDK, les erreurs Google Maven et le daemon Gradle ; reprendre séquentiellement après vérification réseau et avec une mémoire compatible avec les 6 Go de la machine. Aucun APK ne doit être déclaré valide sans sortie zéro et artefact vérifié.

Trace intégrale : [admin-android-previous-1793438019670976300.log](admin-android-previous-1793438019670976300.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
[!] Your app is using an unsupported Gradle project. To fix this problem, create a new project by running `flutter create -t app <app-directory>` and then move the dart code, assets and pubspec.yaml to the new project.

```

## Tentative non réussie — admin-android-previous-1793469645008674400

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 124.

Build Android non certifié pour cette tentative. Examiner le téléchargement SDK/NDK, les erreurs Google Maven et le daemon Gradle ; reprendre séquentiellement après vérification réseau et avec une mémoire compatible avec les 6 Go de la machine. Aucun APK ne doit être déclaré valide sans sortie zéro et artefact vérifié.

Trace intégrale : [admin-android-previous-1793469645008674400.log](admin-android-previous-1793469645008674400.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Running Gradle task 'assembleDebug'...                          

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>if "Windows_NT" == "Windows_NT" setlocal

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>set DEFAULT_JVM_OPTS= 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>set DIRNAME=C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android\ 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>if "C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android\" == "" set DIRNAME=. 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>set APP_BASE_NAME=gradlew 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>set APP_HOME=C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android\ 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>if defined JAVA_HOME goto findJavaFromJavaHome 

C:\Users\cs-ap\dev
[extrait ; trace intégrale dans le journal]
37)
				... 45 more

exception: warning: ATTENTION!
exception: this build uses unsafe internal compiler arguments:
exception: 
exception: 
exception: this mode is not recommended for production use,
exception: as no stability/compatibility guarantees are given on
exception: compiler or generated code. Use it at your own risk!
exception: 
exception: c:\Users\cs-ap\dev\flutter\packages\flutter_tools\gradle\src\main\kotlin\DependencyVersionChecker.kt:194:39: warning: 'getter for minSdkVersion: AndroidVersion' is deprecated. Will be removed in v9.0
exception:             MinSdkVersion(it.name, it.minSdkVersion.apiLevel)
exception:                                       ^^^^^^^^^^^^^
exception: c:\Users\cs-ap\dev\flutter\packages\flutter_tools\gradle\src\main\kotlin\FlutterPlugin.kt:11:37: warning: 'ApkVariant' is deprecated. Deprecated in Java
exception: import com.android.build.gradle.api.ApkVariant
exception:                                     ^^^^^^^^^^
exception: c:\Users\cs-ap\dev\flutter\packages\flutter_tools\gradle\src\main\kotlin\FlutterPlugin.kt:628:69: warning: 'ApkVariant' is deprecated. Deprecated in Java
exception:                     val versionCodeIfPresent: Int? = if (variant is ApkVariant) variant.versionCode else null
exception:                                                                     ^^^^^^^^^^
Checking the license for package NDK (Side by side) 27.0.12077973 in C:\Users\cs-ap\dev\Android\Sdk\licenses
License for package NDK (Side by side) 27.0.12077973 accepted.
Preparing "Install NDK (Side by side) 27.0.12077973 v.27.0.12077973".

TIMEOUT after 4500 seconds
Warning: Failed to download package!
"Install NDK (Side by side) 27.0.12077973 v.27.0.12077973" failed.

FAILURE: Build failed with an exception.

* Where:
Build file 'C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android\build.gradle.kts' line: 19

* What went wrong:
A problem occurred configuring project ':app'.
> com.android.builder.sdk.InstallFailedException: Failed to install the following SDK components:
      ndk;27.0.12077973 NDK (Side by side) 27.0.12077973
  Install the missing components using the SDK manager in Android Studio.


* Try:
> Run with --stacktrace option to get the stack trace.
> Run with --info or --debug option to get more log output.
> Run with --scan to get full insights.
> Get more help at https://help.gradle.org.

BUILD FAILED in 1h 37m 38s

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>if "1" == "0" goto mainEnd 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>rem Set variable GRADLE_EXIT_CONSOLE if you need the _script_ return code instead of 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>rem the _cmd.exe /c_ return code! 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>if not "" == "" exit 1 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\android>exit /b 1 
Running Gradle task 'assembleDebug'...                           5870.0s
Gradle task assembleDebug failed with exit code 1

```

## Tentative non réussie — admin-test-previous-1793435255169109700

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.

Trace intégrale : [admin-test-previous-1793435255169109700.log](admin-test-previous-1793435255169109700.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Error: cannot run without a dependency on either "package:flutter_test" or "package:test". Ensure the following lines are present in your pubspec.yaml:

dev_dependencies:
  flutter_test:
    sdk: flutter


```

## Tentative non réussie — admin-test-previous-1793436624137805600

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.

Trace intégrale : [admin-test-previous-1793436624137805600.log](admin-test-previous-1793436624137805600.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart
lib/src/features/editorial/content_detail_page.dart:34:505: Error: Can't find ')' to match '('.
class _ReviewTab extends StatelessWidget{final Map<String,dynamic> data;const _ReviewTab({required this.data});@override Widget build(BuildContext c){final rows=data['reviews'] as List<dynamic>;final assignments=data['assignments'] as List<dynamic>;return ListView(padding:const EdgeInsets.all(24),children:[StudioSection(title:'Affectations',child:assignments.isEmpty?const Text('Aucune affectation explicite.'):Column(children:[for(final a in assignments.where((x)=>(x as Map)['active']==true))ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.assignment_ind_outlined),title:Text('${a['stage']} • ${a['assignee_id']}'),subtitle:Text(a['due_at']==null?'Sans 
[extrait ; trace intégrale dans le journal]
                                                                           ^
  lib/src/features/editorial/content_detail_page.dart:34:1393: Error: Unexpected token ';'.
  class _ReviewTab extends StatelessWidget{final Map<String,dynamic> data;const _ReviewTab({required this.data});@override Widget build(BuildContext c){final rows=data['reviews'] as List<dynamic>;final assignments=data['assignments'] as List<dynamic>;return ListView(padding:const EdgeInsets.all(24),children:[StudioSection(title:'Affectations',child:assignments.isEmpty?const Text('Aucune affectation explicite.'):Column(children:[for(final a in assignments.where((x)=>(x as Map)['active']==true))ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.assignment_ind_outlined),title:Text('${a['stage']} • ${a['assignee_id']}'),subtitle:Text(a['due_at']==null?'Sans échéance':'Échéance ${formatDate(a['due_at'])}')]))),const SizedBox(height:14),StudioSection(title:'Décisions de revue',child:rows.isEmpty?const Text('Aucune décision enregistrée.'):Column(children:[for(final r in rows.reversed)ListTile(contentPadding:EdgeInsets.zero,leading:Icon(r['decision']=='approved'?Icons.check_circle:Icons.change_circle,color:r['decision']=='approved'?Colors.green:Colors.orange),title:Text('${r['decision']=='approved'?'Approuvé':'Corrections demandées'} • ${r['reviewer_id']}'),subtitle:Text('${r['comment']?.toString().isEmpty==false?r['comment']:'Sans commentaire'}\n${formatDate(r['created_at'])}${r['quality_score']!=null?' • qualité ${r['quality_score']} %':''}'),isThreeLine:true)]))]);}}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  ^
  .
00:00 +0 -1: Some tests failed.

```

## Tentative non réussie — admin-test-previous-1793439552265020100

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.

Trace intégrale : [admin-test-previous-1793439552265020100.log](admin-test-previous-1793439552265020100.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart
00:00 +0: EduNova Studio affiche la connexion
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: exactly one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "EduNova Studio": []>
   Which: means none were found but one was expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart:3:126)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/admin/test/smoke_test.dart line 3
The test description was:
  EduNova Studio affiche la connexion
════════════════════════════════════════════════════════════════════════════════════════════════════
00:02 +0 -1: EduNova Studio affiche la connexion [E]
  Test failed. See exception logs above.
  The test description was: EduNova Studio affiche la connexion
  
00:02 +0 -1: Some tests failed.

```

## Tentative non réussie — admin-web-previous-1793435283928388700

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Consulter les cas individuels et les corrections décrites dans le rapport ; les suites et audits historiques restent distincts.

Trace intégrale : [admin-web-previous-1793435283928388700.log](admin-web-previous-1793435283928388700.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
This project is not configured for the web.
To configure this project for the web, run flutter create . --platforms web

```

## Tentative non réussie — admin-web-previous-1793436664276622500

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Consulter les cas individuels et les corrections décrites dans le rapport ; les suites et audits historiques restent distincts.

Trace intégrale : [admin-web-previous-1793436664276622500.log](admin-web-previous-1793436664276622500.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Compiling lib\main.dart for the Web...                          
Wasm dry run findings:
Found incompatibilities with WebAssembly.

package:flutter_secure_storage_web/flutter_secure_storage_web.dart 5:1 - dart:html unsupported (0)
package:flutter_secure_storage_web/src/subtle.dart 21:1 - dart:html unsupported (0)
package:js/js.dart 10:1 - dart:js unsupported (1)
package:flutter_secure_storage_web/flutter_secure_storage_web.dart 6:1 - JS interop library 'dart:js_util' can't be imported when compiling to Wasm. (2)
package:flutter_secure_storage_web/src/subtle.dart 22:1 - JS interop library 'dart:js_util' can't be imported when compiling to Wasm. (2)
package:flutter_secure_storage_web/src/subtle.dart 26:1 - JS interop library 'package:js/js.dart' can't be imported when compiling to Wasm. (2)

Consider addressing these issues to enable wasm builds. See docs
[extrait ; trace intégrale dans le journal]
R_WEB_USE_SKWASM=false -DFLUTTER_WEB_CANVASKIT_URL=https://www.gstatic.com/flutter-canvaskit/c29809135135e262a912cf583b2c90deb9ded610/ --native-null-assertions --no-source-maps -O4 --minify -o C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\.dart_tool\flutter_build\56142b121af0d4092618f2c27ea7dee4\app.dill --packages=C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\.dart_tool\package_config.json --cfe-only C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\.dart_tool\flutter_build\56142b121af0d4092618f2c27ea7dee4\main.dart
#0      RunResult.throwException (package:flutter_tools/src/base/process.dart:118:5)
#1      _DefaultProcessUtils.run (package:flutter_tools/src/base/process.dart:344:19)
<asynchronous suspension>
#2      Dart2JSTarget.build (package:flutter_tools/src/build_system/targets/web.dart:204:5)
<asynchronous suspension>
#3      _BuildInstance._invokeInternal (package:flutter_tools/src/build_system/build_system.dart:873:9)
<asynchronous suspension>
#4      Future.wait.<anonymous closure> (dart:async/future.dart:525:21)
<asynchronous suspension>
#5      _BuildInstance.invokeTarget (package:flutter_tools/src/build_system/build_system.dart:811:32)
<asynchronous suspension>
#6      Future.wait.<anonymous closure> (dart:async/future.dart:525:21)
<asynchronous suspension>
#7      _BuildInstance.invokeTarget (package:flutter_tools/src/build_system/build_system.dart:811:32)
<asynchronous suspension>
#8      FlutterBuildSystem.build (package:flutter_tools/src/build_system/build_system.dart:631:16)
<asynchronous suspension>
#9      WebBuilder.buildWeb (package:flutter_tools/src/web/compile.dart:90:34)
<asynchronous suspension>
#10     BuildWebCommand.runCommand (package:flutter_tools/src/commands/build_web.dart:282:5)
<asynchronous suspension>
#11     FlutterCommand.run.<anonymous closure> (package:flutter_tools/src/runner/flutter_command.dart:1581:27)
<asynchronous suspension>
#12     AppContext.run.<anonymous closure> (package:flutter_tools/src/base/context.dart:154:19)
<asynchronous suspension>
#13     CommandRunner.runCommand (package:args/command_runner.dart:212:13)
<asynchronous suspension>
#14     FlutterCommandRunner.runCommand.<anonymous closure> (package:flutter_tools/src/runner/flutter_command_runner.dart:503:9)
<asynchronous suspension>
#15     AppContext.run.<anonymous closure> (package:flutter_tools/src/base/context.dart:154:19)
<asynchronous suspension>
#16     FlutterCommandRunner.runCommand (package:flutter_tools/src/runner/flutter_command_runner.dart:438:5)
<asynchronous suspension>
#17     run.<anonymous closure>.<anonymous closure> (package:flutter_tools/runner.dart:98:11)
<asynchronous suspension>
#18     AppContext.run.<anonymous closure> (package:flutter_tools/src/base/context.dart:154:19)
<asynchronous suspension>
#19     main (package:flutter_tools/executable.dart:101:3)
<asynchronous suspension>

Compiling lib\main.dart for the Web...                             19.4s
Error: Failed to compile application for the Web.

```

## Tentative non réussie — admin-windows-previous-1793435306605963700

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Vérifier successivement le support des symlinks, NuGet, ATL et le préfixe CMake. Ces prérequis/caches ont été corrigés au fil des reprises. Un exécutable intermédiaire ne prouve pas que le bundle INSTALL a réussi.

Trace intégrale : [admin-windows-previous-1793435306605963700.log](admin-windows-previous-1793435306605963700.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Building Windows application...                                 
CMake Error at CMakeLists.txt:58 (include):
  include could not find requested file:

    flutter/generated_plugins.cmake


Building Windows application...                                   109.0s
Unable to generate build files

```

## Tentative non réussie — admin-windows-previous-1793436802158588200

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Vérifier successivement le support des symlinks, NuGet, ATL et le préfixe CMake. Ces prérequis/caches ont été corrigés au fil des reprises. Un exécutable intermédiaire ne prouve pas que le bundle INSTALL a réussi.

Trace intégrale : [admin-windows-previous-1793436802158588200.log](admin-windows-previous-1793436802158588200.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Building Windows application...                                 
lib/src/features/editorial/content_detail_page.dart(34,505): error G297C951C: Can't find ')' to match '('. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,308): error G297C951C: Can't find ']' to match '['. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/publication_center_page.dart(28,312): error G44692867: A value of type 'Map<String, dynamic>?' can't be assigned to a variable of type 'bool'. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,726): error G67247B7E: Expected ';' after this. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,727): error G25387D61: Expected an identifier, but got ','. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,727): error G5BADBE1C: Unexpected token ';'. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,752): error G67247B7E: Expected ';' after this. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,753): error G25387D61: Expected an identifier, but got ','. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,753): error G5BADBE1C: Unexpected token ';'. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,1391): error G67247B7E: Expected ';' after this. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,1392): error G25387D61: Expected an identifier, but got ']'. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,1392): error G5BADBE1C: Unexpected token ';'. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,1393): error G25387D61: Expected an identifier, but got ')'. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,1392): error G67247B7E: Expected ';' after this. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
lib/src/features/editorial/content_detail_page.dart(34,1393): error G5BADBE1C: Unexpected token ';'. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(254,5): error MSB8066: Custom build for 'C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\CMakeFiles\9fe8ec03a781cf54e6037c6fc3669e86\flutter_windows.dll.rule;C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\CMakeFiles\359d7a32ba6bbe985d6e015ba9bb7325\flutter_assemble.rule;C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\windows\flutter\CMakeLists.txt' exited with code 1. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\flutter\flutter_assemble.vcxproj]
Building Windows application...                                    39.2s
Build process failed.

```

## Tentative non réussie — admin-windows-previous-1793466765350143500

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin`. Code 1.

Vérifier successivement le support des symlinks, NuGet, ATL et le préfixe CMake. Ces prérequis/caches ont été corrigés au fil des reprises. Un exécutable intermédiaire ne prouve pas que le bundle INSTALL a réussi.

Trace intégrale : [admin-windows-previous-1793466765350143500.log](admin-windows-previous-1793466765350143500.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin
Building Windows application...                                 
C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\windows\flutter\ephemeral\.plugin_symlinks\flutter_secure_storage_windows\windows\flutter_secure_storage_windows_plugin.cpp(6,10): error C1083: Cannot open include file: 'atlstr.h': No such file or directory [C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin\build\windows\x64\plugins\flutter_secure_storage_windows\flutter_secure_storage_windows_plugin.vcxproj]
Building Windows application...                                   151.9s
Build process failed.

```

## Tentative non réussie — audits

Commande : `C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe C:\Users\cs-ap\dev\edusync-web\edunova\scripts\certify_phase19_audits.py` dans `C:\Users\cs-ap\dev\edusync-web\edunova`. Code 1.

Consulter les cas individuels et les corrections décrites dans le rapport ; les suites et audits historiques restent distincts.

Trace intégrale : [audits.log](audits.log).

```text
COMMAND: C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe C:\Users\cs-ap\dev\edusync-web\edunova\scripts\certify_phase19_audits.py
CWD: C:\Users\cs-ap\dev\edusync-web\edunova
audit_campus_intelligence_flutter.py 0
audit_lot10_analytics.py 0
audit_lot10_uiux_maximal.py 1
audit_lot11_editorial.py 0
audit_lot11_maximal.py 1
audit_lot12_ingestion.py 1
audit_lot13_content_factory.py 0
audit_lot13_final.py 1
audit_lot13_uiux_premium.py 1
audit_lot14_final.py 1
audit_lot14_publication.py 0
audit_lot15_final.py 1
audit_lot15_learning_experience.py 1
audit_lot15_student_delight.py 1
audit_lot16_adaptive.py 1
audit_lot16_final.py 1
audit_lot17_planner.py 1
audit_lot18_assessment.py 0
audit_lot18_cognitive_intelligence.py 0
audit_lot18_question_factory.py 0
audit_lot19_remediation.py 0
audit_lot19_tutor.py 0
audit_lot19_v0202.py 0
audit_lot20_knowledge_graph.py 0
audit_lot20_knowledge_graph_v0211.py 0
audit_lot20_knowledge_graph_v0212.py 0
audit_lot21_tutor.py 1
audit_lot22.py 1
audit_lot22_deep.py 1
audit_lot23.py 0
audit_lot23_maximal.py 0
audit_lot24.py 0
audit_lot24_closure.py 0
audit_lot25.py 0
audit_lot25_closure.py 0
audit_lot25_maximal.py 0
audit_lot26.py 1
audit_lot26_closure.py 1
audit_lot26_v0271.py 0
audit_lot26_v0273.py 0
audit_lot27.py 0
audit_lot27_final.py 0
audit_lot27_v0281.py 0
audit_lot28.py 0
audit_lot29.py 0
audit_lot29_final.py 0
audit_lot30.py 0
audit_lot31.py 0
audit_lot32_global.py 0
audit_lot9_ux.py 0
audit_phase16_closure_v0_51_9.py 0
audit_phase16_library_governance_v0_51_2.py 0
audit_phase16_physical_library.py 0
audit_phase16_tenant_policy_v0_51_3.py 0
audit_phase16_v0_51_8.py 0
STRUCTURAL AUDITS: 38 succeeded, 17 failed; not functional tests

```

## Tentative non réussie — backend-final-previous-1793433709429319500

Commande : `C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe -m pytest -q -n 4 --dist loadfile --durations=20 services/api/tests --junitxml=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\local-phase19\backend-final.xml` dans `C:\Users\cs-ap\dev\edusync-web\edunova`. Code 1.

Consulter les cas individuels et les corrections décrites dans le rapport ; les suites et audits historiques restent distincts.

Trace intégrale : [backend-final-previous-1793433709429319500.log](backend-final-previous-1793433709429319500.log).

```text
COMMAND: C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe -m pytest -q -n 4 --dist loadfile --durations=20 services/api/tests --junitxml=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\local-phase19\backend-final.xml
CWD: C:\Users\cs-ap\dev\edusync-web\edunova
bringing up nodes...
bringing up nodes...

........................................................................ [  5%]
........................................................................ [ 11%]
........................................................................ [ 17%]
........................................................................ [ 23%]
........................................................................ [ 29%]
........................................................................ [ 35%]
........................................................................ [ 41%]
........................................................................ [ 47%]
....................F...............F...F
[extrait ; trace intégrale dans le journal]
nciliation.py::test_v2_tampering_fails_closed_without_old_grade_fallback[<lambda>4]
3084.63s setup    services/api/tests/test_phase14_pedagogical_intelligence.py::test_course_sql_rejects_duplicate_and_invalid_grade_rows
3084.40s setup    services/api/tests/test_phase14_score_reconciliation.py::test_historical_partial_scores_kept_but_never_claimed_verified
3078.68s setup    services/api/tests/test_phase13_student_success.py::test_tenant_student_privacy_and_permissions
1925.93s setup    services/api/tests/test_phase14_score_reconciliation.py::test_v2_tampering_fails_closed_without_old_grade_fallback[<lambda>3]
1900.26s setup    services/api/tests/editorial/test_editorial_service.py::test_internal_only_cannot_be_published
1243.84s setup    services/api/tests/editorial/test_editorial_service.py::test_dashboard_counts_workflow
144.23s setup    services/api/tests/test_phase13_student_success.py::test_action_plan_guards_duplicates_dates_and_closed_cases
143.36s setup    services/api/tests/test_phase14_score_reconciliation.py::test_failed_grade_integrity_is_atomic_no_orphan_or_graded_attempt
=========================== short test summary info ===========================
FAILED services/api/tests/ingestion/test_ingestion_api.py::test_batch_upload_idempotency_freeze_worker_and_editorial_projection
FAILED services/api/tests/ingestion/test_ingestion_api.py::test_global_dedup_reuses_already_processed_document_without_second_ocr
FAILED services/api/tests/ingestion/test_ingestion_api.py::test_preview_and_global_dashboard_after_processing
FAILED services/api/tests/ingestion/test_ingestion_api.py::test_global_dedup_never_reuses_rights_or_academic_context_silently
FAILED services/api/tests/ingestion/test_ingestion_api.py::test_frozen_manifest_snapshot_is_persisted_and_verifiable
FAILED services/api/tests/content_factory/test_content_factory.py::test_factory_end_to_end_ready_for_review_with_evidence
FAILED services/api/tests/content_factory/test_content_factory.py::test_factory_create_is_idempotent_for_same_source_and_asset_contract
FAILED services/api/tests/content_factory/test_content_factory.py::test_factory_rejects_unknown_asset_family
FAILED services/api/tests/content_factory/test_content_factory.py::test_factory_never_publishes_and_exposes_quality_score
FAILED services/api/tests/content_factory/test_content_factory.py::test_factory_final_quality_gates_include_grounding_integrity
FAILED services/api/tests/content_factory/test_content_factory.py::test_factory_queued_run_can_be_cancelled_and_not_processed
FAILED services/api/tests/content_factory/test_content_factory.py::test_factory_review_package_pairs_every_asset_with_source_evidence_and_blocks_publication
FAILED services/api/tests/document_engine/test_pipeline.py::test_question_candidates_from_interrogation_photo
FAILED services/api/tests/test_student_finance_phase6.py::test_cash_payment_allocates_oldest_charge_and_receipt_is_idempotent
14 failed, 1186 passed, 17 skipped, 24 warnings in 38214.65s (10:36:54)

```

## Tentative non réussie — backend

Commande : `C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe -m pytest -q services/api/tests --junitxml=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\local-phase19\backend.xml` dans `C:\Users\cs-ap\dev\edusync-web\edunova`. Code 124.

Consulter les cas individuels et les corrections décrites dans le rapport ; les suites et audits historiques restent distincts.

Trace intégrale : [backend.log](backend.log).

```text
COMMAND: C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe -m pytest -q services/api/tests --junitxml=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\local-phase19\backend.xml
CWD: C:\Users\cs-ap\dev\edusync-web\edunova
..................................................FFFFFFF.........FF.... [  5%]
.................................F....FF..FF.F.......................... [ 11%]
........................................................................ [ 17%]
........................................................................ [ 23%]
........................................................................ [ 29%]
........................................................................ [ 35%]
........................................................................ [ 41%]
........................................................................ [ 47%]
........................................................................ [ 53%]
..............................................
[extrait ; trace intégrale dans le journal]
23 request request_id=b0a448bbf1ac44259259e9e9b8cc1673 method=POST path=/v1/sync/push status=200 duration_ms=66
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=c3aa579abc504ad394e3a9ce5089c981 method=POST path=/v1/sync/push status=200 duration_ms=72
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=a5bd87cbd14948f88f4e19caa7a263ff method=POST path=/v1/sync/push status=200 duration_ms=96
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=8ca8710033f5445fbfd334a4578e8fd6 method=POST path=/v1/sync/push status=200 duration_ms=82
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=fd3d5902759845ecad32a9541236bcd8 method=POST path=/v1/sync/push status=200 duration_ms=82
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=9b052729afa749bebcbf9bfc7a3fe606 method=POST path=/v1/sync/push status=200 duration_ms=76
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=a284fa6afc6d4ca0a0075681c9330c06 method=POST path=/v1/sync/push status=200 duration_ms=70
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=143d7b218fb3487e949edcc585072b2e method=POST path=/v1/sync/push status=200 duration_ms=83
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=ed295e46a3564265a1d7a3cb7f796611 method=POST path=/v1/sync/push status=200 duration_ms=79
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=894ed65aebac4b2a9fbe06af72a68e58 method=POST path=/v1/sync/push status=200 duration_ms=42
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=ec06317e04384ded86cd7e430b97fee3 method=POST path=/v1/sync/push status=200 duration_ms=63
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 200 OK"
INFO     edunova.http:observability.py:23 request request_id=a4ddac5a5d7f429981846e0dd8710a96 method=POST path=/v1/sync/push status=401 duration_ms=1067
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/v1/sync/push "HTTP/1.1 401 Unauthorized"
TIMEOUT after 4500 seconds

```

## Tentative non réussie — mobile-analyze-previous-1793394408731926200

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Résolution des paquets non terminée au moment de cette première analyse : imports en cascade indisponibles. Terminer pub get et la génération Drift, puis réanalyser avant de conclure sur le code.

Trace intégrale : [mobile-analyze-previous-1793394408731926200.log](mobile-analyze-previous-1793394408731926200.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Analyzing mobile...                                             

warning - The include file 'package:flutter_lints/flutter.yaml' in 'C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\analysis_options.yaml' can't be found when analyzing 'C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile' - analysis_options.yaml:1:10 - include_file_not_found
  error - Target of URI doesn't exist: 'package:flutter/material.dart' - lib\main.dart:1:8 - uri_does_not_exist
  error - Target of URI doesn't exist: 'package:flutter_riverpod/flutter_riverpod.dart' - lib\main.dart:2:8 - uri_does_not_exist
  error - Undefined name 'WidgetsFlutterBinding' - lib\main.dart:7:3 - undefined_identifier
  error - The function 'runApp' isn't defined - lib\main.dart:8:3 - undefined_function
  error - The name 'ProviderScope' isn't a class - lib\main.dart:8:16 - creation_with_non_type
  error - Targe
[extrait ; trace intégrale dans le journal]
ion 'testWidgets' isn't defined - test\ux\premium_surface_test.dart:30:3 - undefined_function
  error - The function 'MaterialApp' isn't defined - test\ux\premium_surface_test.dart:31:29 - undefined_function
  error - Undefined name 'EduNovaTheme' - test\ux\premium_surface_test.dart:32:14 - undefined_identifier
  error - The function 'Scaffold' isn't defined - test\ux\premium_surface_test.dart:33:13 - undefined_function
  error - The function 'EmptyStateCard' isn't defined - test\ux\premium_surface_test.dart:34:15 - undefined_function
  error - Undefined name 'Icons' - test\ux\premium_surface_test.dart:35:17 - undefined_identifier
  error - The function 'FilledButton' isn't defined - test\ux\premium_surface_test.dart:38:19 - undefined_function
  error - The name 'Text' isn't a class - test\ux\premium_surface_test.dart:38:63 - creation_with_non_type
  error - The function 'expect' isn't defined - test\ux\premium_surface_test.dart:42:5 - undefined_function
  error - Undefined name 'find' - test\ux\premium_surface_test.dart:42:12 - undefined_identifier
  error - Undefined name 'findsOneWidget' - test\ux\premium_surface_test.dart:42:39 - undefined_identifier
  error - The function 'expect' isn't defined - test\ux\premium_surface_test.dart:43:5 - undefined_function
  error - Undefined name 'find' - test\ux\premium_surface_test.dart:43:12 - undefined_identifier
  error - Undefined name 'findsOneWidget' - test\ux\premium_surface_test.dart:43:37 - undefined_identifier
  error - Target of URI doesn't exist: 'package:edunova/src/core/theme/edunova_theme.dart' - test\widget_test.dart:1:8 - uri_does_not_exist
  error - Target of URI doesn't exist: 'package:edunova/src/features/home/presentation/home_page.dart' - test\widget_test.dart:2:8 - uri_does_not_exist
  error - Target of URI doesn't exist: 'package:flutter/material.dart' - test\widget_test.dart:3:8 - uri_does_not_exist
  error - Target of URI doesn't exist: 'package:flutter_test/flutter_test.dart' - test\widget_test.dart:4:8 - uri_does_not_exist
  error - The function 'testWidgets' isn't defined - test\widget_test.dart:7:3 - undefined_function
  error - The function 'MaterialApp' isn't defined - test\widget_test.dart:8:29 - undefined_function
  error - Undefined name 'EduNovaTheme' - test\widget_test.dart:8:48 - undefined_identifier
  error - The name 'HomePage' isn't a class - test\widget_test.dart:8:80 - creation_with_non_type
  error - The function 'expect' isn't defined - test\widget_test.dart:9:5 - undefined_function
  error - Undefined name 'find' - test\widget_test.dart:9:12 - undefined_identifier
  error - Undefined name 'findsWidgets' - test\widget_test.dart:9:36 - undefined_identifier
  error - The function 'expect' isn't defined - test\widget_test.dart:10:5 - undefined_function
  error - Undefined name 'find' - test\widget_test.dart:10:12 - undefined_identifier
  error - Undefined name 'findsOneWidget' - test\widget_test.dart:10:51 - undefined_identifier

12137 issues found. (ran in 24.8s)

```

## Tentative non réussie — mobile-analyze-previous-1793433102054809900

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.

Trace intégrale : [mobile-analyze-previous-1793433102054809900.log](mobile-analyze-previous-1793433102054809900.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Analyzing mobile...                                             

warning - Unused import: 'package:flutter/material.dart' - lib\src\app\router.dart:7:8 - unused_import
   info - 'package:drift/web.dart' is deprecated and shouldn't be used. This variant of web support has downsides compared to `package:drift/wasm.dart` and is in a deprecated bugfix-only mode. Please consider migrating to the new web APIS: https://drift.simonbinder.eu/web - lib\src\core\database\connection\connection_web.dart:2:1 - deprecated_member_use
warning - The declaration 'firstOrNull' isn't referenced - lib\src\features\analytics\infrastructure\drift_analytics_repository.dart:112:49 - unused_element
  error - The method 'ErrorStateCard' isn't defined for the type 'AnalyticsPage' - lib\src\features\analytics\presentation\analytics_page.dart:35:18 - undefined_method
  error - The getter 'eve
[extrait ; trace intégrale dans le journal]
xpected_class_member
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:56:33 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:60:33 - deprecated_member_use
  error - Expected to find ';' - lib\src\features\study_planner\presentation\adaptive_study_planner_page.dart:17:752 - expected_token
  error - Expected a class member - lib\src\features\study_planner\presentation\adaptive_study_planner_page.dart:17:753 - expected_class_member
  error - Expected a class member - lib\src\features\study_planner\presentation\adaptive_study_planner_page.dart:17:754 - expected_class_member
warning - The value of the local variable 'scheme' isn't used - lib\src\features\study_workspace\presentation\study_workspace_page.dart:25:11 - unused_local_variable
   info - Statements in an if should be enclosed in a block - lib\src\features\sync\infrastructure\drift_cloud_sync_repository.dart:338:54 - curly_braces_in_flow_control_structures
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:83:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:85:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:105:45 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:107:45 - use_build_context_synchronously
  error - Missing concrete implementations of 'abstract interface class CloudSyncLocalRepository.recordSyncError' and 'abstract interface class CloudSyncLocalRepository.watchDiagnostics' - test\cloud_sync_use_case_test.dart:6:7 - non_abstract_class_inherits_abstract_member
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\cloud_sync_use_case_test.dart:55:16 - annotate_overrides
  error - Missing concrete implementation of 'abstract interface class LibraryLocalRepository.setCourseFollowed' - test\library_catalog_refresh_test.dart:18:7 - non_abstract_class_inherits_abstract_member
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\sync_push_integrity_test.dart:53:16 - annotate_overrides

100 issues found. (ran in 125.1s)

```

## Tentative non réussie — mobile-analyze-previous-1793434191677524900

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.

Trace intégrale : [mobile-analyze-previous-1793434191677524900.log](mobile-analyze-previous-1793434191677524900.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Analyzing mobile...                                             

warning - Unused import: 'package:flutter/material.dart' - lib\src\app\router.dart:7:8 - unused_import
   info - 'package:drift/web.dart' is deprecated and shouldn't be used. This variant of web support has downsides compared to `package:drift/wasm.dart` and is in a deprecated bugfix-only mode. Please consider migrating to the new web APIS: https://drift.simonbinder.eu/web - lib\src\core\database\connection\connection_web.dart:2:1 - deprecated_member_use
warning - The declaration 'firstOrNull' isn't referenced - lib\src\features\analytics\infrastructure\drift_analytics_repository.dart:112:49 - unused_element
   info - 'groupValue' is deprecated and shouldn't be used. Use a RadioGroup ancestor to manage group value instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\assessm
[extrait ; trace intégrale dans le journal]
s feature was deprecated after v3.33.0-1.0.pre - lib\src\features\engagement\presentation\engagement_page.dart:470:42 - deprecated_member_use
warning - Unnecessary cast - lib\src\features\identity\infrastructure\api_identity_repository.dart:29:18 - unnecessary_cast
warning - The value of the field '_reviewed' isn't used - lib\src\features\pedagogy\presentation\flashcard_session_page.dart:19:7 - unused_field
   info - 'groupValue' is deprecated and shouldn't be used. Use a RadioGroup ancestor to manage group value instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\pedagogy\presentation\quiz_session_page.dart:198:11 - deprecated_member_use
   info - 'onChanged' is deprecated and shouldn't be used. Use RadioGroup to handle value change instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\pedagogy\presentation\quiz_session_page.dart:199:11 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:56:33 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:60:33 - deprecated_member_use
warning - The value of the local variable 'scheme' isn't used - lib\src\features\study_workspace\presentation\study_workspace_page.dart:25:11 - unused_local_variable
   info - Statements in an if should be enclosed in a block - lib\src\features\sync\infrastructure\drift_cloud_sync_repository.dart:338:54 - curly_braces_in_flow_control_structures
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:83:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:85:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:105:45 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:107:45 - use_build_context_synchronously
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\cloud_sync_use_case_test.dart:55:16 - annotate_overrides
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\sync_push_integrity_test.dart:53:16 - annotate_overrides

50 issues found. (ran in 53.7s)

```

## Tentative non réussie — mobile-analyze-previous-1793436638609012000

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.

Trace intégrale : [mobile-analyze-previous-1793436638609012000.log](mobile-analyze-previous-1793436638609012000.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Analyzing mobile...                                             

warning - Unused import: 'package:flutter/material.dart' - lib\src\app\router.dart:7:8 - unused_import
   info - 'package:drift/web.dart' is deprecated and shouldn't be used. This variant of web support has downsides compared to `package:drift/wasm.dart` and is in a deprecated bugfix-only mode. Please consider migrating to the new web APIS: https://drift.simonbinder.eu/web - lib\src\core\database\connection\connection_web.dart:2:1 - deprecated_member_use
warning - The declaration 'firstOrNull' isn't referenced - lib\src\features\analytics\infrastructure\drift_analytics_repository.dart:112:49 - unused_element
   info - 'groupValue' is deprecated and shouldn't be used. Use a RadioGroup ancestor to manage group value instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\assessm
[extrait ; trace intégrale dans le journal]
s feature was deprecated after v3.33.0-1.0.pre - lib\src\features\engagement\presentation\engagement_page.dart:470:42 - deprecated_member_use
warning - Unnecessary cast - lib\src\features\identity\infrastructure\api_identity_repository.dart:29:18 - unnecessary_cast
warning - The value of the field '_reviewed' isn't used - lib\src\features\pedagogy\presentation\flashcard_session_page.dart:19:7 - unused_field
   info - 'groupValue' is deprecated and shouldn't be used. Use a RadioGroup ancestor to manage group value instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\pedagogy\presentation\quiz_session_page.dart:198:11 - deprecated_member_use
   info - 'onChanged' is deprecated and shouldn't be used. Use RadioGroup to handle value change instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\pedagogy\presentation\quiz_session_page.dart:199:11 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:56:33 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:60:33 - deprecated_member_use
warning - The value of the local variable 'scheme' isn't used - lib\src\features\study_workspace\presentation\study_workspace_page.dart:25:11 - unused_local_variable
   info - Statements in an if should be enclosed in a block - lib\src\features\sync\infrastructure\drift_cloud_sync_repository.dart:338:54 - curly_braces_in_flow_control_structures
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:83:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:85:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:105:45 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:107:45 - use_build_context_synchronously
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\cloud_sync_use_case_test.dart:55:16 - annotate_overrides
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\sync_push_integrity_test.dart:56:16 - annotate_overrides

50 issues found. (ran in 63.7s)

```

## Tentative non réussie — mobile-analyze-previous-1793475104459361900

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.

Trace intégrale : [mobile-analyze-previous-1793475104459361900.log](mobile-analyze-previous-1793475104459361900.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Analyzing mobile...                                             

warning - Unused import: 'package:flutter/material.dart' - lib\src\app\router.dart:7:8 - unused_import
   info - 'package:drift/web.dart' is deprecated and shouldn't be used. This variant of web support has downsides compared to `package:drift/wasm.dart` and is in a deprecated bugfix-only mode. Please consider migrating to the new web APIS: https://drift.simonbinder.eu/web - lib\src\core\database\connection\connection_web.dart:2:1 - deprecated_member_use
warning - The declaration 'firstOrNull' isn't referenced - lib\src\features\analytics\infrastructure\drift_analytics_repository.dart:112:49 - unused_element
   info - 'groupValue' is deprecated and shouldn't be used. Use a RadioGroup ancestor to manage group value instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\assessm
[extrait ; trace intégrale dans le journal]
s feature was deprecated after v3.33.0-1.0.pre - lib\src\features\engagement\presentation\engagement_page.dart:470:42 - deprecated_member_use
warning - Unnecessary cast - lib\src\features\identity\infrastructure\api_identity_repository.dart:29:18 - unnecessary_cast
warning - The value of the field '_reviewed' isn't used - lib\src\features\pedagogy\presentation\flashcard_session_page.dart:19:7 - unused_field
   info - 'groupValue' is deprecated and shouldn't be used. Use a RadioGroup ancestor to manage group value instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\pedagogy\presentation\quiz_session_page.dart:198:11 - deprecated_member_use
   info - 'onChanged' is deprecated and shouldn't be used. Use RadioGroup to handle value change instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\pedagogy\presentation\quiz_session_page.dart:199:11 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:56:33 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:60:33 - deprecated_member_use
warning - The value of the local variable 'scheme' isn't used - lib\src\features\study_workspace\presentation\study_workspace_page.dart:25:11 - unused_local_variable
   info - Statements in an if should be enclosed in a block - lib\src\features\sync\infrastructure\drift_cloud_sync_repository.dart:338:54 - curly_braces_in_flow_control_structures
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:83:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:85:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:105:45 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:107:45 - use_build_context_synchronously
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\cloud_sync_use_case_test.dart:55:16 - annotate_overrides
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\sync_push_integrity_test.dart:56:16 - annotate_overrides

50 issues found. (ran in 59.3s)

```

## Tentative non réussie — mobile-analyze

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.

Trace intégrale : [mobile-analyze.log](mobile-analyze.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Analyzing mobile...                                             

warning - Unused import: 'package:flutter/material.dart' - lib\src\app\router.dart:7:8 - unused_import
   info - 'package:drift/web.dart' is deprecated and shouldn't be used. This variant of web support has downsides compared to `package:drift/wasm.dart` and is in a deprecated bugfix-only mode. Please consider migrating to the new web APIS: https://drift.simonbinder.eu/web - lib\src\core\database\connection\connection_web.dart:2:1 - deprecated_member_use
warning - The declaration 'firstOrNull' isn't referenced - lib\src\features\analytics\infrastructure\drift_analytics_repository.dart:112:49 - unused_element
   info - 'groupValue' is deprecated and shouldn't be used. Use a RadioGroup ancestor to manage group value instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\assessm
[extrait ; trace intégrale dans le journal]
s feature was deprecated after v3.33.0-1.0.pre - lib\src\features\engagement\presentation\engagement_page.dart:470:42 - deprecated_member_use
warning - Unnecessary cast - lib\src\features\identity\infrastructure\api_identity_repository.dart:29:18 - unnecessary_cast
warning - The value of the field '_reviewed' isn't used - lib\src\features\pedagogy\presentation\flashcard_session_page.dart:19:7 - unused_field
   info - 'groupValue' is deprecated and shouldn't be used. Use a RadioGroup ancestor to manage group value instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\pedagogy\presentation\quiz_session_page.dart:198:11 - deprecated_member_use
   info - 'onChanged' is deprecated and shouldn't be used. Use RadioGroup to handle value change instead. This feature was deprecated after v3.32.0-0.0.pre - lib\src\features\pedagogy\presentation\quiz_session_page.dart:199:11 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:56:33 - deprecated_member_use
   info - 'value' is deprecated and shouldn't be used. Use initialValue instead. This will set the initial value for the form field. This feature was deprecated after v3.33.0-1.0.pre - lib\src\features\revision\presentation\planning_preferences_page.dart:60:33 - deprecated_member_use
warning - The value of the local variable 'scheme' isn't used - lib\src\features\study_workspace\presentation\study_workspace_page.dart:25:11 - unused_local_variable
   info - Statements in an if should be enclosed in a block - lib\src\features\sync\infrastructure\drift_cloud_sync_repository.dart:338:54 - curly_braces_in_flow_control_structures
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:83:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:85:47 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:105:45 - use_build_context_synchronously
   info - Don't use 'BuildContext's across async gaps, guarded by an unrelated 'mounted' check - lib\src\features\sync\presentation\sync_status_page.dart:107:45 - use_build_context_synchronously
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\cloud_sync_use_case_test.dart:55:16 - annotate_overrides
   info - The member 'markMutationApplied' overrides an inherited member but isn't annotated with '@override' - test\sync_push_integrity_test.dart:56:16 - annotate_overrides

50 issues found. (ran in 25.9s)

```

## Tentative non réussie — mobile-android-previous-1793437804863280900

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Build Android non certifié pour cette tentative. Examiner le téléchargement SDK/NDK, les erreurs Google Maven et le daemon Gradle ; reprendre séquentiellement après vérification réseau et avec une mémoire compatible avec les 6 Go de la machine. Aucun APK ne doit être déclaré valide sans sortie zéro et artefact vérifié.

Trace intégrale : [mobile-android-previous-1793437804863280900.log](mobile-android-previous-1793437804863280900.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
[!] Your app is using an unsupported Gradle project. To fix this problem, create a new project by running `flutter create -t app <app-directory>` and then move the dart code, assets and pubspec.yaml to the new project.

```

## Tentative non réussie — mobile-android-previous-1793467650122036200

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 124.

Build Android non certifié pour cette tentative. Examiner le téléchargement SDK/NDK, les erreurs Google Maven et le daemon Gradle ; reprendre séquentiellement après vérification réseau et avec une mémoire compatible avec les 6 Go de la machine. Aucun APK ne doit être déclaré valide sans sortie zéro et artefact vérifié.

Trace intégrale : [mobile-android-previous-1793467650122036200.log](mobile-android-previous-1793467650122036200.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Running Gradle task 'assembleDebug'...                          

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if "Windows_NT" == "Windows_NT" setlocal

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>set DEFAULT_JVM_OPTS= 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>set DIRNAME=C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android\ 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if "C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android\" == "" set DIRNAME=. 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>set APP_BASE_NAME=gradlew 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>set APP_HOME=C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android\ 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if defined JAVA_HOME goto findJavaFromJavaHome 

C:\User
[extrait ; trace intégrale dans le journal]
E_CACHE_PATH, WINDIR, VSCODE_NODE_COMPILE_CACHE_ROOT, LOCALAPPDATA, COMMONPROGRAMFILES(X86), USERDOMAIN, VSCODE_HANDLES_UNCAUGHT_ERRORS, DART_SDK_PATH, LOGONSERVER, FLUTTER_ROOT, LANG, PYTHONUTF8, ELECTRON_RUN_AS_NODE, FCM_ENABLED, PROGRAMW6432, EDUNOVA_ENV, SYSTEMROOT, NO_COLOR, CODEX_CI, APPLICATION_INSIGHTS_NO_STATSBEAT, OS, COMMONPROGRAMW6432, PYTHONIOENCODING, COMMONPROGRAMFILES, COMSPEC, CODEX_TOOL_CALL_ID, PROCESSOR_REVISION, CLASSPATH, DEBUG, TEMP, USERPROFILE, TMP, CODEX_VERSION]
2026-10-31T12:49:05.485+0200 [DEBUG] [org.gradle.launcher.daemon.server.exec.LogToClient] About to start relaying all logs to the client via the connection.
2026-10-31T12:49:05.486+0200 [INFO] [org.gradle.launcher.daemon.server.exec.LogToClient] The client will now receive all logging from the daemon (pid: 25332). The daemon log file: C:\Users\cs-ap\.gradle\daemon\8.12\daemon-25332.out.log
2026-10-31T12:49:05.578+0200 [INFO] [org.gradle.launcher.daemon.server.exec.LogAndCheckHealth] Starting 2nd build in daemon [uptime: 1 hrs 31 mins 59.139 secs, performance: 100%, GC rate: 0.00/s, heap usage: 0% of 8 GiB, non-heap usage: 5% of 4 GiB]
2026-10-31T12:49:05.581+0200 [DEBUG] [org.gradle.launcher.daemon.server.exec.ExecuteBuild] The daemon has started executing the build.
2026-10-31T12:49:05.582+0200 [DEBUG] [org.gradle.launcher.daemon.server.exec.ExecuteBuild] Executing build with daemon context: DefaultDaemonContext[uid=5b3d13b3-0354-4f6a-8e9c-c536680f99c6,javaHome=C:\Program Files\Android\Android Studio\jbr,javaVersion=21,javaVendor=JetBrains s.r.o.,daemonRegistryDir=C:\Users\cs-ap\.gradle\daemon,pid=25332,idleTimeout=10800000,priority=NORMAL,applyInstrumentationAgent=true,nativeServicesMode=ENABLED,daemonOpts=-XX:MaxMetaspaceSize=4G,-XX:ReservedCodeCacheSize=512m,-XX:+HeapDumpOnOutOfMemoryError,-Xmx8G,-Dfile.encoding=UTF-8,-Duser.country=US,-Duser.language=en,-Duser.variant]----- End of the daemon log -----

JVM crash log found: file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/android/hs_err_pid25332.log

FAILURE: Build failed with an exception.

* What went wrong:
Gradle build daemon disappeared unexpectedly (it may have been killed or may have crashed)

* Try:
> Run with --stacktrace option to get the stack trace.
> Run with --info or --debug option to get more log output.
> Run with --scan to get full insights.
> Get more help at https://help.gradle.org.

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if "1" == "0" goto mainEnd 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>rem Set variable GRADLE_EXIT_CONSOLE if you need the _script_ return code instead of 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>rem the _cmd.exe /c_ return code! 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if not "" == "" exit 1 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>exit /b 1 
Running Gradle task 'assembleDebug'...                             45.7s
Gradle task assembleDebug failed with exit code 1

```

## Tentative non réussie — mobile-android-previous-1793472328756304900

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Configuration Android manquante : flutter_local_notifications exige le core library desugaring. Activer isCoreLibraryDesugaringEnabled et la bibliothèque desugar_jdk_libs suivant le README de la version installée, puis rejouer le build. Ne pas considérer le téléchargement des dépendances comme une compilation réussie.

Trace intégrale : [mobile-android-previous-1793472328756304900.log](mobile-android-previous-1793472328756304900.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Running Gradle task 'assembleDebug'...                          

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if "Windows_NT" == "Windows_NT" setlocal

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>set DEFAULT_JVM_OPTS= 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>set DIRNAME=C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android\ 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if "C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android\" == "" set DIRNAME=. 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>set APP_BASE_NAME=gradlew 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>set APP_HOME=C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android\ 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if defined JAVA_HOME goto findJavaFromJavaHome 

C:\User
[extrait ; trace intégrale dans le journal]
dXR0ZXIuZ2l0,RkxVVFRFUl9GUkFNRVdPUktfUkVWSVNJT049ZDY5M2I0YjlkYg==,RkxVVFRFUl9FTkdJTkVfUkVWSVNJT049YzI5ODA5MTM1MQ==,RkxVVFRFUl9EQVJUX1ZFUlNJT049My45LjI= -Pdart-obfuscation=false -Ptrack-widget-creation=true -Ptree-shake-icons=false assembleDebug 
Checking the license for package Android SDK Build-Tools 35 in C:\Users\cs-ap\dev\Android\Sdk\licenses
License for package Android SDK Build-Tools 35 accepted.
Preparing "Install Android SDK Build-Tools 35 v.35.0.0".
"Install Android SDK Build-Tools 35 v.35.0.0" ready.
Installing Android SDK Build-Tools 35 in C:\Users\cs-ap\dev\Android\Sdk\build-tools\35.0.0
"Install Android SDK Build-Tools 35 v.35.0.0" complete.
"Install Android SDK Build-Tools 35 v.35.0.0" finished.
Checking the license for package Android SDK Platform 34 in C:\Users\cs-ap\dev\Android\Sdk\licenses
License for package Android SDK Platform 34 accepted.
Preparing "Install Android SDK Platform 34 (revision 3)".
"Install Android SDK Platform 34 (revision 3)" ready.
Installing Android SDK Platform 34 in C:\Users\cs-ap\dev\Android\Sdk\platforms\android-34
"Install Android SDK Platform 34 (revision 3)" complete.
"Install Android SDK Platform 34 (revision 3)" finished.
Checking the license for package Android SDK Platform 35 in C:\Users\cs-ap\dev\Android\Sdk\licenses
License for package Android SDK Platform 35 accepted.
Preparing "Install Android SDK Platform 35 (revision 2)".
"Install Android SDK Platform 35 (revision 2)" ready.
Installing Android SDK Platform 35 in C:\Users\cs-ap\dev\Android\Sdk\platforms\android-35
"Install Android SDK Platform 35 (revision 2)" complete.
"Install Android SDK Platform 35 (revision 2)" finished.

FAILURE: Build failed with an exception.

* What went wrong:
Execution failed for task ':app:checkDebugAarMetadata'.
> A failure occurred while executing com.android.build.gradle.internal.tasks.CheckAarMetadataWorkAction
   > An issue was found when checking AAR metadata:

       1.  Dependency ':flutter_local_notifications' requires core library desugaring to be enabled
           for :app.

           See https://developer.android.com/studio/write/java8-support.html for more
           details.

* Try:
> Run with --stacktrace option to get the stack trace.
> Run with --info or --debug option to get more log output.
> Run with --scan to get full insights.
> Get more help at https://help.gradle.org.

BUILD FAILED in 33m 1s

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if "1" == "0" goto mainEnd 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>rem Set variable GRADLE_EXIT_CONSOLE if you need the _script_ return code instead of 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>rem the _cmd.exe /c_ return code! 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>if not "" == "" exit 1 

C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\android>exit /b 1 
Running Gradle task 'assembleDebug'...                           1987.3s
Gradle task assembleDebug failed with exit code 1

```

## Tentative non réussie — mobile-test-previous-1793394551509287100

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.

Trace intégrale : [mobile-test-previous-1793394551509287100.log](mobile-test-previous-1793394551509287100.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Error: cannot run without a dependency on either "package:flutter_test" or "package:test". Ensure the following lines are present in your pubspec.yaml:

dev_dependencies:
  flutter_test:
    sdk: flutter


```

## Tentative non réussie — mobile-test-previous-1793433174507875900

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.

Trace intégrale : [mobile-test-previous-1793433174507875900.log](mobile-test-previous-1793433174507875900.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart
00:00 +0: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: high cognitive work is skipped in low energy window
00:00 +1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: planner respects study capacity and breaks
00:00 +2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: deferred work gains explicit priority reason
00:02 +3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: momentum is explainable and improving
00:02 +4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: urgent low readiness course is prioritized
00:02 +5: C:/Users/cs-ap/dev/edusync-web/e
[extrait ; trace intégrale dans le journal]
e 'DownloadResource' not found.
    final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
                                                                                           ^^^^^^^^^^^^^^^^
  lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart:132:5: Error: A value of type 'Map<String, dynamic>' can't be returned from a function with return type 'Future<Map<String, dynamic>>'.
   - 'Map' is from 'dart:core'.
   - 'Future' is from 'dart:async'.
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
      ^
  lib/src/features/delivery/application/delivery_repository.dart:56:90: Error: 'DownloadResource' isn't a type.
    final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
                                                                                           ^^^^^^^^^^^^^^^^
  lib/src/features/delivery/application/download_resource.dart:30:25: Error: Not a constant expression.
          final ids=const CacheEvictionPlanner().plan(candidates:await local.cacheCandidates(),currentBytes:currentCache,targetBytes:(policy.maxCacheBytes-grant.sizeBytes).clamp(0,policy.maxCacheBytes).toInt(),keepFollowed:policy.keepFollowedCourses);
                          ^^^^^^^^^^^^^^^^^^^^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:45:29: Error: Too many positional arguments: 0 allowed, but 1 found.
  Try removing the extra positional arguments.
      await _plugin.initialize(
                              ^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:78:32: Error: Too many positional arguments: 0 allowed, but 5 found.
  Try removing the extra positional arguments.
      await _plugin.zonedSchedule(_id(n.id),n.title,n.body,tz.TZDateTime.from(n.fireAt.toUtc(),tz.UTC),details,androidScheduleMode:AndroidScheduleMode.inexactAllowWhileIdle,payload:payload);
                                 ^
  lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart:81:91: Error: Too many positional arguments: 0 allowed, but 1 found.
  Try removing the extra positional arguments.
    @override Future<void> cancel(String id) async {await initialize(); await _plugin.cancel(_id(id));}
                                                                                            ^
  lib/src/features/identity/infrastructure/legacy_offline_files_native.dart:11:45: Error: The getter 'isNotEmpty' isn't defined for the type 'Stream<FileSystemEntity>'.
   - 'Stream' is from 'dart:async'.
   - 'FileSystemEntity' is from 'dart:io'.
  Try correcting the name to the name of an existing getter, or defining a getter or field named 'isNotEmpty'.
    return directory.list(followLinks: false).isNotEmpty;
                                              ^^^^^^^^^^
  .
03:23 +49 -21: Some tests failed.

```

## Tentative non réussie — mobile-test-previous-1793434287522519600

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.

Trace intégrale : [mobile-test-previous-1793434287522519600.log](mobile-test-previous-1793434287522519600.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart
00:00 +0: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: momentum is explainable and improving
00:00 +1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: high cognitive work is skipped in low energy window
00:00 +2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: urgent low readiness course is prioritized
00:00 +3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: planner respects study capacity and breaks
00:00 +4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: recommendations remain diversified
00:00 +5: C:/Users/cs-ap/dev/edusync-web/ed
[extrait ; trace intégrale dans le journal]
ing.handleDrawFrame (package:flutter/src/scheduler/binding.dart:1347:9)
#777    AutomatedTestWidgetsFlutterBinding.pump.<anonymous closure> (package:flutter_test/src/binding.dart:1335:9)
#780    TestAsyncUtils.guard (package:flutter_test/src/test_async_utils.dart:74:41)
#781    AutomatedTestWidgetsFlutterBinding.pump (package:flutter_test/src/binding.dart:1324:27)
#782    WidgetTester.pumpWidget.<anonymous closure> (package:flutter_test/src/widget_tester.dart:598:22)
#785    TestAsyncUtils.guard (package:flutter_test/src/test_async_utils.dart:74:41)
#786    WidgetTester.pumpWidget (package:flutter_test/src/widget_tester.dart:595:27)
#787    main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart:8:18)
#788    testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:29)
<asynchronous suspension>
#789    TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 5 frames from dart:async and package:stack_trace)

════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: at least one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Biochimie": []>
   Which: means none were found but some were expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart:9:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart line 9
The test description was:
  home renders premium preparation card
════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following message was thrown:
Multiple exceptions (2) were detected during the running of the current test, and at least one was
unexpected.
════════════════════════════════════════════════════════════════════════════════════════════════════
01:35 +76 -18: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders premium preparation card [E]
  Test failed. See exception logs above.
  The test description was: home renders premium preparation card
  
01:35 +76 -18: Some tests failed.

```

## Tentative non réussie — mobile-test-previous-1793436711215236100

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.

Trace intégrale : [mobile-test-previous-1793436711215236100.log](mobile-test-previous-1793436711215236100.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart
00:00 +0: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: high cognitive work is skipped in low energy window
00:00 +1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: planner respects study capacity and breaks
00:00 +2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: deferred work gains explicit priority reason
00:01 +3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: momentum is explainable and improving
00:01 +4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: urgent low readiness course is prioritized
00:01 +5: C:/Users/cs-ap/dev/edusync-web/e
[extrait ; trace intégrale dans le journal]
nding.handleDrawFrame (package:flutter/src/scheduler/binding.dart:1347:9)
#777    AutomatedTestWidgetsFlutterBinding.pump.<anonymous closure> (package:flutter_test/src/binding.dart:1335:9)
#780    TestAsyncUtils.guard (package:flutter_test/src/test_async_utils.dart:74:41)
#781    AutomatedTestWidgetsFlutterBinding.pump (package:flutter_test/src/binding.dart:1324:27)
#782    WidgetTester.pumpWidget.<anonymous closure> (package:flutter_test/src/widget_tester.dart:598:22)
#785    TestAsyncUtils.guard (package:flutter_test/src/test_async_utils.dart:74:41)
#786    WidgetTester.pumpWidget (package:flutter_test/src/widget_tester.dart:595:27)
#787    main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart:8:18)
#788    testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:29)
<asynchronous suspension>
#789    TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided 5 frames from dart:async and package:stack_trace)

════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following TestFailure was thrown running a test:
Expected: at least one matching candidate
  Actual: _TextWidgetFinder:<Found 0 widgets with text "Biochimie": []>
   Which: means none were found but some were expected

When the exception was thrown, this was the stack:
#4      main.<anonymous closure> (file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart:9:5)
<asynchronous suspension>
#5      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#6      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
<asynchronous suspension>
(elided one frame from package:stack_trace)

This was caught by the test expectation on the following line:
  file:///C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart line 9
The test description was:
  home renders premium preparation card
════════════════════════════════════════════════════════════════════════════════════════════════════
══╡ EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK ╞════════════════════════════════════════════════════
The following message was thrown:
Multiple exceptions (2) were detected during the running of the current test, and at least one was
unexpected.
════════════════════════════════════════════════════════════════════════════════════════════════════
01:06 +88 -6: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders premium preparation card [E]
  Test failed. See exception logs above.
  The test description was: home renders premium preparation card
  
01:06 +88 -6: Some tests failed.

```

## Tentative non réussie — mobile-test-previous-1793439446720879300

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.

Trace intégrale : [mobile-test-previous-1793439446720879300.log](mobile-test-previous-1793439446720879300.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart
00:00 +0: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: high cognitive work is skipped in low energy window
00:00 +1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: planner respects study capacity and breaks
00:00 +2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: deferred work gains explicit priority reason
00:00 +3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: momentum is explainable and improving
00:00 +4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: urgent low readiness course is prioritized
00:00 +5: C:/Users/cs-ap/dev/edusync-web/e
[extrait ; trace intégrale dans le journal]
ch OCR timetable rows conservatively
01:06 +74 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/secure_session_account_ownership_test.dart: logout retains ownership and blocks another account
01:06 +75 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/secure_session_account_ownership_test.dart: concurrent saves cannot claim the same installation twice
01:06 +76 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/secure_session_account_ownership_test.dart: reading a legacy authenticated session immediately pins ownership
01:06 +77 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/secure_session_account_ownership_test.dart: legacy authenticated session is pinned on logout
01:07 +78 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
01:08 +79 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox
01:08 +80 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity
01:08 +81 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes
01:08 +82 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes
01:08 +83 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
01:08 +84 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
01:08 +85 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
01:08 +86 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
01:08 +87 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
01:08 +88 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
01:08 +89 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
01:08 +90 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
01:13 +91 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders preparation for an empty local account
01:13 +92 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders preparation for an empty local account
01:14 +93 -1: Some tests failed.

```

## Tentative non réussie — mobile-test-previous-1793443731860620100

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.

Trace intégrale : [mobile-test-previous-1793443731860620100.log](mobile-test-previous-1793443731860620100.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --reporter=expanded
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
00:00 +0: loading C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart
00:00 +0: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: high cognitive work is skipped in low energy window
00:00 +1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: momentum is explainable and improving
00:00 +2: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: planner respects study capacity and breaks
00:00 +3: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/analytics/analytics_engine_test.dart: urgent low readiness course is prioritized
00:00 +4: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/adaptive_planning_test.dart: deferred work gains explicit priority reason
00:00 +5: C:/Users/cs-ap/dev/edusync-web/e
[extrait ; trace intégrale dans le journal]
/mobile/test/secure_session_account_ownership_test.dart: logout retains ownership and blocks another account
01:09 +75 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/secure_session_account_ownership_test.dart: concurrent saves cannot claim the same installation twice
01:09 +76 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/secure_session_account_ownership_test.dart: reading a legacy authenticated session immediately pins ownership
01:09 +77 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/secure_session_account_ownership_test.dart: legacy authenticated session is pinned on logout
01:15 +78 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late unknown disposition never partially acknowledges outbox
01:16 +79 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: late conflict without canonical never partially acknowledges outbox
01:16 +80 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched successful canonical record cannot modify another entity
01:16 +81 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: mismatched conflict canonical record is rejected before writes
01:16 +82 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: invalid canonical version is rejected before writes
01:16 +83 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: regressing pull cursor is rejected before acknowledgement
01:16 +84 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: non-progressing paginated pull cursor is rejected
01:16 +85 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: missing push outcome blocks pull and keeps outbox
01:16 +86 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: duplicate push outcome blocks pull and keeps outbox
01:16 +87 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: unknown push outcome blocks pull and keeps outbox
01:16 +88 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: account switch during push cannot commit old account outcomes
01:16 +89 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/sync_push_integrity_test.dart: simultaneous triggers share a single push and release lock after failure
01:19 +90 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/ux/premium_surface_test.dart: PremiumPanel remains usable with large text
01:21 +91 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders preparation for an empty local account
01:22 +92 -1: C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/test/widget_test.dart: home renders preparation for an empty local account
01:22 +93 -1: Some tests failed.

```

## Tentative non réussie — mobile-web-previous-1793394862002167500

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Consulter les cas individuels et les corrections décrites dans le rapport ; les suites et audits historiques restent distincts.

Trace intégrale : [mobile-web-previous-1793394862002167500.log](mobile-web-previous-1793394862002167500.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
This project is not configured for the web.
To configure this project for the web, run flutter create . --platforms web

```

## Tentative non réussie — mobile-web-previous-1793433288234098400

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Consulter les cas individuels et les corrections décrites dans le rapport ; les suites et audits historiques restent distincts.

Trace intégrale : [mobile-web-previous-1793433288234098400.log](mobile-web-previous-1793433288234098400.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Compiling lib\main.dart for the Web...                          
Wasm dry run findings:
Found incompatibilities with WebAssembly.

package:flutter_secure_storage_web/flutter_secure_storage_web.dart 5:1 - dart:html unsupported (0)
package:flutter_secure_storage_web/src/subtle.dart 21:1 - dart:html unsupported (0)
package:js/js.dart 10:1 - dart:js unsupported (1)
package:flutter_secure_storage_web/flutter_secure_storage_web.dart 6:1 - JS interop library 'dart:js_util' can't be imported when compiling to Wasm. (2)
package:flutter_secure_storage_web/src/subtle.dart 22:1 - JS interop library 'dart:js_util' can't be imported when compiling to Wasm. (2)
package:flutter_secure_storage_web/src/subtle.dart 26:1 - JS interop library 'package:js/js.dart' can't be imported when compiling to Wasm. (2)

Consider addressing these issues to enable wasm builds. See doc
[extrait ; trace intégrale dans le journal]
EB_USE_SKWASM=false -DFLUTTER_WEB_CANVASKIT_URL=https://www.gstatic.com/flutter-canvaskit/c29809135135e262a912cf583b2c90deb9ded610/ --native-null-assertions --no-source-maps -O4 --minify -o C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\.dart_tool\flutter_build\06891925383680661ef2ef3e4209975d\app.dill --packages=C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\.dart_tool\package_config.json --cfe-only C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\.dart_tool\flutter_build\06891925383680661ef2ef3e4209975d\main.dart
#0      RunResult.throwException (package:flutter_tools/src/base/process.dart:118:5)
#1      _DefaultProcessUtils.run (package:flutter_tools/src/base/process.dart:344:19)
<asynchronous suspension>
#2      Dart2JSTarget.build (package:flutter_tools/src/build_system/targets/web.dart:204:5)
<asynchronous suspension>
#3      _BuildInstance._invokeInternal (package:flutter_tools/src/build_system/build_system.dart:873:9)
<asynchronous suspension>
#4      Future.wait.<anonymous closure> (dart:async/future.dart:525:21)
<asynchronous suspension>
#5      _BuildInstance.invokeTarget (package:flutter_tools/src/build_system/build_system.dart:811:32)
<asynchronous suspension>
#6      Future.wait.<anonymous closure> (dart:async/future.dart:525:21)
<asynchronous suspension>
#7      _BuildInstance.invokeTarget (package:flutter_tools/src/build_system/build_system.dart:811:32)
<asynchronous suspension>
#8      FlutterBuildSystem.build (package:flutter_tools/src/build_system/build_system.dart:631:16)
<asynchronous suspension>
#9      WebBuilder.buildWeb (package:flutter_tools/src/web/compile.dart:90:34)
<asynchronous suspension>
#10     BuildWebCommand.runCommand (package:flutter_tools/src/commands/build_web.dart:282:5)
<asynchronous suspension>
#11     FlutterCommand.run.<anonymous closure> (package:flutter_tools/src/runner/flutter_command.dart:1581:27)
<asynchronous suspension>
#12     AppContext.run.<anonymous closure> (package:flutter_tools/src/base/context.dart:154:19)
<asynchronous suspension>
#13     CommandRunner.runCommand (package:args/command_runner.dart:212:13)
<asynchronous suspension>
#14     FlutterCommandRunner.runCommand.<anonymous closure> (package:flutter_tools/src/runner/flutter_command_runner.dart:503:9)
<asynchronous suspension>
#15     AppContext.run.<anonymous closure> (package:flutter_tools/src/base/context.dart:154:19)
<asynchronous suspension>
#16     FlutterCommandRunner.runCommand (package:flutter_tools/src/runner/flutter_command_runner.dart:438:5)
<asynchronous suspension>
#17     run.<anonymous closure>.<anonymous closure> (package:flutter_tools/runner.dart:98:11)
<asynchronous suspension>
#18     AppContext.run.<anonymous closure> (package:flutter_tools/src/base/context.dart:154:19)
<asynchronous suspension>
#19     main (package:flutter_tools/executable.dart:101:3)
<asynchronous suspension>

Compiling lib\main.dart for the Web...                          10264.9s
Error: Failed to compile application for the Web.

```

## Tentative non réussie — mobile-windows-previous-1793436076733585500

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Vérifier successivement le support des symlinks, NuGet, ATL et le préfixe CMake. Ces prérequis/caches ont été corrigés au fil des reprises. Un exécutable intermédiaire ne prouve pas que le bundle INSTALL a réussi.

Trace intégrale : [mobile-windows-previous-1793436076733585500.log](mobile-windows-previous-1793436076733585500.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Building with plugins requires symlink support.

Please enable Developer Mode in your system settings. Run
  start ms-settings:developers
to open settings.

```

## Tentative non réussie — mobile-windows-previous-1793439565944350700

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Vérifier successivement le support des symlinks, NuGet, ATL et le préfixe CMake. Ces prérequis/caches ont été corrigés au fil des reprises. Un exécutable intermédiaire ne prouve pas que le bundle INSTALL a réussi.

Trace intégrale : [mobile-windows-previous-1793439565944350700.log](mobile-windows-previous-1793439565944350700.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Building Windows application...                                 
CMake Deprecation Warning at C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/build/windows/x64/extracted/firebase_cpp_sdk_windows/CMakeLists.txt:17 (cmake_minimum_required):
  Compatibility with CMake < 3.10 will be removed from a future version of
  CMake.

  Update the VERSION argument <min> value.  Or, use the <min>...<max> syntax
  to tell CMake that the project requires at least <min> but has been updated
  to work with policies introduced by <max> or earlier.


CMake Error at flutter/ephemeral/.plugin_symlinks/flutter_tts/windows/CMakeLists.txt:12 (message):
  nuget.exe not found.  Please install it.


Building Windows application...                                  1719.0s
Unable to generate build files

```

## Tentative non réussie — mobile-windows-previous-1793466628214105900

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Vérifier successivement le support des symlinks, NuGet, ATL et le préfixe CMake. Ces prérequis/caches ont été corrigés au fil des reprises. Un exécutable intermédiaire ne prouve pas que le bundle INSTALL a réussi.

Trace intégrale : [mobile-windows-previous-1793466628214105900.log](mobile-windows-previous-1793466628214105900.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Building Windows application...                                 
CMake Deprecation Warning at C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/build/windows/x64/extracted/firebase_cpp_sdk_windows/CMakeLists.txt:17 (cmake_minimum_required):
  Compatibility with CMake < 3.10 will be removed from a future version of
  CMake.

  Update the VERSION argument <min> value.  Or, use the <min>...<max> syntax
  to tell CMake that the project requires at least <min> but has been updated
  to work with policies introduced by <max> or earlier.


C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\windows\flutter\ephemeral\.plugin_symlinks\flutter_secure_storage_windows\windows\flutter_secure_storage_windows_plugin.cpp(6,10): error C1083: Cannot open include file: 'atlstr.h': No such file or directory [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\plugins\flutter_secure_storage_windows\flutter_secure_storage_windows_plugin.vcxproj]
C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\windows\flutter\ephemeral\.plugin_symlinks\flutter_local_notifications_windows\src\plugin.cpp(5,10): error C1083: Cannot open include file: 'atlbase.h': No such file or directory [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\plugins\flutter_local_notifications_windows\shared\flutter_local_notifications_windows.vcxproj]
Building Windows application...                                   567.5s
Build process failed.

```

## Tentative non réussie — mobile-windows-previous-1793467612749233600

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub` dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile`. Code 1.

Vérifier successivement le support des symlinks, NuGet, ATL et le préfixe CMake. Ces prérequis/caches ont été corrigés au fil des reprises. Un exécutable intermédiaire ne prouve pas que le bundle INSTALL a réussi.

Trace intégrale : [mobile-windows-previous-1793467612749233600.log](mobile-windows-previous-1793467612749233600.log).

```text
COMMAND: C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub
CWD: C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile
Building Windows application...                                 
CMake Deprecation Warning at C:/Users/cs-ap/dev/edusync-web/edunova/apps/mobile/build/windows/x64/extracted/firebase_cpp_sdk_windows/CMakeLists.txt:17 (cmake_minimum_required):
  Compatibility with CMake < 3.10 will be removed from a future version of
  CMake.

  Update the VERSION argument <min> value.  Or, use the <min>...<max> syntax
  to tell CMake that the project requires at least <min> but has been updated
  to work with policies introduced by <max> or earlier.


C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: The command "setlocal [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" -DBUILD_TYPE=Release -P cmake_install.cmake [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: if %errorlevel% neq 0 goto :cmEnd [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: :cmEnd [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: endlocal & call :cmErrorLevel %errorlevel% & goto :cmDone [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: :cmErrorLevel [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: exit /b %1 [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: :cmDone [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: if %errorlevel% neq 0 goto :VCEnd [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\Microsoft.CppCommon.targets(166,5): error MSB3073: :VCEnd" exited with code 1. [C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile\build\windows\x64\INSTALL.vcxproj]
Building Windows application...                                   130.4s
Build process failed.

```

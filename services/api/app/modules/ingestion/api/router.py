from __future__ import annotations

from dataclasses import asdict
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.modules.identity.application.auth_context import AuthContext
from app.modules.identity.api.router import current_auth
from app.modules.ingestion.domain.model import BatchDefaults
from app.modules.editorial.domain.model import ContentKind,RiskLevel,RightsStatus
from app.runtime import runtime
from app.shared.security.rate_limit import RateLimitExceeded

router = APIRouter()


class BatchDefaultsBody(BaseModel):
    content_kind: ContentKind
    faculty_domain: str = Field(min_length=1, max_length=120)
    program: str = Field(min_length=1, max_length=160)
    level: str = Field(min_length=1, max_length=80)
    semester: str | None = None
    risk: RiskLevel = RiskLevel.STANDARD
    rights_status: RightsStatus = RightsStatus.UNKNOWN
    rights_note: str = ""


class CreateBatchBody(BaseModel):
    name: str = Field(min_length=3, max_length=240)
    defaults: BatchDefaultsBody


class StartBody(BaseModel):
    priority: int = Field(default=50, ge=0, le=100)


def _dt(v): return v.isoformat() if v else None

def _batch(b):
    return {"id":b.id,"name":b.name,"created_by":b.created_by,"state":b.state.value,"defaults":asdict(b.defaults),"manifest_version":b.manifest_version,"manifest_sha256":b.manifest_sha256,"created_at":_dt(b.created_at),"updated_at":_dt(b.updated_at),"frozen_at":_dt(b.frozen_at),"cancelled_at":_dt(b.cancelled_at),"manifest_snapshot_available":bool(b.manifest_json)}

def _document(d):
    return {"id":d.id,"batch_id":d.batch_id,"filename":d.filename,"declared_mime_type":d.declared_mime_type,"detected_mime_type":d.detected_mime_type,"size_bytes":d.size_bytes,"checksum_sha256":d.checksum_sha256,"page_count":d.page_count,"width_px":d.width_px,"height_px":d.height_px,"state":d.state.value,"preflight_status":d.preflight_status.value,"rejection_code":d.rejection_code,"duplicate_of_document_id":d.duplicate_of_document_id,"created_at":_dt(d.created_at),"updated_at":_dt(d.updated_at),"editorial_item_id":d.editorial_item_id}

def _job(j):
    return {"id":j.id,"batch_id":j.batch_id,"document_id":j.document_id,"state":j.state.value,"priority":j.priority,"attempt":j.attempt,"max_attempts":j.max_attempts,"next_run_at":_dt(j.next_run_at),"lease_owner":j.lease_owner,"lease_expires_at":_dt(j.lease_expires_at),"heartbeat_at":_dt(j.heartbeat_at),"started_at":_dt(j.started_at),"completed_at":_dt(j.completed_at),"last_error":j.last_error}

def _result(r):
    return {"id":r.id,"batch_id":r.batch_id,"document_id":r.document_id,"job_id":r.job_id,"artifact_sha256":r.artifact_sha256,"pipeline_version":r.pipeline_version,"page_count":r.page_count,"sections_count":r.sections_count,"chunks_count":r.chunks_count,"questions_count":r.questions_count,"mean_ocr_confidence":r.mean_ocr_confidence,"usable_text_ratio":r.usable_text_ratio,"warnings":list(r.warnings),"needs_human_verification":r.needs_human_verification,"editorial_item_id":r.editorial_item_id,"created_at":_dt(r.created_at)}

def _metrics(m): return {k:getattr(m,k) for k in m.__dataclass_fields__}

def _limit(account_id:str,action:str,limit:int,window:int):
    try: runtime.rate_limiter.check(key=f"ingestion:{action}:{account_id}",limit=limit,window_seconds=window)
    except RateLimitExceeded as e: raise HTTPException(status_code=429,detail="too_many_attempts") from e

def _wrap(fn):
    try:return fn()
    except PermissionError as e: raise HTTPException(status_code=403,detail=str(e)) from e
    except ValueError as e:
        code=str(e); status=409 if code in {"batch_manifest_frozen"} else 422
        raise HTTPException(status_code=status,detail=code) from e
    except RuntimeError as e: raise HTTPException(status_code=503,detail=str(e)) from e



@router.get('/dashboard')
def ingestion_dashboard(auth:AuthContext=Depends(current_auth)):
    return _wrap(lambda:runtime.ingestion.dashboard(auth.account_id))


@router.get('/documents/{document_id}/preview')
def preview_document(document_id:str,page:int=Query(1,ge=1,le=5000),auth:AuthContext=Depends(current_auth)):
    return _wrap(lambda:runtime.ingestion.preview(auth.account_id,document_id,page))

@router.post('/batches')
def create_batch(req:CreateBatchBody,auth:AuthContext=Depends(current_auth)):
    _limit(auth.account_id,'create-batch',20,3600)
    raw=req.defaults.model_dump()
    raw['content_kind']=req.defaults.content_kind.value; raw['risk']=req.defaults.risk.value; raw['rights_status']=req.defaults.rights_status.value
    defaults=BatchDefaults(**raw)
    return _batch(_wrap(lambda:runtime.ingestion.create_batch(actor_id=auth.account_id,name=req.name,defaults=defaults)))


@router.get('/batches')
def list_batches(limit:int=Query(50,ge=1,le=200),offset:int=Query(0,ge=0),auth:AuthContext=Depends(current_auth)):
    return [_batch(x) for x in _wrap(lambda:runtime.ingestion.batches(auth.account_id,limit=limit,offset=offset))]


@router.get('/batches/{batch_id}')
def detail(batch_id:str,auth:AuthContext=Depends(current_auth)):
    d=_wrap(lambda:runtime.ingestion.detail(auth.account_id,batch_id))
    return {"batch":_batch(d['batch']),"documents":[_document(x) for x in d['documents']],"jobs":[_job(x) for x in d['jobs']],"results":[_result(x) for x in d['results']],"metrics":_metrics(d['metrics']),"audit":[{**x,"occurred_at":_dt(x.get("occurred_at"))} for x in d.get("audit",())]}


@router.post('/batches/{batch_id}/files')
async def upload_file(batch_id:str,file:UploadFile=File(...),idempotency_key:str|None=Header(default=None,alias='Idempotency-Key'),auth:AuthContext=Depends(current_auth)):
    payload=await file.read()
    import hashlib
    key=(idempotency_key or '').strip() or f"upload:{hashlib.sha256(payload).hexdigest()}"
    doc=_wrap(lambda:runtime.ingestion.add_file(actor_id=auth.account_id,batch_id=batch_id,filename=file.filename or 'document',payload=payload,declared_mime_type=file.content_type,idempotency_key=key))
    return _document(doc)



@router.post('/batches/{batch_id}/image-bundles')
async def upload_image_bundle(batch_id:str,files:list[UploadFile]=File(...),bundle_name:str='scan',idempotency_key:str|None=Header(default=None,alias='Idempotency-Key'),auth:AuthContext=Depends(current_auth)):
    _limit(auth.account_id,'bundle',60,60)
    import hashlib
    parts=[]; digest=hashlib.sha256()
    max_bytes=runtime.ingestion.preflight.policy.max_file_bytes
    total=0
    for f in files:
        payload=await f.read(); total+=len(payload)
        if total>max_bytes: raise HTTPException(status_code=413,detail='bundle_too_large')
        digest.update(payload); parts.append((f.filename or 'scan',payload,f.content_type))
    key=(idempotency_key or '').strip() or f"bundle:{digest.hexdigest()}"
    return _document(_wrap(lambda:runtime.ingestion.add_image_bundle(actor_id=auth.account_id,batch_id=batch_id,bundle_name=bundle_name,files=parts,idempotency_key=key)))

@router.delete('/batches/{batch_id}/files/{document_id}',status_code=204)
def remove_file(batch_id:str,document_id:str,auth:AuthContext=Depends(current_auth)):
    _wrap(lambda:runtime.ingestion.remove_file(actor_id=auth.account_id,batch_id=batch_id,document_id=document_id))


@router.post('/batches/{batch_id}/start')
def start_batch(batch_id:str,req:StartBody=StartBody(),auth:AuthContext=Depends(current_auth)):
    _limit(auth.account_id,'start-batch',60,3600)
    return _batch(_wrap(lambda:runtime.ingestion.start_batch(actor_id=auth.account_id,batch_id=batch_id,priority=req.priority)))


@router.post('/batches/{batch_id}/cancel')
def cancel_batch(batch_id:str,auth:AuthContext=Depends(current_auth)):
    return _batch(_wrap(lambda:runtime.ingestion.cancel_batch(actor_id=auth.account_id,batch_id=batch_id)))


@router.get('/batches/{batch_id}/report')
def batch_report(batch_id:str,auth:AuthContext=Depends(current_auth)):
    return _wrap(lambda:runtime.ingestion.batch_report(auth.account_id,batch_id))


@router.get('/batches/{batch_id}/manifest/verify')
def verify_manifest(batch_id:str,auth:AuthContext=Depends(current_auth)):
    return _wrap(lambda:runtime.ingestion.verify_manifest(auth.account_id,batch_id))


@router.post('/batches/{batch_id}/dead-letters/retry')
def retry_dead_letters_bulk(batch_id:str,auth:AuthContext=Depends(current_auth)):
    _limit(auth.account_id,'retry-dead-letters-bulk',20,3600)
    return _wrap(lambda:runtime.ingestion.retry_dead_letters_bulk(actor_id=auth.account_id,batch_id=batch_id))


@router.post('/jobs/{job_id}/retry')
def retry_job(job_id:str,auth:AuthContext=Depends(current_auth)):
    _limit(auth.account_id,'retry-job',60,3600)
    return _job(_wrap(lambda:runtime.ingestion.retry_dead_letter(actor_id=auth.account_id,job_id=job_id)))


@router.post('/maintenance/recover-leases')
def recover_leases(auth:AuthContext=Depends(current_auth)):
    return {"recovered":_wrap(lambda:runtime.ingestion.recover_leases(actor_id=auth.account_id))}

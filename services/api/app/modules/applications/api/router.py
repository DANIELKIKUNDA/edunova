from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,Form
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
class CreateIn(BaseModel):
 campaign_id:str;given_names:str=Field(min_length=1,max_length=160);family_name:str=Field(min_length=1,max_length=120);birth_date:str|None=None;nationality_code:str|None=None;gender:str|None=None;address:str|None=None;city:str|None=None;country_code:str|None=None;phone_number:str|None=None;email:str|None=None
class PatchIn(BaseModel):
 given_names:str|None=None;family_name:str|None=None;birth_date:str|None=None;nationality_code:str|None=None;gender:str|None=None;address:str|None=None;city:str|None=None;country_code:str|None=None;phone_number:str|None=None;email:str|None=None
def wrap(fn):
 try:return fn()
 except ValueError as e:raise HTTPException(422,str(e)) from e
def out(x):return {**x.__dict__,'state':x.state.value,'created_at':x.created_at.isoformat(),'updated_at':x.updated_at.isoformat(),'submitted_at':x.submitted_at.isoformat() if x.submitted_at else None,'withdrawn_at':x.withdrawn_at.isoformat() if x.withdrawn_at else None}
@router.post('/applications',status_code=201)
def create(req:CreateIn,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.applications.create(auth.account_id,**req.model_dump())))
@router.patch('/applications/{aid}')
def patch(aid:str,expected_version:int,req:PatchIn,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.applications.update(auth.account_id,aid,expected_version,**req.model_dump(exclude_unset=True))))
@router.get('/applications/{aid}')
def detail(aid:str,auth:AuthContext=Depends(current_auth)):
 x,docs,ready=wrap(lambda:runtime.applications.detail(auth.account_id,aid));return {'application':out(x),'readiness':ready,'documents':[{'id':d.id,'requirement_code':d.requirement_code,'original_name':d.original_name,'content_type':d.content_type,'size_bytes':d.size_bytes,'sha256':d.sha256,'state':d.state.value} for d in docs]}
@router.post('/applications/{aid}/documents')
async def upload(aid:str,requirement_code:str=Form(...),file:UploadFile=File(...),auth:AuthContext=Depends(current_auth)):
 payload=await file.read(runtime.applications.MAX_BYTES+1);d=wrap(lambda:runtime.applications.upload(auth.account_id,aid,requirement_code,file.filename or 'document',file.content_type or 'application/octet-stream',payload));return {'id':d.id,'requirement_code':d.requirement_code,'sha256':d.sha256,'size_bytes':d.size_bytes,'state':d.state.value}
@router.get('/applications/{aid}/readiness')
def readiness(aid:str,auth:AuthContext=Depends(current_auth)):return wrap(lambda:runtime.applications.readiness(auth.account_id,aid))
@router.post('/applications/{aid}/submit')
def submit(aid:str,expected_version:int,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.applications.submit(auth.account_id,aid,expected_version)))
class UploadStartIn(BaseModel):
 requirement_code:str;filename:str;content_type:str;total_bytes:int;total_chunks:int;expected_sha256:str|None=None
@router.post('/applications/{aid}/uploads',status_code=201)
def begin_upload(aid:str,req:UploadStartIn,auth:AuthContext=Depends(current_auth)):
 u=wrap(lambda:runtime.applications.begin_upload(auth.account_id,aid,**req.model_dump()));return {'upload_id':u.id,'expires_at':u.expires_at.isoformat(),'total_chunks':u.total_chunks,'total_bytes':u.total_bytes}
@router.put('/applications/{aid}/uploads/{uid}/chunks/{index}')
async def upload_chunk(aid:str,uid:str,index:int,file:UploadFile=File(...),auth:AuthContext=Depends(current_auth)):
 payload=await file.read(1024*1024+1);return wrap(lambda:runtime.applications.upload_chunk(auth.account_id,aid,uid,index,payload))
@router.get('/applications/{aid}/uploads/{uid}')
def upload_status(aid:str,uid:str,auth:AuthContext=Depends(current_auth)):return wrap(lambda:runtime.applications.upload_status(auth.account_id,aid,uid))
@router.post('/applications/{aid}/uploads/{uid}/complete')
def complete_upload(aid:str,uid:str,auth:AuthContext=Depends(current_auth)):
 d=wrap(lambda:runtime.applications.complete_resumable_upload(auth.account_id,aid,uid));return {'id':d.id,'requirement_code':d.requirement_code,'sha256':d.sha256,'size_bytes':d.size_bytes,'state':d.state.value}
class ConsentIn(BaseModel):kind:str;policy_version:str;evidence:str
@router.get('/applications')
def mine(auth:AuthContext=Depends(current_auth)):return [out(x) for x in runtime.applications.list_mine(auth.account_id)]
@router.post('/applications/{aid}/consents',status_code=201)
def consent(aid:str,req:ConsentIn,auth:AuthContext=Depends(current_auth)):
 c=wrap(lambda:runtime.applications.accept_consent(auth.account_id,aid,req.kind,req.policy_version,req.evidence));return {'id':c.id,'kind':c.kind.value,'policy_version':c.policy_version,'accepted_at':c.accepted_at.isoformat(),'evidence_hash':c.evidence_hash}
@router.delete('/applications/{aid}/documents/{did}',status_code=204)
def delete_document(aid:str,did:str,auth:AuthContext=Depends(current_auth)):wrap(lambda:runtime.applications.delete_document(auth.account_id,aid,did))
@router.post('/applications/{aid}/withdraw')
def withdraw(aid:str,expected_version:int,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.applications.withdraw(auth.account_id,aid,expected_version)))
@router.get('/applications/{aid}/status')
def status(aid:str,auth:AuthContext=Depends(current_auth)):return wrap(lambda:runtime.admission_center.candidate_status(auth.account_id,aid))

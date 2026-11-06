from __future__ import annotations
import json
from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.publication.domain.model import RolloutMode,ReleaseState
from app.runtime import runtime
router=APIRouter()
class CreateRelease(BaseModel):
 editorial_item_id:str; editorial_revision_id:str; version_label:str=Field(min_length=1,max_length=120); placement:dict; audience:dict=Field(default_factory=dict); rollout_mode:RolloutMode=RolloutMode.ALL; rollout_percentage:int=Field(100,ge=1,le=100); premium_required:bool=True; offline_allowed:bool=True; scheduled_at:datetime|None=None
class Mutation(BaseModel): expected_version:int|None=None
def out(r): return {'id':r.id,'editorial_item_id':r.editorial_item_id,'editorial_revision_id':r.editorial_revision_id,'state':r.state.value,'version_label':r.version_label,'placement':json.loads(r.placement_json),'audience':json.loads(r.audience_json),'rollout_mode':r.rollout_mode.value,'rollout_percentage':r.rollout_percentage,'premium_required':r.premium_required,'offline_allowed':r.offline_allowed,'scheduled_at':r.scheduled_at,'published_at':r.published_at,'withdrawn_at':r.withdrawn_at,'row_version':r.row_version}
def wrap(fn):
 try:return fn()
 except PermissionError as e: raise HTTPException(403,str(e))
 except ValueError as e: raise HTTPException(409 if 'concurrent' in str(e) else 422,str(e))
@router.get('/dashboard')
def dashboard(auth:AuthContext=Depends(current_auth)): runtime.publication._actor(auth.account_id); return runtime.publication_repository.dashboard()
@router.get('/releases')
def releases(state:ReleaseState|None=None,auth:AuthContext=Depends(current_auth)): runtime.publication._actor(auth.account_id); return [out(x) for x in runtime.publication_repository.list(state)]
@router.post('/preflight')
def preflight(req:CreateRelease,auth:AuthContext=Depends(current_auth)): return wrap(lambda:runtime.publication.preflight(auth.account_id,req.editorial_item_id,req.editorial_revision_id))
@router.post('/releases')
def create(req:CreateRelease,auth:AuthContext=Depends(current_auth)): return out(wrap(lambda:runtime.publication.create(actor_id=auth.account_id,item_id=req.editorial_item_id,revision_id=req.editorial_revision_id,version_label=req.version_label,placement=req.placement,audience=req.audience,rollout_mode=req.rollout_mode,rollout_percentage=req.rollout_percentage,premium_required=req.premium_required,offline_allowed=req.offline_allowed,scheduled_at=req.scheduled_at)))
@router.post('/releases/{release_id}/publish')
def publish(release_id:str,req:Mutation=Mutation(),auth:AuthContext=Depends(current_auth)): return out(wrap(lambda:runtime.publication.publish(auth.account_id,release_id,req.expected_version)))
@router.post('/releases/{release_id}/withdraw')
def withdraw(release_id:str,req:Mutation=Mutation(),auth:AuthContext=Depends(current_auth)): return out(wrap(lambda:runtime.publication.withdraw(auth.account_id,release_id,req.expected_version)))
@router.get('/releases/{release_id}/snapshot')
def snapshot(release_id:str,auth:AuthContext=Depends(current_auth)):
 runtime.publication._actor(auth.account_id); x=runtime.publication_repository.snapshot(release_id)
 if not x: raise HTTPException(404,'snapshot_not_found')
 return {'release_id':x.release_id,'manifest_sha256':x.manifest_sha256,'manifest':json.loads(x.manifest_json),'created_at':x.created_at}

@router.get('/releases/{release_id}/verify')
def verify_snapshot(release_id:str,auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.publication.verify_snapshot(auth.account_id,release_id))

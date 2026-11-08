from __future__ import annotations
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from app.modules.identity.application.auth_context import AuthContext
from app.modules.identity.api.router import current_auth
from app.modules.editorial.domain.model import ContentKind, RiskLevel, RightsStatus, EditorialState, EditorialRole, AssignmentStage
from app.runtime import runtime

router=APIRouter()

class CreateItem(BaseModel):
    kind:ContentKind; title:str=Field(min_length=2,max_length=240); faculty_domain:str=Field(min_length=1,max_length=120); program:str=Field(min_length=1,max_length=160); level:str=Field(min_length=1,max_length=80); semester:str|None=None; risk:RiskLevel=RiskLevel.STANDARD; rights_status:RightsStatus=RightsStatus.UNKNOWN; rights_note:str=''; source_fingerprint:str=''
class UpdateItemBody(BaseModel):
    title:str|None=Field(default=None,min_length=2,max_length=240); faculty_domain:str|None=None; program:str|None=None; level:str|None=None; semester:str|None=None; risk:RiskLevel|None=None; rights_status:RightsStatus|None=None; rights_note:str|None=None; expected_version:int|None=None
class RevisionBody(BaseModel): payload:dict; source_fingerprint:str=''; ai_generated:bool=False; prompt_version:str|None=None; note:str=''; expected_version:int|None=None
class RestoreBody(BaseModel): note:str=''; expected_version:int|None=None
class ReviewBody(BaseModel): approve:bool; comment:str=''; checklist:dict[str,bool]=Field(default_factory=dict); quality_score:int|None=Field(default=None,ge=0,le=100); expected_version:int|None=None
class PublishBody(BaseModel): changelog:str=Field(min_length=1,max_length=2000); expected_version:int|None=None
class MutationBody(BaseModel): expected_version:int|None=None
class MemberBody(BaseModel): account_id:str; role:EditorialRole; active:bool=True
class SourceBody(BaseModel): filename:str=Field(min_length=1,max_length=260); checksum_sha256:str=Field(min_length=64,max_length=64); mime_type:str|None=None; size_bytes:int|None=None; storage_locator:str|None=None; ocr_confidence:float|None=Field(default=None,ge=0,le=1)
class AssignmentBody(BaseModel): assignee_id:str; stage:AssignmentStage; due_at:datetime|None=None

def _dt(v): return v.isoformat() if v else None
def _item(i): return {'id':i.id,'kind':i.kind.value,'title':i.title,'faculty_domain':i.faculty_domain,'program':i.program,'level':i.level,'semester':i.semester,'state':i.state.value,'risk':i.risk.value,'rights_status':i.rights_status.value,'rights_note':i.rights_note,'source_fingerprint':i.source_fingerprint,'created_by':i.created_by,'created_at':_dt(i.created_at),'updated_at':_dt(i.updated_at),'current_revision_id':i.current_revision_id,'published_revision_id':i.published_revision_id,'row_version':i.row_version}
def _revision(r):
    try: payload=json.loads(r.payload_json or '{}')
    except Exception: payload={}
    return {'id':r.id,'item_id':r.item_id,'revision_no':r.revision_no,'payload':payload,'source_fingerprint':r.source_fingerprint,'ai_generated':r.ai_generated,'prompt_version':r.prompt_version,'created_by':r.created_by,'created_at':_dt(r.created_at),'note':r.note}
def _source(s): return {'id':s.id,'item_id':s.item_id,'filename':s.filename,'mime_type':s.mime_type,'checksum_sha256':s.checksum_sha256,'size_bytes':s.size_bytes,'ocr_confidence':s.ocr_confidence,'human_verified':s.human_verified,'imported_by':s.imported_by,'created_at':_dt(s.created_at)}
def _review(r):
    try: checklist=json.loads(r.checklist_json or '{}')
    except Exception: checklist={}
    return {'id':r.id,'item_id':r.item_id,'revision_id':r.revision_id,'reviewer_id':r.reviewer_id,'decision':r.decision,'comment':r.comment,'created_at':_dt(r.created_at),'checklist':checklist,'quality_score':r.quality_score}
def _pub(p): return {'id':p.id,'item_id':p.item_id,'revision_id':p.revision_id,'publisher_id':p.publisher_id,'published_at':_dt(p.published_at),'changelog':p.changelog}
def _assignment(a): return {'id':a.id,'item_id':a.item_id,'stage':a.stage.value,'assignee_id':a.assignee_id,'assigned_by':a.assigned_by,'due_at':_dt(a.due_at),'active':a.active,'created_at':_dt(a.created_at)}
def _gate(g): return {'code':g.code,'passed':g.passed,'label':g.label,'detail':g.detail}
def _wrap(fn):
    try:return fn()
    except PermissionError as e: raise HTTPException(status_code=403,detail=str(e)) from e
    except ValueError as e:
        code=str(e)
        status=409 if 'concurrent_modification' in code else 422
        raise HTTPException(status_code=status,detail=code) from e

@router.get('/me')
def editorial_me(auth:AuthContext=Depends(current_auth)):
    m=_wrap(lambda:runtime.editorial._member(auth.account_id)); return {'account_id':m.account_id,'role':m.role.value,'active':m.active}

@router.get('/dashboard')
def dashboard(auth:AuthContext=Depends(current_auth)): return _wrap(lambda:runtime.editorial.dashboard(auth.account_id))

@router.get('/items/search')
def search_items(
    q:str|None=None,state:EditorialState|None=None,kind:ContentKind|None=None,risk:RiskLevel|None=None,rights_status:RightsStatus|None=None,
    offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=200),auth:AuthContext=Depends(current_auth)):
    rows,total=_wrap(lambda:runtime.editorial.search(auth.account_id,query=q,state=state,kind=kind,risk=risk,rights_status=rights_status,offset=offset,limit=limit))
    return {'items':[_item(x) for x in rows],'total':total,'offset':offset,'limit':limit}

@router.get('/items')
def items(state:EditorialState|None=None,auth:AuthContext=Depends(current_auth)):
    _wrap(lambda:runtime.editorial._member(auth.account_id)); return [_item(x) for x in runtime.editorial_repository.list_items(state=state,limit=500)]

@router.post('/items')
def create(req:CreateItem,auth:AuthContext=Depends(current_auth)): return _item(_wrap(lambda:runtime.editorial.create_item(actor_id=auth.account_id,**req.model_dump())))

@router.patch('/items/{item_id}')
def update_item(item_id:str,req:UpdateItemBody,auth:AuthContext=Depends(current_auth)):
    return _item(_wrap(lambda:runtime.editorial.update_item(actor_id=auth.account_id,item_id=item_id,**req.model_dump())))

@router.get('/items/{item_id}')
def detail(item_id:str,auth:AuthContext=Depends(current_auth)):
    d=_wrap(lambda:runtime.editorial.detail(auth.account_id,item_id))
    return {'item':_item(d['item']),'revisions':[_revision(x) for x in d['revisions']],'sources':[_source(x) for x in d['sources']],'reviews':[_review(x) for x in d['reviews']],'publications':[_pub(x) for x in d['publications']],'assignments':[_assignment(x) for x in d['assignments']],'review_gates':[_gate(x) for x in d['review_gates']],'publish_gates':[_gate(x) for x in d['publish_gates']],'audit':[{**x,'occurred_at':_dt(x.get('occurred_at'))} for x in d.get('audit',())]}

@router.get('/items/{item_id}/quality-gates')
def quality_gates(item_id:str,phase:str='review',auth:AuthContext=Depends(current_auth)): return [_gate(x) for x in _wrap(lambda:runtime.editorial.quality_gates(auth.account_id,item_id,phase))]

@router.post('/items/{item_id}/revisions')
def revision(item_id:str,req:RevisionBody,auth:AuthContext=Depends(current_auth)):
    r=_wrap(lambda:runtime.editorial.add_revision(actor_id=auth.account_id,item_id=item_id,**req.model_dump())); return _revision(r)

@router.post('/items/{item_id}/revisions/{revision_id}/restore')
def restore_revision(item_id:str,revision_id:str,req:RestoreBody,auth:AuthContext=Depends(current_auth)):
    r=_wrap(lambda:runtime.editorial.restore_revision(actor_id=auth.account_id,item_id=item_id,revision_id=revision_id,**req.model_dump())); return _revision(r)

@router.post('/items/{item_id}/submit-review')
def submit(item_id:str,req:MutationBody=MutationBody(),auth:AuthContext=Depends(current_auth)): return _item(_wrap(lambda:runtime.editorial.submit_review(actor_id=auth.account_id,item_id=item_id,expected_version=req.expected_version)))

@router.post('/items/{item_id}/review')
def review(item_id:str,req:ReviewBody,auth:AuthContext=Depends(current_auth)): return _item(_wrap(lambda:runtime.editorial.review(actor_id=auth.account_id,item_id=item_id,**req.model_dump())))

@router.post('/items/{item_id}/publish')
def publish(item_id:str,req:PublishBody,auth:AuthContext=Depends(current_auth)): return _item(_wrap(lambda:runtime.editorial.publish(actor_id=auth.account_id,item_id=item_id,**req.model_dump())))

@router.post('/items/{item_id}/archive')
def archive(item_id:str,req:MutationBody=MutationBody(),auth:AuthContext=Depends(current_auth)): return _item(_wrap(lambda:runtime.editorial.archive(actor_id=auth.account_id,item_id=item_id,expected_version=req.expected_version)))

@router.post('/items/{item_id}/assignments')
def assign(item_id:str,req:AssignmentBody,auth:AuthContext=Depends(current_auth)): return _assignment(_wrap(lambda:runtime.editorial.assign(actor_id=auth.account_id,item_id=item_id,**req.model_dump())))

@router.get('/members')
def members(auth:AuthContext=Depends(current_auth)):
    ms=_wrap(lambda:runtime.editorial.members(auth.account_id)); return [{'account_id':m.account_id,'role':m.role.value,'active':m.active} for m in ms]
@router.put('/members')
def set_member(req:MemberBody,auth:AuthContext=Depends(current_auth)):
    m=_wrap(lambda:runtime.editorial.set_member(actor_id=auth.account_id,account_id=req.account_id,role=req.role,active=req.active)); return {'account_id':m.account_id,'role':m.role.value,'active':m.active}

@router.post('/items/{item_id}/sources')
def add_source(item_id:str,req:SourceBody,auth:AuthContext=Depends(current_auth)):
    src=_wrap(lambda:runtime.editorial.add_source(actor_id=auth.account_id,item_id=item_id,**req.model_dump())); return _source(src)
@router.post('/sources/{source_id}/verify')
def verify_source(source_id:str,auth:AuthContext=Depends(current_auth)): return _source(_wrap(lambda:runtime.editorial.verify_source(actor_id=auth.account_id,source_id=source_id)))

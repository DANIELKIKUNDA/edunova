from __future__ import annotations
from dataclasses import asdict
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel
from app.modules.identity.application.auth_context import AuthContext
from app.modules.identity.api.router import current_auth
from app.runtime import runtime
router=APIRouter()
class CreateRunBody(BaseModel): document_id:str; requested_assets:list[str]|None=None
def dt(v):return v.isoformat() if v else None
def runj(r):
 d=asdict(r); d['state']=r.state.value
 for k in ('created_at','updated_at','started_at','completed_at','lease_expires_at'): d[k]=dt(getattr(r,k))
 return d
def wrap(fn):
 try:return fn()
 except PermissionError as e:raise HTTPException(403,detail=str(e)) from e
 except ValueError as e:raise HTTPException(422,detail=str(e)) from e
@router.post('/runs')
def create(req:CreateRunBody,auth:AuthContext=Depends(current_auth)):return runj(wrap(lambda:runtime.content_factory.create_run(auth.account_id,req.document_id,req.requested_assets)))
@router.post('/runs/{run_id}/process')
def process(run_id:str,auth:AuthContext=Depends(current_auth)):return runj(wrap(lambda:runtime.content_factory.process(auth.account_id,run_id)))
@router.post('/runs/{run_id}/cancel')
def cancel(run_id:str,auth:AuthContext=Depends(current_auth)):return runj(wrap(lambda:runtime.content_factory.cancel(auth.account_id,run_id)))
@router.get('/runs')
def runs(limit:int=Query(100,ge=1,le=500),auth:AuthContext=Depends(current_auth)):return [runj(x) for x in wrap(lambda:runtime.content_factory.list_runs(auth.account_id,limit))]
@router.get('/runs/{run_id}/review-package')
def review_package(run_id:str,auth:AuthContext=Depends(current_auth)):
 d=wrap(lambda:runtime.content_factory.review_package(auth.account_id,run_id)); return {'run':runj(d['run']),'items':[{'asset':{**asdict(x['asset']),'kind':x['asset'].kind.value,'created_at':dt(x['asset'].created_at)},'evidence':({**asdict(x['evidence']),'created_at':dt(x['evidence'].created_at)} if x['evidence'] else None)} for x in d['items']],'quality_gates':[{**asdict(x),'severity':x.severity.value,'created_at':dt(x.created_at)} for x in d['gates']],'publication_allowed':False,'required_next_state':'human_review'}
@router.get('/runs/{run_id}')
def detail(run_id:str,auth:AuthContext=Depends(current_auth)):
 d=wrap(lambda:runtime.content_factory.detail(auth.account_id,run_id)); return {'run':runj(d['run']),'assets':[{**asdict(x),'kind':x.kind.value,'created_at':dt(x.created_at)} for x in d['assets']],'evidence':[{**asdict(x),'created_at':dt(x.created_at)} for x in d['evidence']],'quality_gates':[{**asdict(x),'severity':x.severity.value,'created_at':dt(x.created_at)} for x in d['gates']]}

from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
router=APIRouter()
def call(f):
 try:return f()
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(400,str(e))
def data(x):return {k:(v.value if hasattr(v,'value') else v.isoformat() if isinstance(v,datetime) else v) for k,v in x.__dict__.items()}
class CreateIn(BaseModel):student_id:str;academic_registration_id:str;kind:str;title:str;supervisor_account_id:str
class TransitionIn(BaseModel):state:str;expected_version:int;reason:str
class RevisionIn(BaseModel):document_ref:str;sha256_hex:str;student_note:str=''
class ReviewIn(BaseModel):revision_id:str;decision:str;note:str=''
class DefenseIn(BaseModel):scheduled_at:datetime;room:str;chair_account_id:str;secretary_account_id:str
class ResultIn(BaseModel):decision:str;score:float|None=None;minutes_text:str
@router.post('/institutions/{iid}/projects')
def create(iid:str,q:CreateIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.research.create(auth.account_id,iid,**q.model_dump())))
@router.get('/institutions/{iid}/projects/{pid}')
def get(iid:str,pid:str,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.research.get(auth.account_id,iid,pid)))
@router.post('/institutions/{iid}/projects/{pid}/transition')
def transition(iid:str,pid:str,q:TransitionIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.research.transition(auth.account_id,iid,pid,**q.model_dump())))
@router.post('/institutions/{iid}/projects/{pid}/revisions')
def revision(iid:str,pid:str,q:RevisionIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.research.submit_revision(auth.account_id,iid,pid,**q.model_dump())))
@router.post('/institutions/{iid}/projects/{pid}/review')
def review(iid:str,pid:str,q:ReviewIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.research.review_revision(auth.account_id,iid,pid,**q.model_dump())))
@router.post('/institutions/{iid}/projects/{pid}/defense')
def defense(iid:str,pid:str,q:DefenseIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.research.schedule_defense(auth.account_id,iid,pid,**q.model_dump())))
@router.post('/institutions/{iid}/projects/{pid}/defense/result')
def result(iid:str,pid:str,q:ResultIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.research.record_defense(auth.account_id,iid,pid,**q.model_dump())))

from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException,Query
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
class CreateIn(BaseModel):student_id:str;kind:str;subject:str;details:str=''
class TransitionIn(BaseModel):state:str;expected_version:int;note:str=''
class AssignIn(BaseModel):assignee:str;expected_version:int
class FulfillIn(BaseModel):document_ref:str;sha256_hex:str;expected_version:int
@router.post('/institutions/{iid}/requests')
def create(iid:str,q:CreateIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.service_desk.create(auth.account_id,iid,**q.model_dump())))
@router.get('/institutions/{iid}/requests/{rid}')
def get(iid:str,rid:str,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.service_desk.get(auth.account_id,iid,rid)))
@router.get('/institutions/{iid}/students/{sid}/requests')
def mine(iid:str,sid:str,auth:AuthContext=Depends(current_auth)):return [data(x) for x in call(lambda:runtime.service_desk.mine(auth.account_id,iid,sid))]
@router.post('/institutions/{iid}/requests/{rid}/transition')
def transition(iid:str,rid:str,q:TransitionIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.service_desk.transition(auth.account_id,iid,rid,**q.model_dump())))
@router.post('/institutions/{iid}/requests/{rid}/assign')
def assign(iid:str,rid:str,q:AssignIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.service_desk.assign(auth.account_id,iid,rid,**q.model_dump())))
@router.post('/institutions/{iid}/requests/{rid}/fulfill')
def fulfill(iid:str,rid:str,q:FulfillIn,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.service_desk.fulfill(auth.account_id,iid,rid,**q.model_dump())))
@router.get('/institutions/{iid}/requests/{rid}/timeline')
def timeline(iid:str,rid:str,auth:AuthContext=Depends(current_auth)):return [data(x) for x in call(lambda:runtime.service_desk.timeline(auth.account_id,iid,rid))]

@router.get('/institutions/{iid}/requests')
def queue(iid:str,state:str|None=None,assigned_to:str|None=None,limit:int=Query(100,ge=1,le=200),offset:int=Query(0,ge=0),auth:AuthContext=Depends(current_auth)):
 return [data(x) for x in call(lambda:runtime.service_desk.queue(auth.account_id,iid,state,assigned_to,limit,offset))]
@router.get('/institutions/{iid}/requests-dashboard')
def dashboard(iid:str,auth:AuthContext=Depends(current_auth)):
 return call(lambda:runtime.service_desk.dashboard(auth.account_id,iid))

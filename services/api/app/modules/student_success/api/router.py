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
def data(x):return {k:(v.isoformat() if isinstance(v,datetime) else v) for k,v in x.__dict__.items()}
class Create(BaseModel):
 student_id:str
 category:str
 severity:str
 description:str
class Transition(BaseModel):
 state:str
 expected_version:int
 note:str
 assigned_to:str|None=None
@router.post('/institutions/{iid}/cases')
def create(iid:str,q:Create,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.student_success.create(auth.account_id,iid,q.student_id,q.category,q.severity,q.description)))
@router.get('/institutions/{iid}/cases')
def list_cases(iid:str,student_id:str|None=None,auth:AuthContext=Depends(current_auth)):return [data(x) for x in call(lambda:runtime.student_success.list(auth.account_id,iid,student_id))]
@router.get('/institutions/{iid}/cases/{cid}')
def get(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.student_success.get(auth.account_id,iid,cid)))
@router.post('/institutions/{iid}/cases/{cid}/transition')
def transition(iid:str,cid:str,q:Transition,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.student_success.transition(auth.account_id,iid,cid,**q.model_dump())))
@router.get('/institutions/{iid}/cases/{cid}/timeline')
def timeline(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):return [data(x) for x in call(lambda:runtime.student_success.timeline(auth.account_id,iid,cid))]

@router.post('/institutions/{iid}/students/{sid}/scan')
def scan(iid:str,sid:str,auth:AuthContext=Depends(current_auth)):
 r=call(lambda:runtime.student_success.scan(auth.account_id,iid,sid));return {**r,'created':[data(x) for x in r['created']],'existing':[data(x) for x in r['existing']]}

class PlanCreate(BaseModel):
 objective:str
 target_date:str|None=None
class ActionCreate(BaseModel):
 title:str
 assigned_to:str
 due_date:str|None=None
class CompleteAction(BaseModel):
 expected_version:int
 note:str
class ClosePlan(BaseModel):
 expected_version:int
 note:str
@router.post('/institutions/{iid}/cases/{cid}/plan')
def create_plan(iid:str,cid:str,q:PlanCreate,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.student_success.create_plan(auth.account_id,iid,cid,**q.model_dump())))
@router.get('/institutions/{iid}/cases/{cid}/plan')
def get_plan(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.student_success.get_plan(auth.account_id,iid,cid)))
@router.post('/institutions/{iid}/cases/{cid}/plan/actions')
def add_action(iid:str,cid:str,q:ActionCreate,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.student_success.add_action(auth.account_id,iid,cid,**q.model_dump())))
@router.get('/institutions/{iid}/cases/{cid}/plan/actions')
def list_actions(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):return [data(x) for x in call(lambda:runtime.student_success.list_actions(auth.account_id,iid,cid))]
@router.post('/institutions/{iid}/cases/{cid}/plan/actions/{aid}/complete')
def complete_action(iid:str,cid:str,aid:str,q:CompleteAction,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.student_success.complete_action(auth.account_id,iid,cid,aid,**q.model_dump())))
@router.post('/institutions/{iid}/cases/{cid}/plan/complete')
def close_plan(iid:str,cid:str,q:ClosePlan,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.student_success.close_plan(auth.account_id,iid,cid,**q.model_dump())))

@router.post('/institutions/{iid}/cases/{cid}/plan/reassess')
def reassess_plan(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):return data(call(lambda:runtime.student_success.reassess_plan(auth.account_id,iid,cid)))
@router.get('/institutions/{iid}/cases/{cid}/plan/assessments')
def assessments(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):return [data(x) for x in call(lambda:runtime.student_success.assessments(auth.account_id,iid,cid))]
@router.get('/institutions/{iid}/dashboard')
def dashboard(iid:str,auth:AuthContext=Depends(current_auth)):return call(lambda:runtime.student_success.dashboard(auth.account_id,iid))

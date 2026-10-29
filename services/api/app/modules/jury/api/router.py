from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
router=APIRouter()
def call(fn):
    try:return fn()
    except PermissionError as e:raise HTTPException(403,str(e))
    except ValueError as e:raise HTTPException(400,str(e))
def data(x):
    return {k:(v.value if hasattr(v,'value') else v.isoformat() if isinstance(v,datetime) else v) for k,v in x.__dict__.items()}
class CreateIn(BaseModel):
    cohort_id:str;academic_year_id:str;curriculum_id:str;name:str;min_credits:float;quorum:int=1
class EvaluateIn(BaseModel):
    student_id:str;reason:str
class TransitionIn(BaseModel):
    expected_version:int
class MemberIn(BaseModel):
    account_id:str;role:str='member';voting:bool=True
class VoteIn(BaseModel):
    student_id:str;choice:str;rationale:str
@router.post('/institutions/{iid}/sessions')
def create(iid:str,q:CreateIn,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.jury.create(auth.account_id,iid,**q.model_dump())))
@router.get('/institutions/{iid}/sessions/{sid}')
def get(iid:str,sid:str,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.jury.get(auth.account_id,iid,sid)))
@router.post('/institutions/{iid}/sessions/{sid}/evaluate')
def evaluate(iid:str,sid:str,q:EvaluateIn,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.jury.evaluate(auth.account_id,iid,sid,q.student_id,q.reason)))
@router.post('/institutions/{iid}/sessions/{sid}/lock')
def lock(iid:str,sid:str,q:TransitionIn,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.jury.lock(auth.account_id,iid,sid,q.expected_version)))
@router.post('/institutions/{iid}/sessions/{sid}/publish')
def publish(iid:str,sid:str,q:TransitionIn,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.jury.publish(auth.account_id,iid,sid,q.expected_version)))
@router.get('/institutions/{iid}/sessions/{sid}/outcomes')
def outcomes(iid:str,sid:str,auth:AuthContext=Depends(current_auth)):
    return [data(x) for x in call(lambda:runtime.jury.outcomes(auth.account_id,iid,sid))]

@router.post('/institutions/{iid}/sessions/{sid}/members')
def add_member(iid:str,sid:str,q:MemberIn,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.jury.add_member(auth.account_id,iid,sid,q.account_id,q.role,q.voting)))
@router.post('/institutions/{iid}/sessions/{sid}/votes')
def vote(iid:str,sid:str,q:VoteIn,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.jury.vote(auth.account_id,iid,sid,q.student_id,q.choice,q.rationale)))
@router.post('/institutions/{iid}/sessions/{sid}/minutes')
def minutes(iid:str,sid:str,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.jury.generate_minutes(auth.account_id,iid,sid)))

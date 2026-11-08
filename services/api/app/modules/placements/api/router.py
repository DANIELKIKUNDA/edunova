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
def data(x):return {k:(v.value if hasattr(v,'value') else v.isoformat() if isinstance(v,datetime) else v) for k,v in x.__dict__.items()}
class CreateIn(BaseModel):
    student_id:str;academic_registration_id:str;host_name:str;supervisor_account_id:str;start_date:str;end_date:str
class TransitionIn(BaseModel):
    state:str;expected_version:int;reason:str
class LogIn(BaseModel):
    activity_date:str;description:str
@router.post('/institutions/{iid}/placements')
def create(iid:str,q:CreateIn,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.placements.create(auth.account_id,iid,**q.model_dump())))
@router.get('/institutions/{iid}/placements/{pid}')
def get(iid:str,pid:str,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.placements.get(auth.account_id,iid,pid)))
@router.post('/institutions/{iid}/placements/{pid}/transition')
def transition(iid:str,pid:str,q:TransitionIn,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.placements.transition(auth.account_id,iid,pid,**q.model_dump())))
@router.post('/institutions/{iid}/placements/{pid}/logs')
def log(iid:str,pid:str,q:LogIn,auth:AuthContext=Depends(current_auth)):
    return data(call(lambda:runtime.placements.log(auth.account_id,iid,pid,**q.model_dump())))
@router.get('/institutions/{iid}/placements/{pid}/logs')
def logs(iid:str,pid:str,auth:AuthContext=Depends(current_auth)):
    return [data(x) for x in call(lambda:runtime.placements.logs(auth.account_id,iid,pid))]

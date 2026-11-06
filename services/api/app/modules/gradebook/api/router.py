from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
router=APIRouter()
def wrap(f):
 try:return f()
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(409 if 'concurrent' in str(e) else 400,str(e))
def ser(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 d={k:getattr(x,k) for k in x.__dataclass_fields__}
 for k,v in list(d.items()):
  if hasattr(v,'value'):d[k]=v.value
  elif isinstance(v,datetime):d[k]=v.isoformat()
 return d
class CreateIn(BaseModel):title:str='Résultats académiques';pass_percent:float=50
class ComponentIn(BaseModel):title:str;kind:str;weight_percent:float;max_score:float;source_assignment_id:str|None=None
class VersionIn(BaseModel):expected_version:int
class MarkIn(BaseModel):student_account_id:str;score:float|None=None;validated:bool=True;expected_version:int|None=None;source_ref:str|None=None;attendance:str='present';note:str|None=None
class UnlockIn(BaseModel):expected_version:int;reason:str
class SessionIn(BaseModel):kind:str='regular';starts_at:datetime;ends_at:datetime;room:str|None=None;instructions:str|None=None
class RetractIn(BaseModel):expected_version:int;reason:str
class SessionTransitionIn(BaseModel):expected_version:int;target:str;reason:str|None=None
@router.post('/institutions/{iid}/offerings/{oid}/gradebooks')
def create(iid:str,oid:str,q:CreateIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.create(auth.account_id,iid,oid,**q.model_dump())))
@router.post('/institutions/{iid}/gradebooks/{gid}/components')
def component(iid:str,gid:str,q:ComponentIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.add_component(auth.account_id,iid,gid,**q.model_dump())))
@router.post('/institutions/{iid}/gradebooks/{gid}/open')
def open_book(iid:str,gid:str,q:VersionIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.open(auth.account_id,iid,gid,q.expected_version)))
@router.put('/institutions/{iid}/gradebooks/{gid}/components/{cid}/mark')
def mark(iid:str,gid:str,cid:str,q:MarkIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.set_mark(auth.account_id,iid,gid,cid,q.student_account_id,score=q.score,validate=q.validated,expected_version=q.expected_version,source_ref=q.source_ref,attendance=q.attendance,note=q.note)))
@router.post('/institutions/{iid}/gradebooks/{gid}/components/{cid}/import-assignment-results')
def import_assignment(iid:str,gid:str,cid:str,auth:AuthContext=Depends(current_auth)):return {'imported':wrap(lambda:runtime.gradebook.import_assignment_results(auth.account_id,iid,gid,cid))}
@router.get('/institutions/{iid}/gradebooks/{gid}/my-result')
def my_result(iid:str,gid:str,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.result(auth.account_id,iid,gid)))
@router.get('/institutions/{iid}/gradebooks/{gid}/students/{sid}/result')
def student_result(iid:str,gid:str,sid:str,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.result(auth.account_id,iid,gid,sid)))
@router.post('/institutions/{iid}/gradebooks/{gid}/publish')
def publish(iid:str,gid:str,q:VersionIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.publish(auth.account_id,iid,gid,q.expected_version)))
@router.post('/institutions/{iid}/gradebooks/{gid}/retract')
def retract(iid:str,gid:str,q:RetractIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.retract(auth.account_id,iid,gid,q.expected_version,q.reason)))

@router.post('/institutions/{iid}/gradebooks/{gid}/lock')
def lock(iid:str,gid:str,q:VersionIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.lock(auth.account_id,iid,gid,q.expected_version)))
@router.post('/institutions/{iid}/gradebooks/{gid}/unlock-exceptionally')
def unlock(iid:str,gid:str,q:UnlockIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.unlock_exceptionally(auth.account_id,iid,gid,q.expected_version,q.reason)))
@router.post('/institutions/{iid}/gradebooks/{gid}/components/{cid}/exam-sessions')
def exam_session(iid:str,gid:str,cid:str,q:SessionIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.create_exam_session(auth.account_id,iid,gid,cid,**q.model_dump())))

@router.post('/institutions/{iid}/exam-sessions/{sid}/transition')
def transition_session(iid:str,sid:str,q:SessionTransitionIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.gradebook.transition_exam_session(auth.account_id,iid,sid,q.expected_version,q.target,q.reason)))

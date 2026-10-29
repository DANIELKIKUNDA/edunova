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
 except ValueError as e:raise HTTPException(400,str(e))
def ser(x):
 d={k:getattr(x,k) for k in x.__dataclass_fields__}
 for k,v in list(d.items()):
  if hasattr(v,'value'):d[k]=v.value
  elif isinstance(v,datetime):d[k]=v.isoformat()
 return d
class BindIn(BaseModel):curriculum_course_id:str
@router.post('/institutions/{iid}/offerings/{oid}/curriculum')
def bind(iid:str,oid:str,q:BindIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.academic_delivery.bind_offering(auth.account_id,iid,oid,q.curriculum_course_id)))
@router.get('/institutions/{iid}/offerings/{oid}/me/eligibility')
def eligibility(iid:str,oid:str,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.academic_delivery.assert_student_eligible(auth.account_id,iid,oid)))

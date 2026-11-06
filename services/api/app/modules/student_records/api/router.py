from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
def w(f):
 try:return f()
 except (ValueError,PermissionError) as e:raise HTTPException(422 if isinstance(e,ValueError) else 403,str(e)) from e
def so(s):return {**s.__dict__,'state':s.state.value,'created_at':s.created_at.isoformat(),'updated_at':s.updated_at.isoformat()}
def dossier(d):return {'student':so(d['student']),'registrations':[{**x.__dict__,'state':x.state.value,'registered_at':x.registered_at.isoformat()} for x in d['registrations']],'courses':[{**x.__dict__,'state':x.state.value,'created_at':x.created_at.isoformat()} for x in d['courses']],'events':[{**x.__dict__,'created_at':x.created_at.isoformat()} for x in d['events']],'administrative_history':[{**x.__dict__,'created_at':x.created_at.isoformat()} for x in d['administrative_history']]}
class MatriculateIn(BaseModel):review_id:str;cohort_id:str
class StateIn(BaseModel):expected_version:int;state:str;note:str|None=None
@router.post('/institutions/{iid}/students')
def matriculate(iid:str,req:MatriculateIn,auth:AuthContext=Depends(current_auth)):return so(w(lambda:runtime.student_records.matriculate(auth.account_id,iid,req.review_id,req.cohort_id)))
@router.get('/institutions/{iid}/students/me')
def me(iid:str,auth:AuthContext=Depends(current_auth)):return dossier(w(lambda:runtime.student_records.my_dossier(auth.account_id,iid)))
@router.get('/institutions/{iid}/students/{sid}')
def get(iid:str,sid:str,auth:AuthContext=Depends(current_auth)):return dossier(w(lambda:runtime.student_records.dossier(auth.account_id,iid,sid)))
@router.post('/institutions/{iid}/students/{sid}/state')
def state(iid:str,sid:str,req:StateIn,auth:AuthContext=Depends(current_auth)):return so(w(lambda:runtime.student_records.change_state(auth.account_id,iid,sid,req.expected_version,req.state,req.note)))

class RegisterYearIn(BaseModel):cohort_id:str
@router.post('/institutions/{iid}/students/{sid}/registrations')
def register_year(iid:str,sid:str,req:RegisterYearIn,auth:AuthContext=Depends(current_auth)):
 x=w(lambda:runtime.student_records.register_academic_year(auth.account_id,iid,sid,req.cohort_id));return {**x.__dict__,'state':x.state.value,'registered_at':x.registered_at.isoformat()}

class IdentityCorrectionIn(BaseModel):
 expected_version:int;reason:str;given_names:str|None=None;family_name:str|None=None;birth_date:str|None=None;nationality_code:str|None=None;email:str|None=None;phone_number:str|None=None
@router.post('/institutions/{iid}/students/{sid}/identity-corrections')
def identity_correction(iid:str,sid:str,req:IdentityCorrectionIn,auth:AuthContext=Depends(current_auth)):
 d=req.model_dump();expected=d.pop('expected_version');reason=d.pop('reason');return so(w(lambda:runtime.student_records.correct_identity(auth.account_id,iid,sid,expected,reason,**d)))
class RegistrationStateIn(BaseModel):expected_version:int;state:str;reason:str
@router.post('/institutions/{iid}/students/{sid}/registrations/{rid}/state')
def registration_state(iid:str,sid:str,rid:str,req:RegistrationStateIn,auth:AuthContext=Depends(current_auth)):
 x=w(lambda:runtime.student_records.change_registration_state(auth.account_id,iid,sid,rid,req.expected_version,req.state,req.reason));return {**x.__dict__,'state':x.state.value,'registered_at':x.registered_at.isoformat()}

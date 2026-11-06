from datetime import date
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.campus.domain.model import *
from app.runtime import runtime
router=APIRouter()
class InstitutionIn(BaseModel):name:str=Field(min_length=2,max_length=240);slug:str=Field(min_length=2,max_length=96);legal_name:str='';country_code:str=Field(default='CD',min_length=2,max_length=2);city:str|None=None;logo_url:str|None=None
class InstitutionPatch(BaseModel):expected_version:int=Field(ge=1);name:str|None=None;legal_name:str|None=None;city:str|None=None;logo_url:str|None=None;state:InstitutionState|None=None
class UnitIn(BaseModel):kind:UnitKind;name:str=Field(min_length=2,max_length=240);code:str=Field(min_length=1,max_length=64);parent_id:str|None=None
class PeriodIn(BaseModel):kind:PeriodKind;name:str=Field(min_length=2,max_length=160);starts_on:date;ends_on:date;parent_id:str|None=None
class InviteIn(BaseModel):account_id:str=Field(min_length=1,max_length=64);role:CampusRole;unit_id:str|None=None
class StateIn(BaseModel):state:MembershipState;expected_version:int=Field(ge=1)
class RoleIn(BaseModel):role:CampusRole;expected_version:int=Field(ge=1)
class CohortIn(BaseModel):program_unit_id:str;academic_period_id:str;name:str=Field(min_length=1,max_length=160);level:str=Field(min_length=1,max_length=80)
class EnrollIn(BaseModel):student_account_id:str

def wrap(fn):
 try:return fn()
 except PermissionError as e:raise HTTPException(403,str(e)) from e
 except ValueError as e:raise HTTPException(409 if ('concurrent' in str(e) or 'exists' in str(e) or 'already' in str(e)) else 422,str(e)) from e
def inst(x):return {'id':x.id,'slug':x.slug,'name':x.name,'legal_name':x.legal_name,'country_code':x.country_code,'city':x.city,'logo_url':x.logo_url,'state':x.state.value,'row_version':x.row_version}
def unit(x):return {'id':x.id,'institution_id':x.institution_id,'kind':x.kind.value,'name':x.name,'code':x.code,'parent_id':x.parent_id,'active':x.active,'row_version':x.row_version}
def period(x):return {'id':x.id,'kind':x.kind.value,'name':x.name,'starts_on':x.starts_on.isoformat(),'ends_on':x.ends_on.isoformat(),'parent_id':x.parent_id,'active':x.active,'row_version':x.row_version}
def member(x):return {'id':x.id,'account_id':x.account_id,'role':x.role.value,'state':x.state.value,'unit_id':x.unit_id,'joined_at':x.joined_at.isoformat() if x.joined_at else None,'row_version':x.row_version}
def cohort(x):return {'id':x.id,'program_unit_id':x.program_unit_id,'academic_period_id':x.academic_period_id,'name':x.name,'level':x.level,'active':x.active,'row_version':x.row_version}
@router.get('/me/institutions')
def mine(auth:AuthContext=Depends(current_auth)):return [{'institution':inst(i),'membership':member(m)} for i,m in runtime.campus.my_institutions(auth.account_id)]
@router.post('/institutions')
def create(req:InstitutionIn,auth:AuthContext=Depends(current_auth)):return inst(wrap(lambda:runtime.campus.create_institution(auth.account_id,**req.model_dump())))
@router.get('/institutions/{iid}')
def get(iid:str,auth:AuthContext=Depends(current_auth)):return inst(wrap(lambda:runtime.campus.institution(auth.account_id,iid)))
@router.patch('/institutions/{iid}')
def patch(iid:str,req:InstitutionPatch,auth:AuthContext=Depends(current_auth)):return inst(wrap(lambda:runtime.campus.update_institution(auth.account_id,iid,**req.model_dump())))
@router.get('/institutions/{iid}/overview')
def overview(iid:str,auth:AuthContext=Depends(current_auth)):return wrap(lambda:runtime.campus.overview(auth.account_id,iid))
@router.post('/institutions/{iid}/units')
def add_unit(iid:str,req:UnitIn,auth:AuthContext=Depends(current_auth)):return unit(wrap(lambda:runtime.campus.add_unit(auth.account_id,iid,**req.model_dump())))
@router.get('/institutions/{iid}/units')
def units(iid:str,auth:AuthContext=Depends(current_auth)):
 wrap(lambda:runtime.campus.membership(auth.account_id,iid));return [unit(x) for x in runtime.campus_repo.list_units(iid)]
@router.post('/institutions/{iid}/periods')
def add_period(iid:str,req:PeriodIn,auth:AuthContext=Depends(current_auth)):return period(wrap(lambda:runtime.campus.add_period(auth.account_id,iid,**req.model_dump())))
@router.get('/institutions/{iid}/periods')
def periods(iid:str,auth:AuthContext=Depends(current_auth)):
 wrap(lambda:runtime.campus.membership(auth.account_id,iid));return [period(x) for x in runtime.campus_repo.list_periods(iid)]
@router.post('/institutions/{iid}/members/invitations')
def invite(iid:str,req:InviteIn,auth:AuthContext=Depends(current_auth)):return member(wrap(lambda:runtime.campus.invite_member(auth.account_id,iid,**req.model_dump())))
@router.post('/institutions/{iid}/members/accept')
def accept(iid:str,auth:AuthContext=Depends(current_auth)):return member(wrap(lambda:runtime.campus.accept_invitation(auth.account_id,iid)))
@router.patch('/institutions/{iid}/members/{account_id}/state')
def member_state(iid:str,account_id:str,req:StateIn,auth:AuthContext=Depends(current_auth)):return member(wrap(lambda:runtime.campus.set_member_state(auth.account_id,iid,account_id,req.state,req.expected_version)))
@router.patch('/institutions/{iid}/members/{account_id}/role')
def member_role(iid:str,account_id:str,req:RoleIn,auth:AuthContext=Depends(current_auth)):return member(wrap(lambda:runtime.campus.set_member_role(auth.account_id,iid,account_id,req.role,req.expected_version)))
@router.get('/institutions/{iid}/members')
def members(iid:str,auth:AuthContext=Depends(current_auth)):
 return [member(x) for x in wrap(lambda:runtime.campus.list_members(auth.account_id,iid))]
@router.post('/institutions/{iid}/cohorts')
def add_cohort(iid:str,req:CohortIn,auth:AuthContext=Depends(current_auth)):return cohort(wrap(lambda:runtime.campus.create_cohort(auth.account_id,iid,**req.model_dump())))
@router.get('/institutions/{iid}/cohorts')
def cohorts(iid:str,auth:AuthContext=Depends(current_auth)):
 wrap(lambda:runtime.campus.membership(auth.account_id,iid));return [cohort(x) for x in runtime.campus_repo.list_cohorts(iid)]
@router.post('/institutions/{iid}/cohorts/{cid}/enrollments')
def enroll(iid:str,cid:str,req:EnrollIn,auth:AuthContext=Depends(current_auth)):
 x=wrap(lambda:runtime.campus.enroll(auth.account_id,iid,cohort_id=cid,student_account_id=req.student_account_id));return {'id':x.id,'cohort_id':x.cohort_id,'student_account_id':x.student_account_id,'active':x.active}

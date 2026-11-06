from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
def m(x):return {**x.__dict__,'state':x.state.value,'root_cause':x.root_cause.value}
def p(x):return {**x.__dict__,'steps':[{**z.__dict__,'kind':z.kind.value,'intervention':z.intervention.value} for z in x.steps]}
@router.post('/diagnose')
def diagnose(auth:AuthContext=Depends(current_auth)):return {'items':[m(x) for x in runtime.remediation.diagnose(auth.account_id)]}
@router.get('/dashboard')
def dashboard(auth:AuthContext=Depends(current_auth)):
 d=runtime.remediation.dashboard(auth.account_id);return {**d,'priority':[m(x) for x in d['priority']],'paths':[p(x) for x in d['paths']]}
@router.post('/misconceptions/{id}/path')
def create_path(id:str,auth:AuthContext=Depends(current_auth)):return p(runtime.remediation.create_path(auth.account_id,id))
class VersionIn(BaseModel):row_version:int=Field(ge=1)
@router.post('/paths/{id}/advance')
def advance(id:str,b:VersionIn,auth:AuthContext=Depends(current_auth)):return p(runtime.remediation.advance(auth.account_id,id,b.row_version))
class VerifyIn(VersionIn):score:int=Field(ge=0,le=100)
@router.post('/paths/{id}/verify')
def verify(id:str,b:VerifyIn,auth:AuthContext=Depends(current_auth)):return runtime.remediation.verify(auth.account_id,id,b.score,b.row_version).__dict__

@router.get('/misconceptions/{id}/tutor-decision')
def tutor_decision(id:str,auth:AuthContext=Depends(current_auth)):
 d=runtime.remediation.tutor_decision(auth.account_id,id);return {**d.__dict__,'intervention':d.intervention.value}
class PracticeIn(VersionIn):
 score:int=Field(ge=0,le=100);used_hints:int=Field(ge=0,le=20);transfer:bool=False;mutation_id:str|None=None
@router.post('/paths/{id}/practice')
def practice(id:str,b:PracticeIn,auth:AuthContext=Depends(current_auth)):return p(runtime.remediation.record_practice(auth.account_id,id,b.score,b.used_hints,b.row_version,b.transfer,b.mutation_id))
@router.post('/paths/{id}/retention-check')
def retention(id:str,b:VerifyIn,auth:AuthContext=Depends(current_auth)):return runtime.remediation.retention_check(auth.account_id,id,b.score,b.row_version)

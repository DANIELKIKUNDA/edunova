from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.trust_governance.domain.model import PrivacyRequestKind
from app.runtime import runtime
router=APIRouter()
class ConsentIn(BaseModel): purpose:str=Field(min_length=2,max_length=128); policy_version:str=Field(min_length=1,max_length=64); granted:bool
class PrivacyIn(BaseModel): kind:PrivacyRequestKind
@router.post('/consents',status_code=201)
def consent(req:ConsentIn,auth:AuthContext=Depends(current_auth)):
 x=runtime.trust_governance.record_consent(account_id=auth.account_id,**req.model_dump()); return {**x.__dict__,'state':x.state.value}
@router.get('/consents')
def history(auth:AuthContext=Depends(current_auth)):
 return [{**x.__dict__,'state':x.state.value} for x in runtime.trust_governance.consent_history(auth.account_id)]
@router.post('/privacy-requests',status_code=202)
def privacy(req:PrivacyIn,auth:AuthContext=Depends(current_auth)):
 x=runtime.trust_governance.request_privacy_action(account_id=auth.account_id,kind=req.kind); return {'id':x.id,'kind':x.kind.value,'state':x.state.value,'requested_at':x.requested_at}
@router.get('/security-ledger/verify')
def verify(auth:AuthContext=Depends(current_auth)):
 return {'valid':runtime.trust_governance.verify_ledger()}
class MfaCodeIn(BaseModel): code:str=Field(min_length=6,max_length=6)
@router.post('/mfa/enroll')
def mfa_enroll(auth:AuthContext=Depends(current_auth)):
 secret=runtime.trust_governance.begin_mfa_enrollment(auth.account_id)
 return {'secret':secret,'type':'totp','issuer':'EduNova','account_id':auth.account_id}
@router.post('/mfa/confirm')
def mfa_confirm(req:MfaCodeIn,auth:AuthContext=Depends(current_auth)):
 try: runtime.trust_governance.confirm_mfa(auth.account_id,req.code)
 except ValueError as e: raise HTTPException(status_code=422,detail=str(e))
 return {'enabled':True}
class RetentionIn(BaseModel): data_class:str=Field(min_length=2,max_length=64); retention_days:int=Field(ge=1,le=3650); policy_version:str=Field(min_length=1,max_length=64)
@router.post('/institutions/{institution_id}/retention',status_code=201)
def retention(institution_id:str,req:RetentionIn,auth:AuthContext=Depends(current_auth)):
 from app.modules.campus.domain.model import CampusRole
 try:
  runtime.campus.membership(auth.account_id,institution_id,{CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN})
  x=runtime.trust_governance.set_retention_policy(actor_id=auth.account_id,institution_id=institution_id,**req.model_dump())
 except PermissionError as e: raise HTTPException(status_code=403,detail=str(e))
 except ValueError as e: raise HTTPException(status_code=422,detail=str(e))
 return x.__dict__

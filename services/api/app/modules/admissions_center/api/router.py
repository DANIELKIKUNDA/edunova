from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
def w(f):
 try:return f()
 except ValueError as e:raise HTTPException(422,str(e)) from e
def out(x):return {**x.__dict__,'state':x.state.value,'created_at':x.created_at.isoformat(),'updated_at':x.updated_at.isoformat(),'decided_at':x.decided_at.isoformat() if x.decided_at else None}
class AssignIn(BaseModel):assignee:str;expected_version:int
class DocIn(BaseModel):state:str;note:str|None=None
class ActionIn(BaseModel):expected_version:int;reason:str|None=None
class DecisionIn(BaseModel):expected_version:int;decision:str;reason:str|None=None
@router.post('/institutions/{iid}/applications/{aid}/intake')
def intake(iid:str,aid:str,auth:AuthContext=Depends(current_auth)):return out(w(lambda:runtime.admission_center.intake(auth.account_id,iid,aid)))
@router.get('/institutions/{iid}/reviews')
def listing(iid:str,state:str|None=None,auth:AuthContext=Depends(current_auth)):return [out(x) for x in w(lambda:runtime.admission_center.list(auth.account_id,iid,state))]
@router.post('/institutions/{iid}/reviews/{rid}/assign')
def assign(iid:str,rid:str,req:AssignIn,auth:AuthContext=Depends(current_auth)):return out(w(lambda:runtime.admission_center.assign(auth.account_id,iid,rid,req.assignee,req.expected_version)))
@router.put('/institutions/{iid}/reviews/{rid}/documents/{did}')
def doc(iid:str,rid:str,did:str,req:DocIn,auth:AuthContext=Depends(current_auth)):r=w(lambda:runtime.admission_center.review_document(auth.account_id,iid,rid,did,req.state,req.note));return {**r.__dict__,'state':r.state.value,'reviewed_at':r.reviewed_at.isoformat()}
@router.post('/institutions/{iid}/reviews/{rid}/complete')
def complete(iid:str,rid:str,req:ActionIn,auth:AuthContext=Depends(current_auth)):return out(w(lambda:runtime.admission_center.mark_complete(auth.account_id,iid,rid,req.expected_version)))
@router.post('/institutions/{iid}/reviews/{rid}/request-correction')
def correction(iid:str,rid:str,req:ActionIn,auth:AuthContext=Depends(current_auth)):return out(w(lambda:runtime.admission_center.request_correction(auth.account_id,iid,rid,req.expected_version,req.reason or '')))
@router.post('/institutions/{iid}/reviews/{rid}/decision')
def decision(iid:str,rid:str,req:DecisionIn,auth:AuthContext=Depends(current_auth)):return out(w(lambda:runtime.admission_center.decide(auth.account_id,iid,rid,req.expected_version,req.decision,req.reason)))
class CommitteeIn(BaseModel):
 campaign_id:str;name:str;chair_account_id:str;members:list[str]=[];quorum:int=1
class VoteIn(BaseModel):recommendation:str;note:str|None=None
@router.get('/institutions/{iid}/dashboard')
def dashboard(iid:str,auth:AuthContext=Depends(current_auth)):return w(lambda:runtime.admission_center.dashboard(auth.account_id,iid))
@router.post('/institutions/{iid}/committees')
def committee(iid:str,req:CommitteeIn,auth:AuthContext=Depends(current_auth)):return w(lambda:runtime.admission_center.create_committee(auth.account_id,iid,req.campaign_id,req.name,req.chair_account_id,req.members,req.quorum)).__dict__
@router.post('/institutions/{iid}/committees/{cid}/reviews/{rid}/vote')
def vote(iid:str,cid:str,rid:str,req:VoteIn,auth:AuthContext=Depends(current_auth)):return w(lambda:runtime.admission_center.vote(auth.account_id,iid,cid,rid,req.recommendation,req.note)).__dict__
@router.get('/institutions/{iid}/committees/{cid}/reviews/{rid}/tally')
def tally(iid:str,cid:str,rid:str,auth:AuthContext=Depends(current_auth)):return w(lambda:runtime.admission_center.committee_tally(auth.account_id,iid,cid,rid))
@router.get('/institutions/{iid}/reviews/{rid}/timeline')
def timeline(iid:str,rid:str,auth:AuthContext=Depends(current_auth)):return [x.__dict__ for x in w(lambda:runtime.admission_center.timeline(auth.account_id,iid,rid))]

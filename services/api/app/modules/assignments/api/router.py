from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.assignments.domain.model import AssignmentKind
router=APIRouter()
def wrap(f):
 try:return f()
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(409 if 'concurrent' in str(e) else 400,str(e))
def ser(x):
 d={k:getattr(x,k) for k in x.__dataclass_fields__}
 for k,v in list(d.items()):
  if hasattr(v,'value'):d[k]=v.value
  elif isinstance(v,datetime):d[k]=v.isoformat()
 return d
class AssignmentIn(BaseModel):title:str;instructions:str='';kind:AssignmentKind=AssignmentKind.INDIVIDUAL;opens_at:datetime|None=None;due_at:datetime;closes_at:datetime|None=None;max_attempts:int=1;max_score:float=20
class CriterionIn(BaseModel):label:str;description:str='';max_points:float
class PublishIn(BaseModel):expected_version:int
class SubmitIn(BaseModel):text_content:str='';attachment_refs:list[str]=[];group_key:str|None=None
class ProposalIn(BaseModel):proposed_score:float|None=None;feedback:str='';criterion_scores:list[str]=[];confidence:float|None=None;source:str='ai_assist'
class ValidateIn(BaseModel):final_score:float;feedback:str|None=None
@router.post('/institutions/{iid}/offerings/{oid}/assignments')
def create(iid:str,oid:str,q:AssignmentIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.create(auth.account_id,iid,oid,**q.model_dump())))
@router.post('/institutions/{iid}/assignments/{aid}/rubric')
def criterion(iid:str,aid:str,q:CriterionIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.add_criterion(auth.account_id,iid,aid,**q.model_dump())))
@router.post('/institutions/{iid}/assignments/{aid}/publish')
def publish(iid:str,aid:str,q:PublishIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.publish(auth.account_id,iid,aid,q.expected_version)))
@router.post('/institutions/{iid}/assignments/{aid}/submissions')
def submit(iid:str,aid:str,q:SubmitIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.submit(auth.account_id,iid,aid,**q.model_dump())))
@router.post('/institutions/{iid}/submissions/{sid}/grade-proposal')
def proposal(iid:str,sid:str,q:ProposalIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.propose_grade(auth.account_id,iid,sid,**q.model_dump())))
@router.post('/institutions/{iid}/submissions/{sid}/validate-grade')
def validate(iid:str,sid:str,q:ValidateIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.validate_grade(auth.account_id,iid,sid,**q.model_dump())))
@router.post('/institutions/{iid}/assignments/{aid}/similarity-scan')
def similarity(iid:str,aid:str,auth:AuthContext=Depends(current_auth)):return [ser(x) for x in wrap(lambda:runtime.assignments.similarity_flags(auth.account_id,iid,aid))]
@router.get('/institutions/{iid}/offerings/{oid}/student-assignments')
def student_assignments(iid:str,oid:str,auth:AuthContext=Depends(current_auth)):return [ser(x) for x in wrap(lambda:runtime.assignments.student_assignments(auth.account_id,iid,oid))]

# LOT24 v0.25.2 industrial closure API surface
class TransitionIn(BaseModel):
    to_state:str
    expected_version:int
class GroupIn(BaseModel):
    group_key:str
    members:list[str]
class AutoItemIn(BaseModel):
    kind:str
    prompt:str
    expected_answer:str
    points:float
    tolerance:float|None=None
class DeterministicGradeIn(BaseModel):
    answers:dict[str,str]
class ReopenIn(BaseModel):
    until:datetime
    reason:str
    student_account_id:str|None=None
    group_key:str|None=None
class SimilarityReviewIn(BaseModel):
    decision:str
class ResultMutationIn(BaseModel):
    expected_version:int
    reason:str=''

@router.post('/institutions/{iid}/assignments/{aid}/transition')
def transition_assignment(iid:str,aid:str,q:TransitionIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.transition(auth.account_id,iid,aid,to_state=q.to_state,expected_version=q.expected_version)))
@router.post('/institutions/{iid}/assignments/{aid}/groups')
def create_group(iid:str,aid:str,q:GroupIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.create_group(auth.account_id,iid,aid,group_key=q.group_key,members=q.members)))
@router.post('/institutions/{iid}/assignments/{aid}/auto-items')
def add_auto_item(iid:str,aid:str,q:AutoItemIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.add_auto_item(auth.account_id,iid,aid,**q.model_dump())))
@router.post('/institutions/{iid}/submissions/{sid}/deterministic-grade')
def deterministic_grade(iid:str,sid:str,q:DeterministicGradeIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.deterministic_grade(auth.account_id,iid,sid,answers=q.answers)))
@router.post('/institutions/{iid}/assignments/{aid}/reopen-grants')
def reopen(iid:str,aid:str,q:ReopenIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.grant_reopen(auth.account_id,iid,aid,**q.model_dump())))
@router.post('/institutions/{iid}/similarity/{fid}/review')
def review_similarity(iid:str,fid:str,q:SimilarityReviewIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.review_similarity(auth.account_id,iid,fid,decision=q.decision)))
@router.post('/institutions/{iid}/assignments/{aid}/publish-results')
def publish_results(iid:str,aid:str,q:ResultMutationIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.publish_results(auth.account_id,iid,aid,expected_version=q.expected_version)))
@router.post('/institutions/{iid}/assignments/{aid}/retract-results')
def retract_results(iid:str,aid:str,q:ResultMutationIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.retract_results(auth.account_id,iid,aid,expected_version=q.expected_version,reason=q.reason)))
@router.get('/institutions/{iid}/assignments/{aid}/my-result')
def my_result(iid:str,aid:str,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.assignments.student_result(auth.account_id,iid,aid)))

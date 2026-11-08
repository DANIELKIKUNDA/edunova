from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.tutor.domain.model import TutorEvidence
from app.runtime import runtime
router=APIRouter()
class StartIn(BaseModel):course_id:str|None=None;target_concept_id:str|None=None;subject_domain:str='general';high_stakes:bool=False
class EvidenceIn(BaseModel):concept_id:str;mastery:float=Field(ge=0,le=1);error_count:int=Field(default=0,ge=0);bloom_level:str='understand'
class TurnIn(BaseModel):question:str=Field(min_length=2,max_length=6000);evidence:list[EvidenceIn]=Field(default_factory=list,max_length=40);prerequisites:list[str]=Field(default_factory=list,max_length=40);source_count:int=Field(default=0,ge=0);wants_answer:bool=False;mutation_id:str|None=Field(default=None,max_length=96)
def _session(x):return {'id':x.id,'course_id':x.course_id,'target_concept_id':x.target_concept_id,'subject_domain':x.subject_domain,'high_stakes':x.high_stakes,'state':x.state.value,'hint_level':x.hint_level,'turn_count':x.turn_count,'row_version':x.row_version}
@router.post('/sessions')
def start(req:StartIn,auth:AuthContext=Depends(current_auth)):return _session(runtime.tutor.start(auth.account_id,req.course_id,req.target_concept_id,req.subject_domain,req.high_stakes))
@router.post('/sessions/{sid}/turns')
def turn(sid:str,req:TurnIn,auth:AuthContext=Depends(current_auth)):
 x=runtime.tutor_repo.session(auth.account_id,sid)
 if not x:raise HTTPException(404,'tutor_session_not_found')
 try:t=runtime.tutor.decide(x,req.question,tuple(TutorEvidence(e.concept_id,e.mastery,e.error_count,e.bloom_level) for e in req.evidence),tuple(req.prerequisites),req.source_count,req.wants_answer,req.mutation_id)
 except ValueError as e:raise HTTPException(409 if 'conflict' in str(e) else 422,str(e)) from e
 d=t.decision;return {'turn_id':t.id,'move':d.move.value,'reason':d.reason,'target_concept_id':d.target_concept_id,'bloom_target':d.bloom_target,'hint_level':d.hint_level,'requires_sources':d.requires_sources,'next_action':d.next_action,'evidence':list(t.evidence)}
@router.get('/sessions/{sid}')
def get(sid:str,auth:AuthContext=Depends(current_auth)):
 x=runtime.tutor_repo.session(auth.account_id,sid)
 if not x:raise HTTPException(404,'tutor_session_not_found')
 return {**_session(x),'turns':[{'id':t.id,'question':t.question,'move':t.decision.move.value,'reason':t.decision.reason} for t in runtime.tutor_repo.turns(auth.account_id,sid)]}

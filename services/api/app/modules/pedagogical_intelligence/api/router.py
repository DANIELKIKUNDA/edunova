from fastapi import APIRouter,HTTPException,Depends
from pydantic import BaseModel,Field
from app.modules.pedagogical_intelligence.application.service import PedagogicalIntelligenceService
from app.modules.pedagogical_intelligence.domain.model import LearningSignal
router=APIRouter(); service=PedagogicalIntelligenceService()
class Signal(BaseModel):
 objective_id:str=Field(min_length=1,max_length=200);learner_count:int;assessed_count:int;mean_score:float|None=None;failure_count:int=0;attendance_rate:float|None=None
@router.post('/analyze')
def analyze(q:list[Signal]):
 try:r=service.analyze([LearningSignal(**x.model_dump()) for x in q])
 except ValueError as e:raise HTTPException(400,str(e))
 return {'method':r.method,'predictive_model':r.predictive_model,'objective_count':r.objective_count,'insights':[x.__dict__ for x in r.insights]}

from app.modules.identity.api.router import current_auth
from app.runtime import runtime
@router.get('/institutions/{iid}/offerings/{offering_id}/report')
def canonical_report(iid:str,offering_id:str,a=Depends(current_auth)):
 try:return runtime.pedagogical_intelligence.offering_report(a.account_id,iid,offering_id)
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(400,str(e))
class ObjectiveIn(BaseModel):
 objective_id:str=Field(min_length=1,max_length=120);title:str=Field(min_length=1,max_length=500)
class QuestionMapIn(BaseModel): question_id:str=Field(min_length=1,max_length=64)
class BlueprintBindIn(BaseModel): blueprint_id:str=Field(min_length=1,max_length=64)
@router.post('/institutions/{iid}/offerings/{offering_id}/objectives')
def register_objective(iid:str,offering_id:str,q:ObjectiveIn,a=Depends(current_auth)):
 try:return runtime.pedagogical_intelligence.register_objective(a.account_id,iid,offering_id,q.objective_id,q.title)
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(400,str(e))
@router.post('/institutions/{iid}/offerings/{offering_id}/objectives/{objective_id}/questions')
def map_question(iid:str,offering_id:str,objective_id:str,q:QuestionMapIn,a=Depends(current_auth)):
 try:return runtime.pedagogical_intelligence.map_question(a.account_id,iid,offering_id,objective_id,q.question_id)
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(400,str(e))
@router.post('/institutions/{iid}/offerings/{offering_id}/assessment-blueprints')
def bind_blueprint(iid:str,offering_id:str,q:BlueprintBindIn,a=Depends(current_auth)):
 try:return runtime.pedagogical_intelligence.bind_blueprint(a.account_id,iid,offering_id,q.blueprint_id)
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(400,str(e))
@router.get('/institutions/{iid}/offerings/{offering_id}/objectives/report')
def objective_report(iid:str,offering_id:str,a=Depends(current_auth)):
 try:return runtime.pedagogical_intelligence.objective_report(a.account_id,iid,offering_id)
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(400,str(e))

@router.get('/institutions/{iid}/offerings/{offering_id}/dashboard')
def teaching_dashboard(iid:str,offering_id:str,a=Depends(current_auth)):
 try:return runtime.pedagogical_intelligence.teaching_dashboard(a.account_id,iid,offering_id)
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(400,str(e))

@router.get('/institutions/{iid}/offerings/{offering_id}/gradebook-reconciliation')
def gradebook_assessment_reconciliation(iid:str,offering_id:str,a=Depends(current_auth)):
 try:return runtime.pedagogical_intelligence.gradebook_assessment_reconciliation(a.account_id,iid,offering_id)
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(400,str(e))

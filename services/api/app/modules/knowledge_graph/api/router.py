from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
class NodeIn(BaseModel):kind:str;label:str;description:str='';course_id:str|None=None;source_revision_id:str|None=None;source_locator:str|None=None;provenance_sha256:str|None=None;origin:str='human'
class RelationIn(BaseModel):source_id:str;target_id:str;kind:str;rationale:str;confidence:int=Field(ge=0,le=100);origin:str='human';source_revision_id:str|None=None;provenance_sha256:str|None=None
@router.post('/nodes')
def node(b:NodeIn,a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.create_node(a.account_id,**b.model_dump()).__dict__
@router.post('/relations')
def relation(b:RelationIn,a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.propose_relation(a.account_id,actor=a.account_id,**b.model_dump()).__dict__
@router.post('/relations/{id}/validate')
def validate(id:str,a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.validate_relation(a.account_id,id,a.account_id).__dict__
@router.post('/relations/{id}/publish')
def publish(id:str,high_stakes:bool=False,a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.publish_relation(a.account_id,id,a.account_id,high_stakes).__dict__
@router.get('/concepts/{id}/prerequisites')
def prerequisites(id:str,depth:int=5,a:AuthContext=Depends(current_auth)):return {'items':[x.__dict__ for x in runtime.knowledge_graph.prerequisites(a.account_id,id,min(depth,8))]}
@router.get('/concepts/{id}/assessment-context')
def assessment_context(id:str,a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.assessment_context(a.account_id,id)

class ExtractionIn(BaseModel):
 source_revision_id:str;source_sha256:str=Field(min_length=64,max_length=64);course_id:str|None=None;candidates:list[dict]
@router.post('/extractions')
def extraction(b:ExtractionIn,a:AuthContext=Depends(current_auth)):
 batch,items=runtime.knowledge_graph.start_extraction(a.account_id,b.source_revision_id,b.source_sha256,b.course_id,a.account_id,b.candidates);return {'batch':batch.__dict__,'items':[x.__dict__ for x in items]}
@router.post('/extractions/{id}/review')
def extraction_review(id:str,a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.submit_extraction_review(a.account_id,id,a.account_id).__dict__
@router.post('/extraction-candidates/{id}/accept')
def accept_candidate(id:str,high_stakes:bool=False,a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.accept_candidate(a.account_id,id,a.account_id,high_stakes).__dict__
@router.post('/extraction-candidates/{id}/reject')
def reject_candidate(id:str,a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.reject_candidate(a.account_id,id,a.account_id).__dict__
@router.get('/concepts/{id}/learning-sequence')
def learning_sequence(id:str,a:AuthContext=Depends(current_auth)):return {'items':runtime.knowledge_graph.learning_sequence(a.account_id,id)}
@router.get('/health')
def health(a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.graph_health(a.account_id)

class SnapshotIn(BaseModel):reason:str='manual'
@router.post('/snapshots')
def snapshot(b:SnapshotIn,a:AuthContext=Depends(current_auth)):return runtime.knowledge_graph.create_snapshot(a.account_id,a.account_id,b.reason).__dict__
@router.get('/relations/{id}/impact')
def impact(id:str,a:AuthContext=Depends(current_auth)):return {'items':[x.__dict__ for x in runtime.knowledge_graph.impact_analysis(a.account_id,id)]}
@router.post('/relations/{id}/retire')
def retire(id:str,expected_version:int|None=None,a:AuthContext=Depends(current_auth)):
 r,impacts=runtime.knowledge_graph.retire_relation(a.account_id,id,a.account_id,expected_version);return {'relation':r.__dict__,'impacts':[x.__dict__ for x in impacts]}
class PlanIn(BaseModel):mastery:dict[str,float]={}
@router.post('/concepts/{id}/prerequisite-plan')
def prerequisite_plan(id:str,b:PlanIn,a:AuthContext=Depends(current_auth)):return {'items':runtime.knowledge_graph.prerequisite_plan(a.account_id,id,b.mastery)}

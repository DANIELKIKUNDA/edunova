from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.assessment.domain.model import QuestionType,BloomLevel,ImportFormat
from app.runtime import runtime
router=APIRouter()
class QuestionIn(BaseModel):bank_id:str;course_id:str;chapter_id:str|None=None;kind:QuestionType;prompt:str;choices:list[str]=[];correct:list[str];explanation:str='';pages:list[int]=[];source_text:str;approved:bool=True;points:int=1;difficulty:int=2;bloom_level:BloomLevel=BloomLevel.UNDERSTAND;learning_objective:str='';cognitive_steps:list[str]=[];distractor_rationales:list[str]=[];clinical_vignette:bool=False
class BlueprintIn(BaseModel):title:str;course_id:str;duration_minutes:int=Field(ge=5,le=360);question_count:int=Field(ge=1,le=200);pass_percent:int=Field(60,ge=0,le=100);shuffle:bool=True;bloom_distribution:dict[str,int]|None=None;min_quality_score:int=Field(0,ge=0,le=100)
class AnswerIn(BaseModel):values:list[str]=[];marked_for_review:bool=False;row_version:int=Field(ge=1)
def err(e):raise HTTPException(409 if 'conflict' in str(e) else 422,str(e))
@router.post('/questions',status_code=201)
def question(x:QuestionIn,auth:AuthContext=Depends(current_auth)):
 try:return runtime.assessment.create_question(**x.model_dump()).__dict__
 except ValueError as e:err(e)
@router.post('/blueprints',status_code=201)
def blueprint(x:BlueprintIn,auth:AuthContext=Depends(current_auth)):
 try:return runtime.assessment.create_blueprint(**x.model_dump()).__dict__
 except ValueError as e:err(e)
@router.post('/blueprints/{id}/start',status_code=201)
def start(id:str,auth:AuthContext=Depends(current_auth)):
 try:return runtime.assessment.start(auth.account_id,id).__dict__
 except ValueError as e:err(e)
@router.put('/attempts/{id}/answers/{qid}')
def answer(id:str,qid:str,x:AnswerIn,auth:AuthContext=Depends(current_auth)):
 try:return runtime.assessment.answer(auth.account_id,id,qid,x.values,x.marked_for_review,x.row_version).__dict__
 except ValueError as e:err(e)
@router.post('/attempts/{id}/submit')
def submit(id:str,row_version:int=Query(...,ge=1),auth:AuthContext=Depends(current_auth)):
 try:return runtime.assessment.submit(auth.account_id,id,row_version).__dict__
 except ValueError as e:err(e)
@router.get('/attempts/{id}')
def resume(id:str,auth:AuthContext=Depends(current_auth)):
 try:return runtime.assessment.resume(auth.account_id,id).__dict__
 except ValueError as e:err(e)

@router.post('/questions/quality-check')
def quality_check(x:QuestionIn,auth:AuthContext=Depends(current_auth)):
 try:return runtime.assessment.evaluate_question_quality(x.kind,x.prompt,x.choices,x.correct,x.explanation,x.pages,x.bloom_level,x.learning_objective,x.cognitive_steps,x.distractor_rationales,x.clinical_vignette).__dict__
 except ValueError as e:err(e)

class QuestionImportIn(BaseModel):
 bank_id:str; course_id:str; source_document_id:str; content:str; chapter_id:str|None=None; format:ImportFormat
class QuestionExportIn(BaseModel): question_ids:list[str]; format:ImportFormat
@router.post('/question-factory/import')
def question_factory_import(x:QuestionImportIn,auth:AuthContext=Depends(current_auth)):
 try:
  if x.format==ImportFormat.GIFT:return runtime.assessment.import_gift(x.bank_id,x.course_id,x.source_document_id,x.content,x.chapter_id).__dict__
  if x.format==ImportFormat.MOODLE_XML:return runtime.assessment.import_moodle_xml(x.bank_id,x.course_id,x.source_document_id,x.content,x.chapter_id).__dict__
  raise ValueError('unsupported_import_format')
 except ValueError as e:err(e)
@router.post('/question-factory/export')
def question_factory_export(x:QuestionExportIn,auth:AuthContext=Depends(current_auth)):
 try:
  if x.format==ImportFormat.GIFT:return {'format':'gift','content':runtime.assessment.export_gift(x.question_ids)}
  if x.format==ImportFormat.MOODLE_XML:return {'format':'moodle_xml','content':runtime.assessment.export_moodle_xml(x.question_ids)}
  raise ValueError('unsupported_export_format')
 except ValueError as e:err(e)
@router.get('/questions/{id}/variant-spec')
def variant_spec(id:str,target_bloom:str|None=None,target_difficulty:int|None=None,auth:AuthContext=Depends(current_auth)):
 try:return runtime.assessment.variant_specification(id,target_bloom,target_difficulty).__dict__
 except ValueError as e:err(e)

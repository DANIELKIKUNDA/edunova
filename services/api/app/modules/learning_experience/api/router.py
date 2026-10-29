from datetime import datetime,UTC
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.learning_experience.domain.model import StudyMode,MasteryStage
from app.runtime import runtime
router=APIRouter()
class StartReq(BaseModel): course_id:str; chapter_id:str|None=None; mode:StudyMode=StudyMode.READ; objective:str|None=Field(None,max_length=500)
class MutReq(BaseModel): active_seconds:int=Field(0,ge=0,le=7200); last_position:str|None=Field(None,max_length=255); expected_version:int|None=None
class ProgressReq(BaseModel): course_id:str; chapter_id:str|None=None; stage:MasteryStage; completion_ratio:float=Field(ge=0,le=1); correct:int=Field(0,ge=0); total:int=Field(0,ge=0)
class ErrorReq(BaseModel): course_id:str; chapter_id:str|None=None; source_type:str; source_id:str; prompt:str; correct_answer:str|None=None
class ReviewReq(BaseModel): card_id:str; course_id:str; chapter_id:str|None=None; quality:int=Field(ge=0,le=5)
class ErrorReviewReq(BaseModel): correct:bool
class ExamPlanReq(BaseModel): title:str=Field(min_length=1,max_length=160); exam_at:datetime; daily_minutes:int=Field(ge=10,le=480); course_ids:list[str]=Field(min_length=1,max_length=30)
def session_out(x): return {'id':x.id,'course_id':x.course_id,'chapter_id':x.chapter_id,'mode':x.mode.value,'state':x.state.value,'started_at':x.started_at,'updated_at':x.updated_at,'ended_at':x.ended_at,'active_seconds':x.active_seconds,'last_position':x.last_position,'objective':x.objective,'row_version':x.row_version}
def call(fn):
 try:return fn()
 except LookupError as e: raise HTTPException(404,str(e))
 except ValueError as e: raise HTTPException(409 if 'concurrent' in str(e) or 'active_session' in str(e) else 422,str(e))
@router.get('/home')
def home(auth:AuthContext=Depends(current_auth)): return runtime.learning_experience.home(auth.account_id)
@router.post('/sessions')
def start(req:StartReq,auth:AuthContext=Depends(current_auth)): return session_out(call(lambda:runtime.learning_experience.start(auth.account_id,req.course_id,req.chapter_id,req.mode,req.objective)))
@router.post('/sessions/{id}/{action}')
def mutate(id:str,action:str,req:MutReq,auth:AuthContext=Depends(current_auth)): return session_out(call(lambda:runtime.learning_experience.mutate(auth.account_id,id,action,active_seconds=req.active_seconds,last_position=req.last_position,expected_version=req.expected_version)))
@router.post('/progress')
def progress(req:ProgressReq,auth:AuthContext=Depends(current_auth)):
 x=call(lambda:runtime.learning_experience.record_progress(auth.account_id,req.course_id,req.chapter_id,req.stage,req.completion_ratio,req.correct,req.total)); return {'stage':x.stage.value,'completion_ratio':x.completion_ratio,'accuracy':x.accuracy,'updated_at':x.updated_at}
@router.post('/errors')
def error(req:ErrorReq,auth:AuthContext=Depends(current_auth)): x=runtime.learning_experience.add_error(auth.account_id,req.course_id,req.chapter_id,req.source_type,req.source_id,req.prompt,req.correct_answer); return {'id':x.id,'next_review_at':x.next_review_at}
@router.get('/errors')
def errors(auth:AuthContext=Depends(current_auth)): return [{'id':x.id,'course_id':x.course_id,'chapter_id':x.chapter_id,'prompt':x.prompt,'attempts':x.attempts,'next_review_at':x.next_review_at} for x in runtime.learning_repository.unresolved_errors(auth.account_id)]
@router.post('/flashcards/review')
def review(req:ReviewReq,auth:AuthContext=Depends(current_auth)): x=runtime.learning_experience.review(auth.account_id,req.card_id,req.course_id,req.chapter_id,req.quality); return {'card_id':x.card_id,'repetitions':x.repetitions,'interval_days':x.interval_days,'ease_factor':x.ease_factor,'due_at':x.due_at}
@router.get('/flashcards/due')
def due(auth:AuthContext=Depends(current_auth)): return [{'card_id':x.card_id,'course_id':x.course_id,'chapter_id':x.chapter_id,'due_at':x.due_at} for x in runtime.learning_repository.due_cards(auth.account_id,runtime.learning_experience.now())]

@router.post('/errors/{error_id}/review')
def review_error(error_id:str,req:ErrorReviewReq,auth:AuthContext=Depends(current_auth)):
 x=call(lambda:runtime.learning_experience.review_error(auth.account_id,error_id,correct=req.correct)); return {'id':x.id,'attempts':x.attempts,'resolved':x.resolved,'next_review_at':x.next_review_at}
@router.post('/exam-plans')
def exam_plan(req:ExamPlanReq,auth:AuthContext=Depends(current_auth)):
 x=call(lambda:runtime.learning_experience.create_exam_plan(auth.account_id,req.title,req.exam_at,req.daily_minutes,req.course_ids)); return {'id':x.id,'title':x.title,'exam_at':x.exam_at,'daily_minutes':x.daily_minutes,'course_ids':x.course_ids,'state':x.state.value,'row_version':x.row_version}
@router.get('/recommendations')
def recommendations(auth:AuthContext=Depends(current_auth)):
 return [x.__dict__ for x in runtime.learning_experience.recommendations(auth.account_id)]

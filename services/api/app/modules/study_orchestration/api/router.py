from datetime import date,datetime
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
class Prefs(BaseModel):
 timezone:str='Africa/Lubumbashi';daily_limit_minutes:int=Field(120,ge=30,le=480);session_max_minutes:int=Field(45,ge=10,le=120);preferred_start_hour:int=Field(18,ge=0,le=23);preferred_end_hour:int=Field(22,ge=1,le=24);buffer_minutes:int=Field(10,ge=0,le=60);weekend_enabled:bool=True;row_version:int=1
class Busy(BaseModel):starts_at:datetime;ends_at:datetime;label:str=Field(min_length=1,max_length=180);source:str='manual'
def item(x):return {**x.__dict__,'source':x.source.value,'state':x.state.value,'plan_date':x.plan_date.isoformat(),'starts_at':x.starts_at.isoformat(),'ends_at':x.ends_at.isoformat(),'minutes':x.minutes}
@router.get('/preferences')
def prefs(auth:AuthContext=Depends(current_auth)):return runtime.study_planner.preferences(auth.account_id).__dict__
@router.put('/preferences')
def put_prefs(body:Prefs,auth:AuthContext=Depends(current_auth)):
 try:return runtime.study_planner.update_preferences(auth.account_id,**body.model_dump()).__dict__
 except ValueError as e:raise HTTPException(409 if 'conflict' in str(e) else 422,str(e))
@router.post('/busy-blocks',status_code=201)
def busy(body:Busy,auth:AuthContext=Depends(current_auth)):
 try:return runtime.study_planner.add_busy(auth.account_id,body.starts_at,body.ends_at,body.label,body.source).__dict__
 except ValueError as e:raise HTTPException(422,str(e))
@router.post('/days/{day}/generate')
def generate(day:date,auth:AuthContext=Depends(current_auth)):
 x=runtime.study_planner.generate_day(auth.account_id,day);return {'date':x.plan_date.isoformat(),'planned_minutes':x.planned_minutes,'capacity_minutes':x.capacity_minutes,'overflow_minutes':x.overflow_minutes,'explanation':x.explanation,'model_version':x.model_version,'items':[item(i) for i in x.items]}
@router.get('/days/{day}')
def get_day(day:date,auth:AuthContext=Depends(current_auth)):
 x=runtime.study_planner.day(auth.account_id,day);return {**x,'date':day.isoformat(),'items':[item(i) for i in x['items']]}
@router.post('/items/{id}/{state}')
def transition(id:str,state:str,row_version:int=Query(...,ge=1),auth:AuthContext=Depends(current_auth)):
 if state not in {'done','skipped'}:raise HTTPException(422,'invalid_transition')
 try:return item(runtime.study_planner.transition(auth.account_id,id,state,row_version))
 except ValueError as e:raise HTTPException(409 if 'conflict' in str(e) else 404,str(e))
@router.post('/replan')
def replan(days:int=Query(7,ge=1,le=14),auth:AuthContext=Depends(current_auth)):
 xs=runtime.study_planner.replan_from_today(auth.account_id,days);return {'days':[{'date':x.plan_date.isoformat(),'planned_minutes':x.planned_minutes,'capacity_minutes':x.capacity_minutes,'overflow_minutes':x.overflow_minutes,'items':[item(i) for i in x.items]} for x in xs]}

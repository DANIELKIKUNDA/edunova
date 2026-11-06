from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.runtime import runtime
from app.modules.identity.application.auth_context import AuthContext
from app.modules.identity.api.router import current_auth
from app.modules.engagement.domain.model import EngagementDay, NotificationPreferences

router=APIRouter()

def auth(account: AuthContext = Depends(current_auth)):
    return account

class PreferencesBody(BaseModel):
    quiet_start_minute:int=Field(1320,ge=0,lt=1440); quiet_end_minute:int=Field(420,ge=0,lt=1440); max_daily_notifications:int=Field(2,ge=0,le=6)
    assessment_enabled:bool=True; study_plan_enabled:bool=True; flashcards_enabled:bool=True; streak_enabled:bool=False; content_enabled:bool=True; push_enabled:bool=True; preferred_study_minute:int=Field(1140,ge=0,lt=1440); timezone_offset_minutes:int=Field(0,ge=-840,le=840); daily_goal_minutes:int=Field(30,ge=5,le=240)
class PushBody(BaseModel): device_id:str=Field(min_length=3,max_length=80); platform:str; token:str=Field(min_length=16,max_length=4096)
class ActivityBody(BaseModel): day_key:str=Field(pattern=r"^\d{4}-\d{2}-\d{2}$"); active_minutes:int=Field(0,ge=0,le=1440); completed_tasks:int=Field(0,ge=0); quiz_questions:int=Field(0,ge=0); flashcards_reviewed:int=Field(0,ge=0)

@router.get('/preferences')
def get_preferences(account=Depends(auth)):
    return runtime.engagement.preferences(account.account_id).__dict__

@router.put('/preferences')
def put_preferences(body:PreferencesBody, account=Depends(auth)):
    try: p=NotificationPreferences(**body.model_dump())
    except ValueError as e: raise HTTPException(422,str(e))
    return runtime.engagement.update_preferences(account.account_id,p).__dict__

@router.post('/push-devices',status_code=204)
def register_push(body:PushBody,account=Depends(auth)):
    try: runtime.engagement.register_push(account.account_id,body.device_id,body.platform,body.token)
    except ValueError as e: raise HTTPException(422,str(e))

@router.delete('/push-devices/{device_id}',status_code=204)
def revoke_push(device_id:str,account=Depends(auth)):
    runtime.engagement.revoke_push(account.account_id,device_id)

@router.post('/activity')
def activity(body:ActivityBody,account=Depends(auth)):
    s=runtime.engagement.record_activity(account.account_id,EngagementDay(**body.model_dump()))
    return s.__dict__

@router.get('/streak')
def streak(account=Depends(auth)):
    return runtime.engagement.streak(account.account_id).__dict__

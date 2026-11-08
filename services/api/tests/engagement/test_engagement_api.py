from uuid import uuid4
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.runtime import runtime
from app.modules.identity.application.service import RegisterInput

client=TestClient(app)

def headers():
    _,t=runtime.identity.register(RegisterInput(display_name='Engagement User',password='strong-pass-123',email=f'e-{uuid4().hex}@test.local',phone_number=None,device_name='pytest'))
    return {'Authorization':f'Bearer {t.access_token}'}

def test_preferences_round_trip_and_streak_endpoint():
    h=headers()
    r=client.put('/v1/engagement/preferences',headers=h,json={'quiet_start_minute':1260,'quiet_end_minute':360,'max_daily_notifications':1,'assessment_enabled':True,'study_plan_enabled':True,'flashcards_enabled':False,'streak_enabled':False,'content_enabled':True,'push_enabled':True,'preferred_study_minute':1080})
    assert r.status_code==200
    assert client.get('/v1/engagement/preferences',headers=h).json()['max_daily_notifications']==1
    day_key=runtime.engagement.now().date().isoformat()
    a=client.post('/v1/engagement/activity',headers=h,json={'day_key':day_key,'active_minutes':25,'completed_tasks':2,'quiz_questions':10,'flashcards_reviewed':0})
    assert a.status_code==200 and a.json()['current_days']>=1

def test_push_registration_rejects_short_token_and_unknown_platform():
    h=headers()
    assert client.post('/v1/engagement/push-devices',headers=h,json={'device_id':'dev1','platform':'android','token':'short'}).status_code==422
    r=client.post('/v1/engagement/push-devices',headers=h,json={'device_id':'dev1','platform':'blackberry','token':'x'*32})
    assert r.status_code==422

def test_push_registration_accepts_android_and_revoke():
    h=headers(); token='x'*64
    r=client.post('/v1/engagement/push-devices',headers=h,json={'device_id':'dev1','platform':'android','token':token})
    assert r.status_code==204
    assert client.delete('/v1/engagement/push-devices/dev1',headers=h).status_code==204


def test_daily_goal_validation_rejects_unrealistic_value():
    h=headers()
    r=client.put('/v1/engagement/preferences',headers=h,json={'daily_goal_minutes':1})
    assert r.status_code==422


def test_activity_upsert_is_monotonic_for_retry_safety():
    h=headers()
    day_key=runtime.engagement.now().date().isoformat()
    first={'day_key':day_key,'active_minutes':40,'completed_tasks':3,'quiz_questions':20,'flashcards_reviewed':12}
    second={'day_key':day_key,'active_minutes':10,'completed_tasks':1,'quiz_questions':5,'flashcards_reviewed':2}
    assert client.post('/v1/engagement/activity',headers=h,json=first).status_code==200
    assert client.post('/v1/engagement/activity',headers=h,json=second).status_code==200
    account=runtime.authenticator.authenticate(h['Authorization'].split(' ',1)[1]).account_id
    day=next(d for d in runtime.engagement_repository.recent_days(account,10) if d.day_key==day_key)
    assert day.active_minutes==40 and day.completed_tasks==3 and day.quiz_questions==20 and day.flashcards_reviewed==12

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_planning_today_endpoint_prioritizes_imminent_course():
    payload = {
      'now':'2026-09-20T10:00:00Z','budget_minutes':15,
      'states':[{'course_id':'bio','readiness':30,'open_errors':5},{'course_id':'math','readiness':80}],
      'events':[{'id':'e','course_id':'bio','title':'Interro','kind':'interrogation','starts_at':'2026-09-22T10:00:00Z'}],
      'tasks':[{'id':'b','course_id':'bio','title':'Quiz Bio','kind':'quiz','estimated_minutes':15,'learning_value':.8},{'id':'m','course_id':'math','title':'Quiz Math','kind':'quiz','estimated_minutes':15,'learning_value':.8}],
    }
    r=client.post('/v1/planning/today',json=payload)
    assert r.status_code==200
    assert r.json()['tasks'][0]['course_id']=='bio'


def test_planning_conflict_endpoint():
    r=client.post('/v1/planning/timetable/conflicts',json=[
      {'id':'a','course_id':'c1','weekday':1,'start_minute':480,'end_minute':540},
      {'id':'b','course_id':'c2','weekday':1,'start_minute':530,'end_minute':600},
    ])
    assert r.status_code==200
    assert r.json()['conflicts']==[['a','b']]


def test_adaptive_day_api_schedules_inside_real_window():
    now='2026-09-20T08:00:00+00:00'
    payload={
        'now':now,
        'windows':[{'id':'w','starts_at':now,'ends_at':'2026-09-20T10:00:00+00:00','energy':'high'}],
        'states':[{'course_id':'bio','readiness':35,'readiness_confidence':.4,'open_errors':3}],
        'tasks':[{'id':'quiz','course_id':'bio','title':'Quiz bio','kind':'quiz','remaining_minutes':30,'learning_value':.9,'cognitive_load':4}],
        'constraints':{'max_continuous_minutes':50,'break_minutes':10},
    }
    r=client.post('/v1/planning/adaptive/day',json=payload)
    assert r.status_code==200
    data=r.json()
    assert data['study_minutes']>0
    assert data['blocks'][0]['course_id']=='bio'
    assert data['available_minutes']==120


def test_adaptive_feasibility_api_reports_deficit():
    payload={
        'now':'2026-09-20T08:00:00+00:00','deadline':'2026-09-20T10:00:00+00:00','required_minutes':180,
        'windows':[{'id':'w','starts_at':'2026-09-20T08:00:00+00:00','ends_at':'2026-09-20T10:00:00+00:00'}],
    }
    r=client.post('/v1/planning/adaptive/feasibility',json=payload)
    assert r.status_code==200
    assert r.json()['deficit_minutes']==60

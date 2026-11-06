from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)


def payload():
    return {
      'generated_at':'2026-09-22T08:00:00Z','study_minutes_7d':210,'study_minutes_prev_7d':140,
      'quiz_accuracy_7d':.72,'quiz_accuracy_prev_7d':.61,'plan_adherence_7d':.68,
      'active_days_7d':5,'streak_days':4,
      'courses':[{
        'course_id':'phys','title':'Physiologie','coverage':.55,'quiz_mastery':.48,
        'flashcard_mastery':.62,'weakness_recovery':.4,'open_errors':7,'overdue_flashcards':9,
        'days_to_next_assessment':4,'next_assessment_readiness':53,'study_minutes_7d':35,
        'plan_adherence_7d':.6,'mastery_delta_7d':.05,
      }]
    }


def test_analyze_endpoint_is_deterministic_and_stateless():
    a=client.post('/v1/analytics/analyze',json=payload())
    b=client.post('/v1/analytics/analyze',json=payload())
    assert a.status_code==200 and b.status_code==200
    assert a.json()==b.json()
    assert a.json()['course_insights'][0]['course_id']=='phys'
    assert a.json()['recommendations']


def test_analyze_endpoint_rejects_impossible_percentages():
    body=payload(); body['courses'][0]['quiz_mastery']=1.5
    r=client.post('/v1/analytics/analyze',json=body)
    assert r.status_code==422


def test_health_reports_new_baseline_version():
    r=client.get('/health')
    from app.version import __version__
    assert r.status_code==200 and r.json()['version']==__version__

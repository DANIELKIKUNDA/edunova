from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_pedagogy_capabilities():
    response = client.get('/v1/pedagogy/capabilities')
    assert response.status_code == 200
    assert 'quiz_evaluation' in response.json()['features']


def test_pedagogy_adaptive_readiness_api():
    response = client.post('/v1/pedagogy/readiness', json={'coverage': 1, 'quiz_mastery': 0})
    assert response.status_code == 200
    assert response.json()['value'] == 43


def test_pedagogy_flashcard_review_api():
    response = client.post('/v1/pedagogy/flashcards/review', json={'flashcard_id': 'f1', 'rating': 'good'})
    assert response.status_code == 200
    assert response.json()['interval_days'] == 1


def test_pedagogy_quiz_evaluation_api():
    response = client.post('/v1/pedagogy/quiz/evaluate', json={
        'kind': 'single_choice',
        'prompt': '2+2 ?',
        'options': [{'id': 'A', 'text': '4'}, {'id': 'B', 'text': '5'}],
        'correct_option_ids': ['A'],
        'selected_option_ids': ['A'],
        'explanation': '2+2=4',
    })
    assert response.status_code == 200
    assert response.json() == {'correct': True, 'score': 1.0, 'explanation': '2+2=4'}


def test_mastery_endpoint():
    response = client.post('/v1/pedagogy/mastery', json=[
        {'objective_id':'o1','score':1.0,'weight':1,'recency_factor':0.5},
        {'objective_id':'o1','score':0.0,'weight':1,'recency_factor':1.0},
    ])
    assert response.status_code == 200
    assert response.json()['value'] == 33


def test_adaptive_practice_endpoint():
    response = client.post('/v1/pedagogy/practice/rank', json=[
        {'question_id':'strong','difficulty':2,'mastery':0.9,'error_count':0,'seen_count':3},
        {'question_id':'weak','difficulty':3,'mastery':0.2,'error_count':3,'seen_count':1},
    ])
    assert response.status_code == 200
    assert response.json()['question_ids'][0] == 'weak'

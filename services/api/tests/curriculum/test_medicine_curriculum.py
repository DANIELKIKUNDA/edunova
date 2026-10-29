from fastapi.testclient import TestClient
from app.main import app
from app.modules.curriculum.application.service import CurriculumCatalogService

client=TestClient(app)

def test_complete_medicine_reference_has_14_semesters_and_source_totals():
    s=CurriculumCatalogService(); c=s.catalog()
    assert [x['semester'] for x in c['semesters']]==list(range(1,15))
    assert all(x['declared_totals']['hours']==750 and x['declared_totals']['credits']==30 for x in c['semesters'])
    assert c['suggestions_status']=='editorial_recommendations_not_applied'

def test_source_anomalies_are_preserved_not_silently_repaired():
    s=CurriculumCatalogService(); s2=s.semester(2); s8=s.semester(8); s14=s.semester(14)
    assert any('declared 2 credits' in x for x in s2['notes'])
    chi=next(x for x in s8['entries'] if x.get('code')=='CHI1448')
    assert chi['title'] is None and chi['source_row_incomplete'] is True
    assert all(x.get('source_code_semester_mismatch') for x in s14['entries'] if x.get('code') in {'SZS14713','SGO14713','SPE14713'})

def test_search_supports_code_and_title_without_mutating_source():
    s=CurriculumCatalogService()
    assert s.find_entries('ANA1111')[0]['title'].startswith('Anatomie 1')
    assert any(x['code']=='TFE13714' for x in s.find_entries('travail de fin'))

def test_curriculum_audit_surfaces_source_review_items():
    a=CurriculumCatalogService().audit()
    assert a['semester_count']==14 and a['entry_count']>=100 and a['suggestions_applied'] is False
    assert any(x['kind']=='source_row_incomplete' and x.get('code')=='CHI1448' for x in a['issues'])

def test_curriculum_api_exposes_semesters_search_and_audit():
    assert client.get('/v1/curricula/medicine/semesters/14').status_code==200
    r=client.get('/v1/curricula/medicine/search',params={'q':'Neurophysiologie'}); assert r.status_code==200 and r.json()[0]['semester']==5
    a=client.get('/v1/curricula/medicine/audit'); assert a.status_code==200 and a.json()['semester_count']==14

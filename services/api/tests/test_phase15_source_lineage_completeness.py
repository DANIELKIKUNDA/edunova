"""EduNova v0.50.2 — evidence lineage, observational reach and safe comparisons.

Real SQLite / SQLAlchemy integration tests: no PostgreSQL, Redis or Flutter claim.
"""
from datetime import timedelta
from uuid import uuid4
import pytest
from sqlalchemy import select

from app.modules.campus.domain.model import CampusRole
from app.modules.gradebook.infrastructure.sqlalchemy_repo import GradebookRow, ComponentRow, MarkRow
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import AttendanceSessionRow, AttendanceRecordRow
from app.modules.institutional_analytics.application.service import InstitutionalAnalyticsService
from test_institutional_analytics_lot27 import seed, NOW
from test_phase15_institutional_intelligence import _add_students
from test_phase15_period_comparison import five_disjoint, compare


def _gradebook(ia, i, off, students, *, scores=None, weight=100, max_score=20, pass_percent=50):
    scores = scores or {student: 20 for student in students}
    gid, cid = uuid4().hex, uuid4().hex
    with ia.repo.sf() as db:
        db.add(GradebookRow(id=gid,institution_id=i.id,offering_id=off.id,title='Final',
            state='published',pass_percent=pass_percent,row_version=1,created_by='owner',
            created_at=NOW,updated_at=NOW))
        db.add(ComponentRow(id=cid,institution_id=i.id,gradebook_id=gid,title='Exam',
            kind='exam',weight_percent=weight,max_score=max_score,source_assignment_id=None,
            position=1,created_at=NOW))
        for student in students:
            db.add(MarkRow(id=uuid4().hex,institution_id=i.id,gradebook_id=gid,
                component_id=cid,student_account_id=student,score=scores[student],
                state='validated',source_ref=None,validated_by='owner',row_version=1,
                created_at=NOW,updated_at=NOW,attendance='present',note=None))
        db.commit()
    return gid,cid


def _attendance(ia,i,off,students):
    with ia.repo.sf() as db:
        sid=uuid4().hex
        db.add(AttendanceSessionRow(id=sid,institution_id=i.id,teaching_session_id=uuid4().hex,
            offering_id=off.id,state='closed',opens_at=NOW,closes_at=NOW+timedelta(hours=1),
            qr_epoch=0,row_version=1,created_by='owner',created_at=NOW,updated_at=NOW))
        for student in students:
            db.add(AttendanceRecordRow(id=uuid4().hex,institution_id=i.id,attendance_session_id=sid,
                student_account_id=student,status='present',recorded_at=NOW,method='manual',
                device_id=None,risk_score=0,review='clear',evidence='',row_version=1,
                updated_at=NOW))
        db.commit()


def test_released_gradebook_has_versioned_lineage_and_full_reach():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    _gradebook(ia,i,off,['student','s2','s3'])
    metric=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['results.pass_rate']
    assert metric['status']=='available' and metric['value']==100
    assert metric['population_reach']['percent']==100.0
    assert metric['population_reach']['status']=='sufficient_observed_population'
    assert len(metric['source_fingerprint_sha256'])==64
    assert metric['source_lineage_version']==2
    assert metric['source_contract']=='published_validated_gradebook'


def test_digest_changes_when_released_statistic_changes_but_no_mutation_of_grades():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    gid,cid=_gradebook(ia,i,off,['student','s2','s3'])
    initial=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['results.pass_rate']
    assert initial['value']==100
    with ia.repo.sf() as db:
        record=db.scalar(select(MarkRow).where(MarkRow.component_id==cid,MarkRow.student_account_id=='s3'))
        record.score=0
        db.commit()
    # The underlying lineage still changes, but a second *published* live
    # projection must be suppressed by the v0.50.7 temporal commitment.
    observed=ia.repo.snapshot(i.id,offering_id=off.id,governed=True)
    calculated=ia._governed_metrics(observed,3)['results.pass_rate']
    assert calculated['value']==66.67
    assert calculated['source_fingerprint_sha256']!=initial['source_fingerprint_sha256']
    new=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['results.pass_rate']
    assert new['value'] is None and new['source_fingerprint_sha256'] is None
    assert new['status']=='temporal_disclosure_suppressed' 
    with ia.repo.sf() as db:
        assert db.get(MarkRow,record.id).score==0  # analytics stays read-only


def test_gradebook_with_inconsistent_component_weights_fails_closed():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    gid,cid=_gradebook(ia,i,off,['student','s2','s3'],weight=50)
    metric=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['results.pass_rate']
    assert metric['status'] in ('unavailable_or_untrusted_source','suppressed_small_population')
    assert metric['value'] is None and metric['source_fingerprint_sha256'] is None
    with ia.repo.sf() as db:
        db.get(ComponentRow,cid).weight_percent=100
        db.commit()
    assert ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['results.pass_rate']['value']==100


@pytest.mark.parametrize('score,max_score,pass_percent',[
    (-1,20,50), (21,20,50), (20,0,50), (20,20,120),
])
def test_corrupt_scores_and_grading_contract_never_publish_a_false_pass_rate(score,max_score,pass_percent):
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    _gradebook(ia,i,off,['student','s2','s3'],scores={'student':score,'s2':20,'s3':20},
               max_score=max_score,pass_percent=pass_percent)
    metric=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['results.pass_rate']
    assert metric['value'] is None and metric['source_fingerprint_sha256'] is None


def test_population_reach_is_suppressed_for_one_person_even_with_many_marks():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3','s4','s5')
    _gradebook(ia,i,off,['student'])
    metric=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['results.pass_rate']
    assert metric['value'] is None
    assert metric['source_fingerprint_sha256'] is None
    assert metric['population_reach']['percent'] is None


def test_attendance_has_observational_reach_not_claim_of_complete_data():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3','s4','s5')
    _attendance(ia,i,off,['student','s2','s3'])
    metric=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['attendance.attendance_rate']
    assert metric['value']==100
    assert metric['population_reach']['percent']==60
    assert metric['population_reach']['status']=='limited_observed_population'
    assert metric['status']=='available'  # descriptive observation, not cohort pass rate


def test_no_coverage_ratio_or_hash_on_unreleased_small_group():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _attendance(ia,i,off,['student'])
    metric=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['attendance.attendance_rate']
    assert metric['value'] is None
    assert metric['population_reach']['percent'] is None
    assert metric['source_fingerprint_sha256'] is None


def test_partial_gradebook_reach_blocks_comparison_of_official_result_rates():
    f=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    future_id=ia.repo.offering_ids(i.id,after.id,future.id)[0]
    new_off=ts.repo.offering(i.id,future_id)
    _gradebook(ia,i,off,['student','old2','old3'])
    _gradebook(ia,i,new_off,['new1','new2','new3','new4','new5'])
    result=compare(f)
    metric=result['metrics']['results.pass_rate']
    assert result['comparison_policy']['data_release']=='eligible'
    assert metric['status']=='source_unavailable_or_version_mismatch'
    assert metric['previous'] is None and metric['delta_percentage_points'] is None
    assert result['comparison_policy']['minimum_reach_percent_for_student_observation_comparisons']==80


def test_full_gradebook_reach_allows_comparison_when_populations_are_disjoint():
    f=five_disjoint()
    cs,ts,ass,gs,ops,ia,i,p,cohort,off,after,future=f
    future_id=ia.repo.offering_ids(i.id,after.id,future.id)[0]
    new_off=ts.repo.offering(i.id,future_id)
    _gradebook(ia,i,off,['student','old2','old3','old4','old5'])
    _gradebook(ia,i,new_off,['new1','new2','new3','new4','new5'],
        scores={'new1':0,'new2':20,'new3':20,'new4':20,'new5':20})
    metric=compare(f)['metrics']['results.pass_rate']
    assert metric['status']=='comparable'
    assert metric['previous']==100 and metric['current']==80
    assert metric['delta_percentage_points']==-20
    assert metric['source_lineage_version']==2


def test_missing_internal_contributors_fail_closed_without_coverage_disclosure():
    data={'results':{'pass_rate':100,'complete_results':5},
          '_metric_contributors':{},'_source_integrity':{'results.pass_rate':True}}
    metric=InstitutionalAnalyticsService._governed_metrics(data,5)['results.pass_rate']
    assert metric['value'] is None and metric['population_reach']['percent'] is None


def test_tampered_internal_result_source_integrity_blocks_release():
    data={'results':{'pass_rate':100,'complete_results':5},
          '_metric_contributors':{'results.pass_rate':5},
          '_source_integrity':{'results.pass_rate':False}}
    metric=InstitutionalAnalyticsService._governed_metrics(data,5)['results.pass_rate']
    assert metric['status']=='unavailable_or_untrusted_source'
    assert metric['source_fingerprint_sha256'] is None


def test_faculty_and_cross_university_cannot_use_new_metric_metadata_to_bypass_rbac():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    other=cs.create_institution('evil',name='Other',slug='other-provenance',legal_name='',country_code='CD',city='Goma',logo_url=None)
    for actor,iid in [('student',i.id),('evil',i.id),('owner',other.id)]:
        with pytest.raises(PermissionError):ia.decision_brief(actor,iid,offering_id=off.id)


def test_published_gradebook_without_components_cannot_inflate_other_results():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    with ia.repo.sf() as db:
        db.add(GradebookRow(id=uuid4().hex,institution_id=i.id,offering_id=off.id,
            title='Contract missing',state='published',pass_percent=50,row_version=1,
            created_by='owner',created_at=NOW,updated_at=NOW))
        db.commit()
    metric=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['results.pass_rate']
    assert metric['value'] is None and metric['source_fingerprint_sha256'] is None


def test_corrupt_attendance_status_fails_closed_in_governed_metric_only():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3')
    _attendance(ia,i,off,['student','s2','s3'])
    ok=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['attendance.attendance_rate']
    assert ok['value']==100
    with ia.repo.sf() as db:
        r=db.scalar(select(AttendanceRecordRow).where(
            AttendanceRecordRow.institution_id==i.id,AttendanceRecordRow.student_account_id=='s3'))
        r.status='forged'
        db.commit()
    bad=ia.decision_brief('owner',i.id,offering_id=off.id)['metrics']['attendance.attendance_rate']
    assert bad['value'] is None
    assert bad['source_fingerprint_sha256'] is None
    assert bad['status']=='unavailable_or_untrusted_source'


def test_missing_internal_integrity_flags_deny_even_with_five_contributors():
    data={'institution_id':'uni-a','scope':{},
          'attendance':{'attendance_rate':100,'records':5},
          'results':{'pass_rate':100,'complete_results':5},
          '_metric_contributors':{'results.pass_rate':5,'attendance.attendance_rate':5}}
    metrics=InstitutionalAnalyticsService._governed_metrics(data,5)
    assert metrics['results.pass_rate']['value'] is None
    assert metrics['attendance.attendance_rate']['value'] is None


def test_identical_public_rates_in_separate_scopes_have_separate_fingerprints():
    data={'institution_id':'uni-a','scope':{'academic_period_id':'semester-a'},
          'results':{'pass_rate':100,'complete_results':5},
          '_metric_contributors':{'results.pass_rate':5},
          '_source_integrity':{'results.pass_rate':True}}
    digest1=InstitutionalAnalyticsService._governed_metrics(data,5)['results.pass_rate']['source_fingerprint_sha256']
    data['scope']={'academic_period_id':'semester-b'}
    digest2=InstitutionalAnalyticsService._governed_metrics(data,5)['results.pass_rate']['source_fingerprint_sha256']
    assert digest1 and digest2 and digest1!=digest2


def test_low_result_rate_from_partial_population_is_descriptive_not_a_management_alert():
    cs,ts,ass,gs,ops,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'s2','s3','s4','s5')
    _gradebook(ia,i,off,['student','s2','s3'],
        scores={'student':0,'s2':0,'s3':0})
    brief=ia.decision_brief('owner',i.id,offering_id=off.id)
    metric=brief['metrics']['results.pass_rate']
    assert metric['value']==0
    assert metric['population_reach']['status']=='limited_observed_population'
    assert not any(item['metric']=='results.pass_rate' for item in brief['findings'])

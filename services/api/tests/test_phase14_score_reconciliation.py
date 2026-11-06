"""Phase 14 v0.49.11: versioned grade provenance, full-detail reconciliation."""
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.shared.infrastructure.database import Base
from app.modules.assessment.domain.score_integrity import verified_auto_sum
from app.modules.assessment.application.service import AssessmentService
from app.modules.assessment.infrastructure.sqlalchemy_repo import (
    QuestionRow, BlueprintRow, AttemptRow, ResultRow, SqlAlchemyAssessmentRepository,
)
from app.modules.academic_delivery.infrastructure.sqlalchemy_repo import OfferingCurriculumLinkRow
from app.modules.pedagogical_intelligence.infrastructure import (
    SqlObjectiveEvidenceRepository, PedagogicalObjectiveRow,
    PedagogicalBlueprintOfferingRow, PedagogicalQuestionObjectiveRow,
)
from app.modules.pedagogical_intelligence.application.service import CanonicalPedagogicalIntelligenceService
from app.modules.campus.domain.model import CampusRole, MembershipState

NOW = datetime(2026, 10, 13, tzinfo=timezone.utc)


def _assessment(earned=100, possible=200, percent=50, passed=0, questions=None):
    return SimpleNamespace(earned=earned, possible=possible, percent=percent,
                           passed=passed, questions=questions if questions is not None else [
                               {'question_id':'q1','earned':100,'possible':100,'correct':True},
                               {'question_id':'q2','earned':0,'possible':100,'correct':False},
                           ])


def test_complete_auto_sum_verifier_accepts_valid_and_exacts():
    attempt=SimpleNamespace(question_ids=['q1','q2'])
    catalog={'q1':('cc1',100),'q2':('cc1',100)}
    assert verified_auto_sum(_assessment(),attempt,catalog,'cc1',60)
    assert not verified_auto_sum(_assessment(),attempt,catalog,'cc1',50)  # failed verdict contradicted by pass threshold
    # Genuine rounding: round(100/3) = 33 (no arbitrary tolerance for v1).
    p=_assessment(1,3,33,False,[{'question_id':'q1','earned':1,'possible':1,'correct':True},
                                {'question_id':'q2','earned':0,'possible':2,'correct':False}])
    assert verified_auto_sum(p,attempt,{'q1':('cc1',1),'q2':('cc1',2)},'cc1',60)


@pytest.mark.parametrize('change',[
    {'questions':[{'question_id':'q1','earned':100,'possible':100,'correct':True}]},
    {'questions':[{'question_id':'q1','earned':100,'possible':100,'correct':True}]*2},
    {'questions':[{'question_id':'q1','earned':100,'possible':100,'correct':True},
                  {'question_id':'foreign','earned':0,'possible':100,'correct':False}]},
    {'questions':[{'question_id':'q1','earned':100,'possible':100,'correct':False},
                  {'question_id':'q2','earned':0,'possible':100,'correct':False}]},
    {'earned':110}, {'earned':float('nan')}, {'possible':201}, {'percent':51},
    {'passed':1}, {'passed':'false'},
])
def test_contract_rejects_missing_duplicate_foreign_and_contradictory_results(change):
    data=vars(_assessment()).copy();data.update(change)
    assert not verified_auto_sum(SimpleNamespace(**data),SimpleNamespace(question_ids=['q1','q2']),
                                  {'q1':('cc1',100),'q2':('cc1',100)},'cc1',60)


def test_contract_rejects_catalog_drift_foreign_course_and_repeated_attempt_ids():
    grade=_assessment();a=SimpleNamespace(question_ids=['q1','q2'])
    assert not verified_auto_sum(grade,a,{'q1':('cc1',80),'q2':('cc1',100)},'cc1',60)
    assert not verified_auto_sum(grade,a,{'q1':('cc1',100),'q2':('cc2',100)},'cc1',60)
    assert not verified_auto_sum(grade,SimpleNamespace(question_ids=['q1','q1']),
                                 {'q1':('cc1',100)},'cc1',60)
    assert not verified_auto_sum(grade,a,{'q1':('cc1',100)},'cc1',60)


@pytest.fixture
def scoring_database(tmp_path):
    engine=create_engine(f"sqlite+pysqlite:///{tmp_path/'score.sqlite'}")
    Base.metadata.create_all(engine)
    sf=sessionmaker(bind=engine,expire_on_commit=False)
    with sf() as s:
        s.add_all([
            OfferingCurriculumLinkRow(id='link1',institution_id='i1',offering_id='off1',curriculum_id='cur1',curriculum_course_id='cc1',cohort_id='co1',bound_by='a1',bound_at=NOW),
            OfferingCurriculumLinkRow(id='link2',institution_id='i2',offering_id='off2',curriculum_id='cur2',curriculum_course_id='cc2',cohort_id='co2',bound_by='a2',bound_at=NOW),
            PedagogicalObjectiveRow(id='obj1',institution_id='i1',curriculum_course_id='cc1',objective_id='lo1',title='Learning objective'),
            PedagogicalObjectiveRow(id='obj2',institution_id='i2',curriculum_course_id='cc2',objective_id='lo2',title='Secret objective'),
            PedagogicalBlueprintOfferingRow(blueprint_id='bp1',institution_id='i1',offering_id='off1',curriculum_course_id='cc1'),
            PedagogicalBlueprintOfferingRow(blueprint_id='bp2',institution_id='i2',offering_id='off2',curriculum_course_id='cc2'),
            PedagogicalQuestionObjectiveRow(question_id='q1',institution_id='i1',curriculum_course_id='cc1',objective_id='lo1'),
            PedagogicalQuestionObjectiveRow(question_id='q2',institution_id='i1',curriculum_course_id='cc1',objective_id='lo1'),
            PedagogicalQuestionObjectiveRow(question_id='q3',institution_id='i2',curriculum_course_id='cc2',objective_id='lo2'),
            BlueprintRow(id='bp1',title='Grade',course_id='cc1',duration_minutes=30,question_count=2,pass_percent=60,shuffle=0,approved_only=0,row_version=1),
            BlueprintRow(id='bp2',title='Other grade',course_id='cc2',duration_minutes=30,question_count=1,pass_percent=60,shuffle=0,approved_only=0,row_version=1),
            *[QuestionRow(id=qid,bank_id='bank',course_id=course,chapter_id=None,kind='single',prompt='Q',choices=['True','False'],correct=['True'],explanation='',source_pages=[],provenance_sha256='0'*64,difficulty=1,approved=1,points=100)
              for qid,course in [('q1','cc1'),('q2','cc1'),('q3','cc2')]],
        ])
        for student in ('student1','student2','student3'):
            s.add(AttemptRow(id='attempt-'+student,account_id=student,blueprint_id='bp1',
                             question_ids=['q1','q2'],started_at=NOW,expires_at=NOW+timedelta(hours=1),
                             state='graded',answers=[],submitted_at=NOW+timedelta(minutes=5),row_version=2))
            s.add(ResultRow(attempt_id='attempt-'+student,earned=100,possible=200,percent=50,passed=0,
                            grading_contract_version=1,by_chapter={},by_bloom={},questions=_assessment().questions))
        s.add(AttemptRow(id='other-tenant',account_id='student-foreign',blueprint_id='bp2',
                         question_ids=['q3'],started_at=NOW,expires_at=NOW+timedelta(hours=1),
                         state='graded',answers=[],submitted_at=NOW,row_version=2))
        s.add(ResultRow(attempt_id='other-tenant',earned=100,possible=100,percent=100,passed=1,
                        grading_contract_version=1,by_chapter={},by_bloom={},
                        questions=[{'question_id':'q3','earned':100,'possible':100,'correct':True}]))
        s.commit()
    yield sf
    engine.dispose()


def _signals(sf, accounts=('student1','student2','student3')):
    return SqlObjectiveEvidenceRepository(sf).objective_signals('i1','off1',set(accounts))[0]


def test_sql_three_verified_grades_are_visible_and_complete(scoring_database):
    row=_signals(scoring_database)
    assert row['assessed_count']==3 and row['mean_score']==50
    assert row['evidence_integrity']=='verified_auto_sum'
    trends=SqlObjectiveEvidenceRepository(scoring_database).objective_trends('i1','off1',{'student1','student2','student3'})
    assert len(trends['timeline'])==1 and trends['timeline'][0]['evidence_integrity']=='verified_auto_sum'
    assert all(x['evidence_integrity']=='verified_auto_sum' for x in trends['recurrent_errors'])
    assert 'foreign' not in str(trends).lower() and 'Secret' not in str(trends)


@pytest.mark.parametrize('mutate',[
    lambda r:r.questions.pop(),
    lambda r:r.questions.append({'question_id':'q3','earned':100,'possible':100,'correct':True}),
    lambda r:setattr(r,'earned',110),
    lambda r:setattr(r,'percent',51),
    lambda r:setattr(r,'passed',1),
    lambda r:setattr(r,'grading_contract_version',2),
    lambda r:setattr(r,'questions',r.questions[:1]*2),
])
def test_sql_corrupt_or_unsupported_v1_grade_excluded_without_legacy_fallback(scoring_database,mutate):
    with scoring_database() as s:
        r=s.get(ResultRow,'attempt-student1')
        r.questions=[dict(x) for x in r.questions]
        mutate(r)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(r,'questions')
        s.commit()
    row=_signals(scoring_database)
    assert row['assessed_count']==2 and row['mean_score'] is None
    assert row['evidence_integrity']=='suppressed' and row['evidence_hash'] is None
    assert SqlObjectiveEvidenceRepository(scoring_database).objective_trends('i1','off1',{'student1','student2','student3'})['timeline']==()


def test_historical_partial_scores_kept_but_never_claimed_verified(scoring_database):
    with scoring_database() as s:
        for n in ('student1','student2','student3'):
            row=s.get(ResultRow,'attempt-'+n)
            row.grading_contract_version=0
            row.questions=[row.questions[0]]  # even if published total cannot be reconstructed
        s.commit()
    row=_signals(scoring_database)
    assert row['assessed_count']==3 and row['evidence_integrity']=='legacy_unverified'
    assert row['mean_score']==100  # limited question signal; NOT the official grade
    with scoring_database() as s:
        official=s.get(ResultRow,'attempt-student1')
        assert official.earned==100 and official.possible==200 and official.percent==50


def test_mixed_legacy_and_v1_tagged_without_inventing_missing_data(scoring_database):
    with scoring_database() as s:
        row=s.get(ResultRow,'attempt-student1')
        row.grading_contract_version=0
        row.questions=[row.questions[0]]
        s.commit()
    assert _signals(scoring_database)['evidence_integrity']=='mixed_verified_and_legacy'


def test_scoped_roster_and_suppression_hide_small_learner_results(scoring_database):
    row=_signals(scoring_database,('student1','student2'))
    assert row['assessed_count']==2 and row['evidence_integrity']=='suppressed'
    assert row['mean_score'] is None and row['question_evidence_count'] is None
    assert _signals(scoring_database,())['assessed_count']==0
    assert _signals(scoring_database)['learner_count']==3


class _Campus:
    def membership(self, institution, actor):
        if institution!='i1' or actor!='teacher': return None
        return SimpleNamespace(role=CampusRole.TEACHER,state=MembershipState.ACTIVE)
    def enrollments_for_cohort(self, cohort):
        return tuple(SimpleNamespace(student_account_id=f'student{i}',active=True,institution_id='i1') for i in range(1,4))

class _Teaching:
    def offering(self, institution, offering):
        return SimpleNamespace(cohort_id='co1') if institution=='i1' and offering=='off1' else None
    def assignment(self, offering, actor):
        return SimpleNamespace(active=True) if offering=='off1' and actor=='teacher' else None


def test_teacher_api_quality_labels_follow_rbac_and_tenant(scoring_database):
    service=CanonicalPedagogicalIntelligenceService(SqlObjectiveEvidenceRepository(scoring_database),_Campus(),_Teaching())
    report=service.objective_report('teacher','i1','off1')
    assert report['objectives'][0]['evidence_integrity']=='verified_auto_sum'
    dashboard=service.teaching_dashboard('teacher','i1','off1')
    assert dashboard['objectives'][0]['evidence_integrity']=='verified_auto_sum'
    assert 'student1' not in str(dashboard) and 'attempt-' not in str(dashboard)
    with pytest.raises(PermissionError): service.objective_report('intruder','i1','off1')
    with pytest.raises(ValueError): service.teaching_dashboard('teacher','i2','off2')


def test_production_sql_writer_sets_v2_only_after_atomic_grading(scoring_database):
    repo=SqlAlchemyAssessmentRepository(scoring_database)
    service=AssessmentService(repo,lambda:NOW+timedelta(minutes=10))
    attempt=service.start('student4','bp1')
    grade=service.submit('student4',attempt.id,attempt.row_version)
    assert grade.possible==200 and grade.percent==0
    with scoring_database() as s:
        saved=s.get(ResultRow,attempt.id)
        assert saved.grading_contract_version==2 and saved.earned==0
        assert saved.grading_snapshot is not None and len(saved.grading_snapshot_sha256)==64
        assert s.get(AttemptRow,attempt.id).state=='graded'
    with pytest.raises(ValueError):service.submit('student4',attempt.id,attempt.row_version)


def test_failed_grade_integrity_is_atomic_no_orphan_or_graded_attempt(scoring_database,monkeypatch):
    repo=SqlAlchemyAssessmentRepository(scoring_database)
    service=AssessmentService(repo,lambda:NOW+timedelta(minutes=10))
    attempt=service.start('student5','bp1')
    real_question=repo.question
    def forged(qid):
        question=real_question(qid)
        return replace(question,points=90) if qid=='q1' else question
    monkeypatch.setattr(repo,'question',forged)
    with pytest.raises(ValueError,match='assessment_auto_sum_integrity_required'):
        service.submit('student5',attempt.id,attempt.row_version)
    with scoring_database() as s:
        row=s.get(AttemptRow,attempt.id)
        assert row.state=='active' and row.row_version==1 and row.submitted_at is None
        assert s.get(ResultRow,attempt.id) is None


def test_legacy_quality_prevents_false_high_confidence_even_for_large_cohort(scoring_database):
    repo=SqlObjectiveEvidenceRepository(scoring_database)
    with scoring_database() as s:
        for n in ('student1','student2','student3'):
            r=s.get(ResultRow,'attempt-'+n)
            r.grading_contract_version=0
            r.questions=[r.questions[0]]
        s.commit()
    # Injectable active-roster extension: describe the real 3 learners, not
    # fabricated extra grade rows. A report must visibly warn the teacher.
    service=CanonicalPedagogicalIntelligenceService(repo,_Campus(),_Teaching())
    signal=service.objective_report('teacher','i1','off1')['objectives'][0]
    assert signal['evidence_integrity']=='legacy_unverified'
    assert signal['insight']['confidence']=='low'
    assert 'historiques' in signal['insight']['reason']


def test_direct_sql_writer_disallows_unverified_or_second_official_result(scoring_database):
    repo=SqlAlchemyAssessmentRepository(scoring_database)
    from app.modules.assessment.domain.model import ExamResult, QuestionResult
    q1=QuestionResult('q1',100,100,True,'',(),None)
    incomplete=ExamResult('attempt-student1',100,200,50,False,{},(q1,))
    with pytest.raises(ValueError,match='assessment_finalization_conflict'):
        repo.save_result(incomplete)
    # Use a separate graded attempt without a result to ensure full validation.
    with scoring_database() as s:
        s.add(AttemptRow(id='missing-grade',account_id='student6',blueprint_id='bp1',
                         question_ids=['q1','q2'],started_at=NOW,expires_at=NOW+timedelta(hours=1),
                         state='graded',answers=[],submitted_at=NOW,row_version=2))
        s.commit()
    incomplete=replace(incomplete,attempt_id='missing-grade')
    with pytest.raises(ValueError,match='assessment_auto_sum_integrity_required'):
        repo.save_result(incomplete)
    with scoring_database() as s:
        assert s.get(ResultRow,'missing-grade') is None


def test_source_scoring_rejects_cross_course_question_before_finalization(scoring_database):
    repo=SqlAlchemyAssessmentRepository(scoring_database)
    service=AssessmentService(repo,lambda:NOW+timedelta(minutes=10))
    attempt=service.start('student7','bp1')
    with scoring_database() as s:
        s.get(QuestionRow,'q2').course_id='cc2'
        s.commit()
    with pytest.raises(ValueError,match='assessment_invalid_grading_source'):
        service.submit('student7',attempt.id,attempt.row_version)
    with scoring_database() as s:
        assert s.get(AttemptRow,attempt.id).state=='active'
        assert s.get(ResultRow,attempt.id) is None

# v0.49.12 -- grading-time canonical snapshot: future catalog edits must not
# silently re-label an already checked automatic sum as invalid or as legacy.
from app.modules.assessment.domain.score_integrity import (
    make_auto_sum_snapshot, snapshot_digest, verified_snapshot_auto_sum,
)
from sqlalchemy.orm.attributes import flag_modified


def _produce_v2(sf, account='student4'):
    repo=SqlAlchemyAssessmentRepository(sf)
    service=AssessmentService(repo,lambda:NOW+timedelta(minutes=10))
    attempt=service.start(account,'bp1')
    result=service.submit(account,attempt.id,attempt.row_version)
    return attempt.id,result


def _replace_three_v2_results(sf):
    """Grade 3 students through the real SQL writer, not a forged grade JSON."""
    with sf() as s:
        for n in ('student1','student2','student3'):
            s.delete(s.get(ResultRow,'attempt-'+n))
            s.delete(s.get(AttemptRow,'attempt-'+n))
        s.commit()
    return [_produce_v2(sf,n)[0] for n in ('student1','student2','student3')]


def test_v2_snapshot_created_in_sql_transaction_and_matches_authoritative_catalog(scoring_database):
    attempt_id, result = _produce_v2(scoring_database)
    with scoring_database() as s:
        a=s.get(AttemptRow,attempt_id)
        r=s.get(ResultRow,attempt_id)
        assert r.grading_contract_version == 2
        assert r.grading_snapshot['attempt_id']==attempt_id
        assert r.grading_snapshot['blueprint_id']=='bp1'
        assert r.grading_snapshot['curriculum_course_id']=='cc1'
        assert r.grading_snapshot['pass_percent']==60
        assert [q['points'] for q in r.grading_snapshot['questions']] == [100,100]
        assert r.grading_snapshot_sha256==snapshot_digest(r.grading_snapshot)
        assert verified_snapshot_auto_sum(r,a,'cc1')==(True, {'q1':100,'q2':100})
        assert verified_snapshot_auto_sum(r,a,'cc2')==(False,{})
        assert result.percent==0


def test_v2_historical_evidence_survives_question_point_edits_and_deletion(scoring_database):
    _replace_three_v2_results(scoring_database)
    before=_signals(scoring_database)
    assert before['evidence_integrity']=='verified_snapshot_v2'
    assert before['assessed_count']==3 and before['mean_score']==0
    with scoring_database() as s:
        s.get(QuestionRow,'q1').points=999
        s.delete(s.get(QuestionRow,'q2'))
        s.commit()
    after=_signals(scoring_database)
    assert after['assessed_count']==3 and after['mean_score']==0
    assert after['evidence_integrity']=='verified_snapshot_v2'
    trends=SqlObjectiveEvidenceRepository(scoring_database).objective_trends(
        'i1','off1',{'student1','student2','student3'})
    assert len(trends['timeline'])==1
    assert trends['timeline'][0]['evidence_integrity']=='verified_snapshot_v2'


def test_v2_keeps_original_blueprint_pass_threshold_without_mutating_grade(scoring_database):
    ids=_replace_three_v2_results(scoring_database)
    before=_signals(scoring_database)
    with scoring_database() as s:
        s.get(BlueprintRow,'bp1').pass_percent=0
        s.commit()
    after=_signals(scoring_database)
    assert after['assessed_count']==3 and after['evidence_integrity']=='verified_snapshot_v2'
    assert after['mean_score']==before['mean_score']
    with scoring_database() as s:
        assert s.get(ResultRow,ids[0]).passed==0


def test_v1_remains_current_catalog_dependent_not_fabricated_as_v2(scoring_database):
    assert _signals(scoring_database)['evidence_integrity']=='verified_auto_sum'
    with scoring_database() as s:
        s.get(QuestionRow,'q1').points=90
        s.commit()
    assert _signals(scoring_database)['assessed_count']==0


@pytest.mark.parametrize('alter',[
    lambda r: setattr(r,'grading_snapshot_sha256','0'*64),
    lambda r: r.grading_snapshot['questions'][0].update(points=50),
    lambda r: r.grading_snapshot.update(pass_percent=101),
    lambda r: r.grading_snapshot.update(curriculum_course_id='cc2'),
    lambda r: r.grading_snapshot.update(blueprint_id='bp2'),
    lambda r: r.grading_snapshot.update(attempt_id='foreign-attempt'),
    lambda r: r.grading_snapshot['questions'].append(dict(r.grading_snapshot['questions'][0])),
    lambda r: r.grading_snapshot.update(schema=3),
    lambda r: r.grading_snapshot.update(extra_property=True),
    lambda r: setattr(r,'percent',95),
    lambda r: r.questions.pop(),
    lambda r: setattr(r,'grading_contract_version',3),
    lambda r: setattr(r,'grading_snapshot',None),
])
def test_v2_tampering_fails_closed_without_old_grade_fallback(scoring_database,alter):
    ids=_replace_three_v2_results(scoring_database)
    with scoring_database() as s:
        r=s.get(ResultRow,ids[0])
        r.grading_snapshot={**r.grading_snapshot,'questions':[dict(x) for x in r.grading_snapshot['questions']]}
        r.questions=[dict(x) for x in r.questions]
        alter(r)
        if isinstance(r.grading_snapshot,dict):flag_modified(r,'grading_snapshot')
        flag_modified(r,'questions')
        s.commit()
    row=_signals(scoring_database)
    assert row['assessed_count']==2 and row['evidence_integrity']=='suppressed'
    assert row['mean_score'] is None and row['evidence_hash'] is None
    assert SqlObjectiveEvidenceRepository(scoring_database).objective_trends(
        'i1','off1',{'student1','student2','student3'})['timeline']==()


def test_v2_recomputed_digest_cannot_authorize_cross_course_or_bad_points(scoring_database):
    ids=_replace_three_v2_results(scoring_database)
    with scoring_database() as s:
        r=s.get(ResultRow,ids[0]);snap={**r.grading_snapshot,
            'questions':[dict(row) for row in r.grading_snapshot['questions']]}
        snap['questions'][0]['course_id']='cc2'
        r.grading_snapshot=snap
        r.grading_snapshot_sha256=snapshot_digest(snap)
        s.commit()
    assert _signals(scoring_database)['assessed_count']==2
    with scoring_database() as s:
        r=s.get(ResultRow,ids[0]);snap={**r.grading_snapshot,
            'questions':[dict(row) for row in r.grading_snapshot['questions']]}
        snap['questions'][0]['course_id']='cc1'
        snap['questions'][0]['points']=5
        r.grading_snapshot=snap
        r.grading_snapshot_sha256=snapshot_digest(snap)
        s.commit()
    assert _signals(scoring_database)['assessed_count']==2


def test_v2_cross_tenant_teacher_and_small_cohort_guardrails(scoring_database):
    _replace_three_v2_results(scoring_database)
    service=CanonicalPedagogicalIntelligenceService(
        SqlObjectiveEvidenceRepository(scoring_database),_Campus(),_Teaching())
    report=service.objective_report('teacher','i1','off1')
    assert report['objectives'][0]['evidence_integrity']=='verified_snapshot_v2'
    assert 'attempt-' not in str(report) and 'student' not in str(report)
    with pytest.raises(PermissionError): service.objective_report('intruder','i1','off1')
    with pytest.raises(ValueError): service.objective_report('teacher','i2','off2')
    suppressed=_signals(scoring_database,('student1','student2'))
    assert suppressed['assessed_count']==2 and suppressed['evidence_integrity']=='suppressed'
    assert suppressed['mean_score'] is None and suppressed['evidence_hash'] is None
    trends=SqlObjectiveEvidenceRepository(scoring_database).objective_trends('i1','off1',{'student1','student2'})
    assert trends['timeline']==() and trends['recurrent_errors']==()


def test_v2_and_v1_in_same_cohort_are_identified_as_mixed_verified(scoring_database):
    with scoring_database() as s:
        s.delete(s.get(ResultRow,'attempt-student1'))
        s.delete(s.get(AttemptRow,'attempt-student1'))
        s.commit()
    _produce_v2(scoring_database,'student1')
    row=_signals(scoring_database)
    assert row['assessed_count']==3 and row['evidence_integrity']=='mixed_verified_contracts'
    with scoring_database() as s:
        r=s.get(ResultRow,'attempt-student2')
        r.grading_contract_version=0
        s.commit()
    assert _signals(scoring_database)['evidence_integrity']=='mixed_verified_and_legacy'


def test_v2_snapshot_independent_of_exposed_current_catalog_for_deleted_question(scoring_database):
    aid,_=_produce_v2(scoring_database)
    with scoring_database() as s:
        s.delete(s.get(QuestionRow,'q1'))
        s.delete(s.get(QuestionRow,'q2'))
        s.commit()
    with scoring_database() as s:
        r=s.get(ResultRow,aid);a=s.get(AttemptRow,aid)
        assert verified_snapshot_auto_sum(r,a,'cc1')[0]
        assert r.earned==0 and r.possible==200


def test_v2_student_grade_snapshot_survives_current_question_course_reassignment(scoring_database):
    _replace_three_v2_results(scoring_database)
    with scoring_database() as s:
        s.get(QuestionRow,'q1').course_id='cc2'
        s.commit()
    # A valid *previously graded* cc1 attempt retains its cc1 mapping and points.
    # A *new* attempt will fail source-course checks (covered in earlier tests).
    row=_signals(scoring_database)
    assert row['assessed_count']==3 and row['evidence_integrity']=='verified_snapshot_v2'
    assert SqlObjectiveEvidenceRepository(scoring_database).objective_signals(
        'i2','off2',{'student1','student2','student3'})[0]['assessed_count']==0


def test_forbidden_result_id_or_blueprint_swap_is_atomic_on_direct_repository_write(scoring_database):
    from app.modules.assessment.domain.model import ExamResult,QuestionResult,AttemptState
    repo=SqlAlchemyAssessmentRepository(scoring_database)
    service=AssessmentService(repo,lambda:NOW+timedelta(minutes=10))
    original=service.start('student-forged','bp1')
    grade=ExamResult(original.id,0,200,0,False,{},(
        QuestionResult('q1',0,100,False,'',(),None),
        QuestionResult('q2',0,100,False,'',(),None)))
    ready=replace(original,state=AttemptState.GRADED,submitted_at=NOW+timedelta(minutes=10),row_version=2)
    with pytest.raises(ValueError,match='assessment_auto_sum_integrity_required'):
        repo.save_graded_attempt_result(ready,replace(grade,attempt_id='other-attempt'))
    with pytest.raises(ValueError,match='assessment_finalization_conflict'):
        repo.save_graded_attempt_result(replace(ready,blueprint_id='bp2'),grade)
    with scoring_database() as s:
        assert s.get(AttemptRow,original.id).state=='active'
        assert s.get(ResultRow,original.id) is None
        assert s.get(ResultRow,'other-attempt') is None


def test_snapshot_verifier_accepts_domain_attempt_tuple_as_well_as_sql_list(scoring_database):
    aid,_=_produce_v2(scoring_database)
    with scoring_database() as s:
        row=s.get(ResultRow,aid)
        attempt=s.get(AttemptRow,aid)
        from types import SimpleNamespace
        snapshot_attempt=SimpleNamespace(blueprint_id=attempt.blueprint_id,
                                         question_ids=tuple(attempt.question_ids))
        assert verified_snapshot_auto_sum(row,snapshot_attempt,'cc1')[0]


def test_snapshot_rejects_boolean_points_even_when_fingerprint_matches(scoring_database):
    aid,_=_produce_v2(scoring_database)
    with scoring_database() as s:
        row=s.get(ResultRow,aid)
        attempt=s.get(AttemptRow,aid)
        corrupt={**row.grading_snapshot,
                 'questions':[dict(x) for x in row.grading_snapshot['questions']]}
        corrupt['questions'][0]['points']=True
        row.grading_snapshot=corrupt
        row.grading_snapshot_sha256=snapshot_digest(corrupt)
        s.flush()
        assert verified_snapshot_auto_sum(row,attempt,'cc1')==(False,{})

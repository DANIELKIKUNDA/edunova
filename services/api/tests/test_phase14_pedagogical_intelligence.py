import pytest
from app.modules.pedagogical_intelligence.application.service import PedagogicalIntelligenceService
from app.modules.pedagogical_intelligence.domain.model import LearningSignal

def test_collect_more_evidence_prevents_overclaim():
 r=PedagogicalIntelligenceService().analyze([LearningSignal('o1',20,4,40,3,90)])
 assert r.predictive_model is False and r.insights[0].action=='collect_more_evidence' and r.insights[0].confidence=='low'
def test_collective_weakness_recommends_reteach():
 r=PedagogicalIntelligenceService().analyze([LearningSignal('o1',20,18,55,9,88)])
 assert r.insights[0].action=='reteach_and_check' and r.insights[0].confidence=='high'
def test_attendance_signal_does_not_diagnose():
 r=PedagogicalIntelligenceService().analyze([LearningSignal('o1',10,8,75,1,55)])
 assert r.insights[0].action=='address_participation' and 'diagnos' not in r.insights[0].reason.lower()
def test_invalid_aggregates_rejected():
 with pytest.raises(ValueError):PedagogicalIntelligenceService().analyze([LearningSignal('o',3,4,50,0,None)])

from app.modules.pedagogical_intelligence.application.service import CanonicalPedagogicalIntelligenceService

class Obj:
 def __init__(self,**kw):self.__dict__.update(kw)
class Repo:
 def offering_signal(self,i,o,allowed_accounts=None):return {'objective_id':'cc1','learner_count':20,'assessed_count':18,'mean_score':55.0,'failure_count':9,'attendance_rate':88.0,'published_result_count':18,'closed_attendance_sessions':4,'attendance_record_count':72,'evidence':('result:r1:h1',),'curriculum_course_id':'cc1'}
class Campus:
 def __init__(self,role='teacher',state='active'):self.role=role;self.state=state
 def membership(self,i,a):
  from app.modules.campus.domain.model import CampusRole,MembershipState
  return Obj(role=CampusRole(self.role),state=MembershipState(self.state))
 def enrollments_for_cohort(self,c):return (Obj(student_account_id='student1',active=True,institution_id='i1'),)
class Teaching:
 def offering(self,i,o):return Obj(id=o,cohort_id='c1')
 def assignment(self,o,a):return Obj(active=True) if a=='teacher' else None

def test_canonical_report_is_course_scoped_and_explainable():
 s=CanonicalPedagogicalIntelligenceService(Repo(),Campus(),Teaching())
 r=s.offering_report('teacher','i1','o1')
 assert r['scope']=='curriculum_course' and r['insight']['action']=='reteach_and_check'
 assert r['predictive_model'] is False and 'objective-level' in r['limitations'][0]

def test_canonical_report_rejects_student_access():
 s=CanonicalPedagogicalIntelligenceService(Repo(),Campus('student'),Teaching())
 with pytest.raises(PermissionError):s.offering_report('student','i1','o1')

class ObjectiveRepo(Repo):
 def objective_signals(self,i,o,allowed_accounts=None):return ({'objective_id':'lo1','objective_title':'Résoudre une équation','learner_count':10,'assessed_count':10,'mean_score':52.0,'failure_count':6,'attendance_rate':None,'question_evidence_count':20,'evidence':('assessment:a1:q1:0/1',)},)
 def upsert_objective(self,*a):self.registered=a
 def map_question(self,*a):self.mapped=a
 def bind_blueprint(self,*a):self.bound=a

def test_objective_report_uses_explicit_question_evidence_only():
 s=CanonicalPedagogicalIntelligenceService(ObjectiveRepo(),Campus(),Teaching());r=s.objective_report('teacher','i1','o1')
 assert r['scope']=='learning_objective' and r['objectives'][0]['objective_id']=='lo1'
 assert r['objectives'][0]['insight']['action']=='reteach_and_check' and r['predictive_model'] is False

def test_objective_mapping_management_is_staff_guarded():
 repo=ObjectiveRepo();s=CanonicalPedagogicalIntelligenceService(repo,Campus(),Teaching())
 assert s.register_objective('teacher','i1','o1','lo1','Objectif')['objective_id']=='lo1'
 assert s.map_question('teacher','i1','o1','lo1','q1')['mapped'] is True
 assert s.bind_blueprint('teacher','i1','o1','b1')['bound'] is True
 with pytest.raises(PermissionError):CanonicalPedagogicalIntelligenceService(repo,Campus('student'),Teaching()).register_objective('student','i1','o1','x','X')


class TrendRepo(ObjectiveRepo):
 def objective_trends(self,i,o,allowed_accounts=None):
  return {'timeline':({'blueprint_id':'b1','objective_id':'lo1','objective_title':'Résoudre une équation','assessed_count':10,'mean_score':45.0,'failure_count':7},{'blueprint_id':'b2','objective_id':'lo1','objective_title':'Résoudre une équation','assessed_count':10,'mean_score':68.0,'failure_count':3}), 'recurrent_errors':({'objective_id':'lo1','objective_title':'Résoudre une équation','question_id':'q7','affected_learner_count':5,'interpretation':'recurrent_incorrect_response','diagnosis':False},)}

def test_teacher_dashboard_exposes_descriptive_trends_without_diagnosis():
 r=CanonicalPedagogicalIntelligenceService(TrendRepo(),Campus(),Teaching()).teaching_dashboard('teacher','i1','o1')
 assert r['scope']=='teacher_dashboard' and r['predictive_model'] is False
 assert len(r['assessment_timeline'])==2 and r['recurrent_errors'][0]['diagnosis'] is False
 assert any('psychometrically' in x for x in r['guardrails'])

def test_teacher_dashboard_is_staff_guarded():
 with pytest.raises(PermissionError):CanonicalPedagogicalIntelligenceService(TrendRepo(),Campus('student'),Teaching()).teaching_dashboard('student','i1','o1')


class DashboardRepo(TrendRepo):
 def objective_signals(self,i,o,allowed_accounts=None):
  return (
   {'objective_id':'lo-high','objective_title':'Objectif fragile','learner_count':10,'assessed_count':10,'mean_score':48.0,'failure_count':7,'attendance_rate':None,'question_evidence_count':10,'evidence':('e1',)},
   {'objective_id':'lo-ok','objective_title':'Objectif maîtrisé','learner_count':10,'assessed_count':10,'mean_score':82.0,'failure_count':1,'attendance_rate':None,'question_evidence_count':10,'evidence':('e2',)},
  )

def test_teacher_dashboard_prioritizes_explainable_actions():
 r=CanonicalPedagogicalIntelligenceService(DashboardRepo(),Campus(),Teaching()).teaching_dashboard('teacher','i1','o1')
 assert r['summary']['objective_count']==2 and r['summary']['high_priority_count']==1
 assert r['objectives'][0]['objective_id']=='lo-high' and r['objectives'][0]['priority']=='high'
 assert r['priority_actions'][0]['action']=='reteach_and_check'
 assert r['priority_actions'][0]['confidence']=='high'

def test_teacher_dashboard_does_not_turn_normal_objectives_into_actions():
 r=CanonicalPedagogicalIntelligenceService(DashboardRepo(),Campus(),Teaching()).teaching_dashboard('teacher','i1','o1')
 assert all(x['objective_id']!='lo-ok' for x in r['priority_actions'])
 assert r['predictive_model'] is False


class FilteringRepo(DashboardRepo):
 def __init__(self):self.allowed_signals=None;self.allowed_trends=None
 def objective_signals(self,i,o,allowed_accounts=None):
  self.allowed_signals=set(allowed_accounts or ());return super().objective_signals(i,o,allowed_accounts)
 def objective_trends(self,i,o,allowed_accounts=None):
  self.allowed_trends=set(allowed_accounts or ());return super().objective_trends(i,o,allowed_accounts)

def test_dashboard_scopes_evidence_to_active_offering_enrollment():
 repo=FilteringRepo();CanonicalPedagogicalIntelligenceService(repo,Campus(),Teaching()).teaching_dashboard('teacher','i1','o1')
 assert repo.allowed_signals=={'student1'} and repo.allowed_trends=={'student1'}

def test_teacher_from_other_institution_is_rejected_even_if_assignment_id_collides():
 class WrongTenantTeaching(Teaching):
  def offering(self,i,o):return None
 with pytest.raises(ValueError):CanonicalPedagogicalIntelligenceService(DashboardRepo(),Campus(),WrongTenantTeaching()).teaching_dashboard('teacher','i2','o1')

def test_dashboard_never_exposes_per_learner_identity_fields():
 r=CanonicalPedagogicalIntelligenceService(DashboardRepo(),Campus(),Teaching()).teaching_dashboard('teacher','i1','o1')
 payload=str(r).lower()
 assert 'student_account_id' not in payload and 'account_id' not in payload and 'attempt_id' not in payload

from app.modules.pedagogical_intelligence.infrastructure import SqlObjectiveEvidenceRepository, PedagogicalQuestionObjectiveRow, PedagogicalBlueprintOfferingRow
from app.modules.assessment.infrastructure.sqlalchemy_repo import QuestionRow, BlueprintRow

class _ConflictSession:
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def scalar(self,q):return Obj(objective_id='lo1')
 def get(self,model,key):
  if model is QuestionRow:return Obj(course_id='cc1')
  if model is BlueprintRow:return Obj(course_id='cc1')
  if model is PedagogicalQuestionObjectiveRow:return Obj(institution_id='other',curriculum_course_id='cc1',objective_id='lo1')
  if model is PedagogicalBlueprintOfferingRow:return Obj(institution_id='i1',offering_id='other-offering',curriculum_course_id='cc1')
  return None
 def merge(self,*a):raise AssertionError('conflicting binding must not be overwritten')
 def commit(self):raise AssertionError('conflicting binding must not commit')
class _ConflictSF:
 def __call__(self):return _ConflictSession()

def test_question_mapping_conflict_cannot_hijack_other_tenant_mapping():
 with pytest.raises(ValueError,match='pedintel_question_mapping_conflict'):
  SqlObjectiveEvidenceRepository(_ConflictSF()).map_question('i1','cc1','lo1','q1')

def test_blueprint_binding_conflict_cannot_move_assessment_between_offerings():
 with pytest.raises(ValueError,match='pedintel_blueprint_binding_conflict'):
  SqlObjectiveEvidenceRepository(_ConflictSF()).bind_blueprint('i1','o1','cc1','b1')

# v0.49.6: real SQL projection / adversarial regression, not mocked repository calls.
import math
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.shared.infrastructure.database import Base
from app.modules.academic_delivery.infrastructure.sqlalchemy_repo import OfferingCurriculumLinkRow
from app.modules.assessment.infrastructure.sqlalchemy_repo import AttemptRow, ResultRow
from app.modules.pedagogical_intelligence.infrastructure import (
    PedagogicalObjectiveRow, _question_result_rows,
)

@pytest.fixture
def sql_evidence(tmp_path):
    engine=create_engine(f"sqlite+pysqlite:///{tmp_path/'pedintel.sqlite'}")
    Base.metadata.create_all(engine)
    sf=sessionmaker(bind=engine,expire_on_commit=False)
    now=datetime(2026,10,13,tzinfo=timezone.utc)
    with sf() as s:
        s.add_all([
            OfferingCurriculumLinkRow(id='link1',institution_id='i1',offering_id='o1',curriculum_id='c1',curriculum_course_id='cc1',cohort_id='cohort1',bound_by='registrar',bound_at=now),
            OfferingCurriculumLinkRow(id='link2',institution_id='i2',offering_id='o2',curriculum_id='c2',curriculum_course_id='cc2',cohort_id='cohort2',bound_by='registrar',bound_at=now),
            PedagogicalObjectiveRow(id='obj1',institution_id='i1',curriculum_course_id='cc1',objective_id='lo1',title='Objective 1'),
            PedagogicalObjectiveRow(id='obj2',institution_id='i1',curriculum_course_id='cc1',objective_id='lo2',title='Without evidence'),
            PedagogicalObjectiveRow(id='obj3',institution_id='i2',curriculum_course_id='cc2',objective_id='secret-lo',title='Other tenant'),
            PedagogicalBlueprintOfferingRow(blueprint_id='bp1',institution_id='i1',offering_id='o1',curriculum_course_id='cc1'),
            PedagogicalBlueprintOfferingRow(blueprint_id='bp2',institution_id='i2',offering_id='o2',curriculum_course_id='cc2'),
            PedagogicalQuestionObjectiveRow(question_id='q1',institution_id='i1',curriculum_course_id='cc1',objective_id='lo1'),
            PedagogicalQuestionObjectiveRow(question_id='q2',institution_id='i1',curriculum_course_id='cc1',objective_id='lo1'),
            PedagogicalQuestionObjectiveRow(question_id='secret-q',institution_id='i2',curriculum_course_id='cc2',objective_id='secret-lo'),
            BlueprintRow(id='bp1',title='Exam',course_id='cc1',duration_minutes=30,question_count=2,pass_percent=60,shuffle=0,approved_only=0,row_version=1),
            BlueprintRow(id='bp2',title='Foreign exam',course_id='cc2',duration_minutes=30,question_count=1,pass_percent=60,shuffle=0,approved_only=0,row_version=1),
            *[QuestionRow(id=qid,bank_id='bank',course_id=course,chapter_id=None,kind='single',prompt='Q',choices=[],correct=[],explanation='',source_pages=[],provenance_sha256='0'*64,difficulty=1,approved=1,points=100)
              for qid,course in [('q1','cc1'),('q2','cc1'),('secret-q','cc2')]],
        ])
        for aid,actor,bp,questions,state in [
            ('a1','learner1','bp1',['q1'],'graded'),
            ('a2','learner2','bp1',['q1','q2'],'graded'),
            ('a3','learner3','bp1',['q1'],'graded'),
            ('ax','outsider','bp1',['q1'],'graded'),
            ('at','other-tenant-student','bp2',['secret-q'],'graded'),
            ('unfinished','learner3','bp1',['q1'],'in_progress')]:
            s.add(AttemptRow(id=aid,account_id=actor,blueprint_id=bp,question_ids=questions,started_at=now,expires_at=now+timedelta(days=1),state=state,answers=[],submitted_at=now,row_version=1))
        for aid,questions in [
            ('a1',[{'question_id':'q1','earned':30,'possible':100}, {'question_id':'q2','earned':100,'possible':100}]), # forged, not attempted q2
            ('a2',[{'question_id':'q1','earned':50,'possible':100}, {'question_id':'q2','earned':float('nan'),'possible':100}]),
            ('a3',[{'question_id':'q1','earned':40,'possible':100}]),
            ('ax',[{'question_id':'q1','earned':100,'possible':100}]),
            ('at',[{'question_id':'secret-q','earned':0,'possible':100}]),
            ('unfinished',[{'question_id':'q1','earned':90,'possible':100}]),
        ]:
            s.add(ResultRow(attempt_id=aid,earned=0,possible=100,percent=0,passed=0,by_chapter={},by_bloom={},questions=questions))
        s.commit()
    yield sf
    engine.dispose()


def test_sql_projection_enrollment_is_denominator_not_just_graded_accounts(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    rows=repo.objective_signals('i1','o1',{'learner1','learner2','learner3','inactive-without-attempt'})
    by_id={r['objective_id']:r for r in rows}
    assert set(by_id)=={'lo1','lo2'}
    assert by_id['lo1']['learner_count']==4 and by_id['lo1']['assessed_count']==3
    assert by_id['lo1']['mean_score']==pytest.approx(40)
    assert by_id['lo1']['failure_count']==3
    assert by_id['lo1']['question_evidence_count']==3  # excludes forged & NaN entries
    assert by_id['lo2']['learner_count']==4 and by_id['lo2']['assessed_count']==0
    assert by_id['lo2']['mean_score'] is None
    assert all(r.get('objective_title')!='Other tenant' for r in rows)


def test_sql_projection_zero_authorized_accounts_reads_no_results(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    rows=repo.objective_signals('i1','o1',set())
    assert all(r['learner_count']==0 and r['assessed_count']==0 for r in rows)
    trends=repo.objective_trends('i1','o1',set())
    assert trends=={'timeline':(), 'recurrent_errors':()}


def test_sql_trends_are_offering_scoped_with_group_threshold(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    trends=repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})
    assert len(trends['timeline'])==1
    assert trends['timeline'][0]['mean_score']==pytest.approx(40)
    assert trends['timeline'][0]['assessed_count']==3
    assert len(trends['recurrent_errors'])==1
    assert trends['recurrent_errors'][0]['question_id']=='q1'
    assert trends['recurrent_errors'][0]['affected_learner_count']==3
    assert 'secret' not in str(trends).lower() and 'outsider' not in str(trends).lower()


def test_sql_trends_suppress_small_groups_and_ungraded_attempts(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    trends=repo.objective_trends('i1','o1',{'learner1','learner2'})
    assert trends['recurrent_errors']==()
    assert trends['timeline']==()  # small-cell suppression


def test_result_json_forgery_duplicates_and_invalid_scores_are_rejected():
    allowed=['q1','q2','q3']
    raw=[{'question_id':'q1','possible':10,'earned':2},
         {'question_id':'q1','possible':10,'earned':8},  # both duplicate entries discarded
         {'question_id':'q2','possible':10,'earned':11}, # earned greater than possible
         {'question_id':'q3','possible':10,'earned':3},
         {'question_id':'evil','possible':10,'earned':0},
         {'question_id':'q4','possible':100,'earned':99},
         None, 42]
    assert _question_result_rows(raw,allowed)==(('q3',3.0,10.0),)
    assert _question_result_rows({'question_id':'q3'}, allowed)==()
    assert _question_result_rows(raw,[])==()


@pytest.mark.parametrize('earned,possible',[
    (float('nan'),10),(float('inf'),10),(5,float('inf')),(5,float('nan')),
    (-1,10),(11,10),(1,0),(True,10),(1,False),('5',10),
])
def test_bad_question_result_values_never_become_evidence(earned,possible):
    assert _question_result_rows([{'question_id':'q1','earned':earned,'possible':possible}],['q1'])==()


@pytest.mark.parametrize('field', ['mean_score','attendance_rate'])
@pytest.mark.parametrize('value',[float('nan'),float('inf'),float('-inf')])
def test_rule_engine_rejects_nonfinite_signal(field,value):
    args=dict(objective_id='o1',learner_count=5,assessed_count=4,mean_score=50.0,failure_count=2,attendance_rate=80.0)
    args[field]=value
    with pytest.raises(ValueError,match='pedintel_invalid_'):
        PedagogicalIntelligenceService().analyze([LearningSignal(**args)])


def test_teacher_dashboard_distinguishes_unassessed_from_watch():
    class MissingEvidenceRepo(DashboardRepo):
        def objective_signals(self,*args,**kw):
            return ({'objective_id':'lo-missing','objective_title':'Not evaluated','learner_count':10,'assessed_count':0,'mean_score':None,'failure_count':0,'attendance_rate':None},)
    dashboard=CanonicalPedagogicalIntelligenceService(MissingEvidenceRepo(),Campus(),Teaching()).teaching_dashboard('teacher','i1','o1')
    assert dashboard['summary']['watch_count']==0
    assert dashboard['summary']['unassessed_count']==1
    assert dashboard['objectives'][0]['priority']=='unassessed'
    assert dashboard['priority_actions'][0]['action']=='collect_more_evidence'


def test_atomic_mapping_and_binding_are_idempotent_and_cannot_be_reassigned(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    # Exercise the actual SQLite atomic insert/no-update path and idempotent retries.
    from app.modules.assessment.infrastructure.sqlalchemy_repo import QuestionRow, BlueprintRow
    with sql_evidence() as s:
        s.add(QuestionRow(id='qnew',bank_id='bank',course_id='cc1',chapter_id=None,kind='mcq',prompt='Q',choices=[],correct=[],explanation='',source_pages=[],provenance_sha256='0'*64,difficulty=1,approved=1,points=1))
        s.add(BlueprintRow(id='bpnew',title='Blueprint',course_id='cc1',duration_minutes=30,question_count=1,pass_percent=60,shuffle=0,approved_only=0,row_version=1))
        s.commit()
    repo.map_question('i1','cc1','lo1','qnew')
    repo.map_question('i1','cc1','lo1','qnew')
    repo.bind_blueprint('i1','o1','cc1','bpnew')
    repo.bind_blueprint('i1','o1','cc1','bpnew')
    with pytest.raises(ValueError,match='pedintel_question_mapping_conflict'):
        repo.map_question('i1','cc1','lo2','qnew')
    with pytest.raises(ValueError,match='pedintel_blueprint_binding_conflict'):
        repo.bind_blueprint('i1','different-offering','cc1','bpnew')
    with sql_evidence() as s:
        assert s.get(PedagogicalQuestionObjectiveRow,'qnew').objective_id=='lo1'
        assert s.get(PedagogicalBlueprintOfferingRow,'bpnew').offering_id=='o1'


def test_sql_tenant_and_offering_scope_are_fail_closed(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with pytest.raises(ValueError,match='pedintel_offering_curriculum_link_required'):
        repo.objective_signals('i2','o1',{'learner1'})
    with pytest.raises(ValueError,match='pedintel_offering_curriculum_link_required'):
        repo.objective_trends('i2','o1',{'learner1'})


def test_sql_aggregates_suppress_one_or_two_learners_and_provenance(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    for allowed in ({'learner1'},{'learner1','learner2'}):
        row=next(x for x in repo.objective_signals('i1','o1',allowed) if x['objective_id']=='lo1')
        assert row['aggregate_suppressed'] is True
        assert row['mean_score'] is None and row['failure_count']==0
        assert row['evidence_hash'] is None and row['question_evidence_count'] is None
        assert repo.objective_trends('i1','o1',allowed)['timeline']==()


def test_rule_engine_does_not_infer_from_single_learner():
    signal=LearningSignal('lo1',1,1,10,1,None)
    insight=PedagogicalIntelligenceService().analyze([signal]).insights[0]
    assert insight.action=='collect_more_evidence' and insight.confidence=='low'


def test_course_report_suppresses_small_cohort_results():
    class SmallCourseRepo(Repo):
        def offering_signal(self,i,o,allowed_accounts=None):
            return {**super().offering_signal(i,o,allowed_accounts),'learner_count':1,'assessed_count':1,'mean_score':20.0,'failure_count':1,'attendance_rate':25.0}
    report=CanonicalPedagogicalIntelligenceService(SmallCourseRepo(),Campus(),Teaching()).offering_report('teacher','i1','o1')
    assert report['signal']['aggregate_suppressed'] is True
    assert report['signal']['mean_score'] is None and report['signal']['attendance_rate'] is None
    assert report['insight']['action']=='collect_more_evidence'
    assert report['evidence'][0]['evidence_hash'] is None


def test_empty_cohort_dashboard_exposes_no_null_action():
    class EmptyRepo(TrendRepo):
        def objective_signals(self,*args,**kw):
            return ({'objective_id':'lo0','objective_title':'No active students','learner_count':0,'assessed_count':0,'mean_score':None,'failure_count':0,'attendance_rate':None},)
    report=CanonicalPedagogicalIntelligenceService(EmptyRepo(),Campus(),Teaching()).teaching_dashboard('teacher','i1','o1')
    assert report['summary']['unassessed_count']==1
    assert report['priority_actions']==()

# v0.49.7: course-level canonical cohort and attendance completeness regression.
from app.modules.academic_delivery.infrastructure.sqlalchemy_repo import PublishedCourseResultRow
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import AttendanceSessionRow, AttendanceRecordRow


def _published_result(id, account, percent, *, institution='i1', offering='o1', course='cc1'):
    return PublishedCourseResultRow(
        id=id, institution_id=institution, student_id='s-'+account,
        student_account_id=account, course_registration_id='reg-'+id,
        curriculum_course_id=course, offering_id=offering,
        gradebook_id='gradebook', percent=percent, passed=percent >= 60,
        evidence_hash='x'*64, published_by='registrar',
        published_at=datetime(2026,10,13,tzinfo=timezone.utc),
    )


def _attendance_record(id, session_id, account, status, *, institution='i1'):
    return AttendanceRecordRow(
        id=id,institution_id=institution, attendance_session_id=session_id,
        student_account_id=account,status=status,
        recorded_at=datetime(2026,10,13,tzinfo=timezone.utc),method='manual',
        device_id=None,risk_score=0,review='clear',evidence='',row_version=1,
        updated_at=datetime(2026,10,13,tzinfo=timezone.utc),
    )


def test_course_sql_uses_active_roster_denominator_not_results(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        s.add_all([
            _published_result('r1','learner1',30),
            _published_result('r2','learner2',40),
            _published_result('r3','learner3',50),
            _published_result('r4','withdrawn',100),
            _published_result('r5','learner1',99,course='wrong-course'),
            _published_result('r6','learner2',99,institution='i2'),
        ]); s.commit()
    actual=repo.offering_signal('i1','o1',{'learner1','learner2','learner3','not-yet-graded'})
    assert actual['learner_count']==4 and actual['assessed_count']==3
    assert actual['mean_score']==pytest.approx(40)
    assert actual['failure_count']==3 and actual['published_result_count']==3
    assert actual['evidence'][0]['evidence_count']==3  # never includes withdrawn / another tenant
    empty=repo.offering_signal('i1','o1',set())
    assert empty['learner_count']==empty['assessed_count']==0
    assert empty['mean_score'] is None
    with pytest.raises(ValueError,match='pedintel_offering_curriculum_link_required'):
        repo.offering_signal('i2','o1',{'learner1'})


def test_course_sql_rejects_duplicate_and_invalid_grade_rows(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        s.add_all([
            _published_result('r1','learner1',45),
            _published_result('r1b','learner1',90),  # distinct registration, ambiguous learner
            _published_result('r2','learner2',float('inf')),
            _published_result('r3','learner3',42),
            _published_result('r4','learner4',-5),
            _published_result('r5','learner5',101),
        ]);s.commit()
    data=repo.offering_signal('i1','o1',{'learner1','learner2','learner3','learner4','learner5'})
    assert data['learner_count']==5 and data['assessed_count']==1
    assert data['mean_score']==42 and data['published_result_count']==1
    assert data['evidence'][0]['evidence_count']==1


def test_course_sql_attendance_requires_complete_closed_session_roster(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    now=datetime(2026,10,13,tzinfo=timezone.utc)
    with sql_evidence() as s:
        s.add_all([
            AttendanceSessionRow(id='closed',institution_id='i1',teaching_session_id='t1',
                offering_id='o1',state='closed',opens_at=now,closes_at=now,qr_epoch=1,
                row_version=1,created_by='teacher',created_at=now,updated_at=now),
            AttendanceSessionRow(id='open',institution_id='i1',teaching_session_id='t2',
                offering_id='o1',state='open',opens_at=now,closes_at=now,qr_epoch=1,
                row_version=1,created_by='teacher',created_at=now,updated_at=now),
            _attendance_record('p1','closed','learner1','present'),
            _attendance_record('p2','closed','learner2','absent'),
            _attendance_record('px','closed','withdrawn','present'),
            _attendance_record('po','open','learner1','present'),
        ]);s.commit()
    cohort={'learner1','learner2','learner3'}
    partial=repo.offering_signal('i1','o1',cohort)
    assert partial['learner_count']==3 and partial['attendance_record_count']==2
    assert partial['closed_attendance_sessions']==1
    assert partial['attendance_rate'] is None and partial['attendance_complete'] is False
    with sql_evidence() as s:
        s.add(_attendance_record('p3','closed','learner3','late'))
        s.commit()
    complete=repo.offering_signal('i1','o1',cohort)
    assert complete['attendance_rate']==pytest.approx(200/3)
    assert complete['attendance_complete'] is True
    assert complete['attendance_record_count']==3
    # A medically/administratively justified absence is not physical presence.
    with sql_evidence() as s:
        row=s.get(AttendanceRecordRow,'p3')
        row.status='justified'
        s.commit()
    justified=repo.offering_signal('i1','o1',cohort)
    assert justified['attendance_complete'] is True
    assert justified['attendance_rate']==pytest.approx(100/3)
    # Fraud review is not resolved evidence of participation.
    with sql_evidence() as s:
        row=s.get(AttendanceRecordRow,'p1')
        row.review='needs_review'
        s.commit()
    disputed=repo.offering_signal('i1','o1',cohort)
    assert disputed['attendance_rate'] is None
    assert disputed['attendance_complete'] is False


def test_course_report_roster_is_forwarded_and_empty_roster_is_safe(sql_evidence):
    class EmptyCampus(Campus):
        def enrollments_for_cohort(self,c): return ()
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    service=CanonicalPedagogicalIntelligenceService(repo,EmptyCampus(),Teaching())
    report=service.offering_report('teacher','i1','o1')
    assert report['signal']['learner_count']==0 and report['signal']['assessed_count']==0
    assert report['signal']['aggregate_suppressed'] is True
    assert report['insight']['action']=='collect_more_evidence'
    assert report['insight']['confidence']=='low'
    assert report['evidence'][0]['evidence_hash'] is None


def test_low_cell_rule_never_discloses_raw_marks_in_evidence():
    for n in (1,2):
        report=PedagogicalIntelligenceService().analyze([
            LearningSignal('objective', 10, n, 42.5, n, 25.0)
        ])
        evidence=' '.join(report.insights[0].evidence)
        assert 'mean_score' not in evidence
        assert 'failure_rate' not in evidence
        assert 'attendance_rate' not in evidence
        assert report.insights[0].action=='collect_more_evidence'


def test_course_report_filters_active_enrollment_even_with_foreign_records(sql_evidence):
    class TwoEnrollments(Campus):
        def enrollments_for_cohort(self,c):
            return (Obj(student_account_id='learner1',active=True,institution_id='i1'),
                    Obj(student_account_id='learner2',active=True,institution_id='i1'),
                    Obj(student_account_id='learner3',active=True,institution_id='i1'),
                    Obj(student_account_id='withdrawn',active=False,institution_id='i1'),
                    Obj(student_account_id='another-tenant',active=True,institution_id='i2'))
    with sql_evidence() as s:
        s.add_all([
            _published_result('r1','learner1',40),
            _published_result('r2','learner2',50),
            _published_result('r3','learner3',60),
            _published_result('r4','withdrawn',100),
        ]);s.commit()
    report=CanonicalPedagogicalIntelligenceService(
        SqlObjectiveEvidenceRepository(sql_evidence),TwoEnrollments(),Teaching()
    ).offering_report('teacher','i1','o1')
    assert report['signal']['learner_count']==3
    assert report['signal']['mean_score']==50
    assert report['signal']['assessed_count']==3
    assert report['evidence'][0]['evidence_count']==3


# v0.49.8: source-bound assessment integrity, retry de-duplication, tenant and course invariants.

def test_latest_graded_attempt_per_student_blueprint_prevents_retake_weighting(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    now=datetime(2026,10,13,tzinfo=timezone.utc)
    with sql_evidence() as s:
        # A second graded retake for learner1 supersedes the older attempt,
        # rather than manufacturing an extra learner or an extra assessment weight.
        s.add(AttemptRow(id='a1-new',account_id='learner1',blueprint_id='bp1',question_ids=['q1'],
                         started_at=now+timedelta(hours=2),expires_at=now+timedelta(days=1),
                         state='graded',answers=[],submitted_at=now+timedelta(hours=2),row_version=1))
        s.add(ResultRow(attempt_id='a1-new',earned=100,possible=100,percent=100,passed=1,
                        by_chapter={},by_bloom={},questions=[{'question_id':'q1','earned':100,'possible':100,'correct':True}]))
        s.commit()
    data={x['objective_id']:x for x in repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})}['lo1']
    assert data['assessed_count']==3
    assert data['mean_score']==pytest.approx((100+50+40)/3)
    assert data['question_evidence_count']==3  # old retry contributes nothing
    trends=repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})
    assert trends['timeline'][0]['mean_score']==pytest.approx((100+50+40)/3)
    assert trends['recurrent_errors']==()  # only two distinct learners now missed q1


def test_canonical_question_course_change_blocks_stale_foreign_mapping(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        s.get(QuestionRow,'q1').course_id='cc2'
        s.commit()
    results=repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})
    assert {x['objective_id'] for x in results}=={'lo1','lo2'}
    assert all(x['assessed_count']==0 and x['mean_score'] is None for x in results)
    assert repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})=={'timeline':(), 'recurrent_errors':()}


def test_invalid_question_point_value_fails_closed_even_when_result_json_is_valid(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        s.get(QuestionRow,'q1').points=20  # recorded results claim 100 points
        s.commit()
    data=repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})[0]
    assert data['assessed_count']==0 and data['question_evidence_count'] is None
    assert repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})['timeline']==()


def test_canonical_blueprint_course_mismatch_excludes_attempts(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        s.get(BlueprintRow,'bp1').course_id='cc2'
        s.commit()
    assert repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})[0]['assessed_count']==0
    assert repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})['timeline']==()


def test_correct_flag_and_score_cannot_contradict_each_other():
    valid=[{'question_id':'q','earned':100,'possible':100,'correct':True}]
    assert _question_result_rows(valid,['q'],{'q':100})==(('q',100.,100.),)
    for bad in [
        {'question_id':'q','earned':45,'possible':100,'correct':True},
        {'question_id':'q','earned':45,'possible':100,'correct':False},
        {'question_id':'q','earned':0,'possible':100,'correct':'false'},
        {'question_id':'q','earned':20,'possible':99},
    ]:
        assert _question_result_rows([bad],['q'],{'q':100})==()


def test_duplicate_question_in_attempt_cannot_double_count_graded_evidence():
    rows=[{'question_id':'q','earned':5,'possible':10}]
    assert _question_result_rows(rows,['q','q'],{'q':10})==()


def test_grades_remain_read_only_after_teacher_analytics(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        original={x.attempt_id:x.questions for x in s.scalars(select(ResultRow)).all()}
    repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})
    repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})
    with sql_evidence() as s:
        assert {x.attempt_id:x.questions for x in s.scalars(select(ResultRow)).all()}==original


def test_corrupt_attempt_question_ids_fail_closed_without_server_error():
    assert _question_result_rows([{'question_id':'q','earned':10,'possible':10}], ['q', {'evil':'id'}],{'q':10})==()

def test_invalid_newest_retake_does_not_fallback_to_disallowed_older_grade(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    now=datetime(2026,10,13,tzinfo=timezone.utc)
    with sql_evidence() as s:
        s.add(AttemptRow(id='a1-corrupted',account_id='learner1',blueprint_id='bp1',question_ids=['q1','q1'],
                         started_at=now+timedelta(hours=1),expires_at=now+timedelta(days=1),
                         state='graded',answers=[],submitted_at=now+timedelta(hours=1),row_version=1))
        s.add(ResultRow(attempt_id='a1-corrupted',earned=100,possible=100,percent=100,passed=1,
                        by_chapter={},by_bloom={},questions=[{'question_id':'q1','earned':100,'possible':100}]))
        s.commit()
    signal=repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})[0]
    assert signal['assessed_count']==2 and signal['aggregate_suppressed'] is True
    assert repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})['timeline']==()


# v0.49.9 — adversarial institutional identity, evidence digest and submitted-state guards.

def test_published_results_with_distinct_accounts_same_student_are_not_double_counted(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        first=_published_result('identity-a','learner1',30)
        second=_published_result('identity-b','learner2',40)
        second.student_id=first.student_id  # corrupted SIS merge / duplicate student
        third=_published_result('identity-c','learner3',50)
        s.add_all([first,second,third]);s.commit()
    report=repo.offering_signal('i1','o1',{'learner1','learner2','learner3'})
    assert report['learner_count']==3
    assert report['assessed_count']==1
    assert report['mean_score']==50
    assert report['failure_count']==1
    assert report['evidence'][0]['evidence_count']==1


def test_published_identity_conflict_does_not_affect_other_institution(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        home=_published_result('home','learner1',40)
        foreign=_published_result('foreign','learner3',99,institution='i2',offering='o2',course='cc2')
        foreign.student_id=home.student_id
        s.add_all([home,foreign]);s.commit()
    report=repo.offering_signal('i1','o1',{'learner1'})
    assert report['assessed_count']==1 and report['mean_score']==40


def test_course_evidence_digest_tracks_published_score_even_if_upstream_hash_stale(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        s.add_all([_published_result(f'p-{n}',f'learner{n}',n*10) for n in (1,2,3)])
        s.commit()
    before=repo.offering_signal('i1','o1',{'learner1','learner2','learner3'})
    with sql_evidence() as s:
        row=s.get(PublishedCourseResultRow,'p-2')
        row.percent=80
        s.commit()
    after=repo.offering_signal('i1','o1',{'learner1','learner2','learner3'})
    assert before['evidence'][0]['evidence_hash'] != after['evidence'][0]['evidence_hash']
    assert before['evidence'][0]['evidence_count']==after['evidence'][0]['evidence_count']==3
    assert after['mean_score']!=before['mean_score']
    assert all('learner' not in str(x) for x in [before['evidence'],after['evidence']])


def test_attendance_review_state_changes_digest_without_exposing_attendance_rate(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    now=datetime(2026,10,13,tzinfo=timezone.utc)
    with sql_evidence() as s:
        s.add(AttendanceSessionRow(id='se-v49',institution_id='i1',teaching_session_id='ts-v49',
            offering_id='o1',state='closed',opens_at=now,closes_at=now,qr_epoch=1,
            row_version=1,created_by='teacher',created_at=now,updated_at=now))
        s.add_all([_attendance_record(f'at-v49-{n}','se-v49',f'learner{n}','present') for n in (1,2,3)])
        s.commit()
    before=repo.offering_signal('i1','o1',{'learner1','learner2','learner3'})
    assert before['attendance_complete'] is True and before['attendance_rate']==100
    with sql_evidence() as s:
        record=s.get(AttendanceRecordRow,'at-v49-2')
        record.review='needs_review'
        s.commit()
    after=repo.offering_signal('i1','o1',{'learner1','learner2','learner3'})
    assert after['attendance_complete'] is False and after['attendance_rate'] is None
    assert before['evidence'][0]['evidence_hash'] != after['evidence'][0]['evidence_hash']


def test_invalid_missing_submission_newest_grade_never_revives_older_attempt(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    now=datetime(2026,10,13,tzinfo=timezone.utc)
    with sql_evidence() as s:
        s.add(AttemptRow(id='new-unsubmitted',account_id='learner1',blueprint_id='bp1',
            question_ids=['q1'],started_at=now+timedelta(days=1),expires_at=now+timedelta(days=2),
            state='graded',answers=[],submitted_at=None,row_version=2))
        s.add(ResultRow(attempt_id='new-unsubmitted',earned=100,possible=100,percent=100,passed=1,
            by_chapter={},by_bloom={},questions=[{'question_id':'q1','earned':100,'possible':100}]))
        s.commit()
    signal=repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})[0]
    assert signal['assessed_count']==2 and signal['aggregate_suppressed'] is True
    assert repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})['timeline']==()


def test_older_missing_submission_cannot_override_submitted_newer_grade(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    now=datetime(2026,10,13,tzinfo=timezone.utc)
    with sql_evidence() as s:
        s.add(AttemptRow(id='older-unsubmitted',account_id='learner1',blueprint_id='bp1',
            question_ids=['q1'],started_at=now-timedelta(days=1),expires_at=now,
            state='graded',answers=[],submitted_at=None,row_version=2))
        s.add(ResultRow(attempt_id='older-unsubmitted',earned=100,possible=100,percent=100,passed=1,
            by_chapter={},by_bloom={},questions=[{'question_id':'q1','earned':100,'possible':100}]))
        s.commit()
    signal=repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})[0]
    assert signal['assessed_count']==3 and signal['mean_score']==pytest.approx(40)
    assert len(repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})['timeline'])==1

# v0.49.10 — latest-started attempt provenance, impossible submission chronology,
# and canonical result-total sanity across both objective analytics projections.

def test_newer_invalid_submission_does_not_resurrect_old_retaken_grade(sql_evidence):
    repo = SqlObjectiveEvidenceRepository(sql_evidence)
    now = datetime(2026, 10, 13, tzinfo=timezone.utc)
    with sql_evidence() as s:
        # Started after original attempt but forged its submitted_at in the past.
        s.add(AttemptRow(id='new-backdated-submission', account_id='learner1', blueprint_id='bp1',
            question_ids=['q1'], started_at=now + timedelta(hours=2),
            expires_at=now + timedelta(days=1), state='graded', answers=[],
            submitted_at=now - timedelta(days=5), row_version=2))
        s.add(ResultRow(attempt_id='new-backdated-submission', earned=100, possible=100,
            percent=100, passed=1, by_chapter={}, by_bloom={},
            questions=[{'question_id':'q1', 'earned':100, 'possible':100}]))
        s.commit()
    # Neither the forged new grade nor the historical superseded grade is usable.
    signal = repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})[0]
    assert signal['assessed_count'] == 2 and signal['aggregate_suppressed'] is True
    assert repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})['timeline'] == ()


def test_newer_started_retake_wins_even_if_older_is_submitted_later(sql_evidence):
    repo = SqlObjectiveEvidenceRepository(sql_evidence)
    now = datetime(2026, 10, 13, tzinfo=timezone.utc)
    with sql_evidence() as s:
        # The previous attempt was long-running; grading it later does not make
        # its start chronologically newer than a completed retake.
        previous = s.get(AttemptRow, 'a1')
        previous.submitted_at = now + timedelta(hours=4)
        s.add(AttemptRow(id='retake-started-last', account_id='learner1', blueprint_id='bp1',
            question_ids=['q1'], started_at=now + timedelta(hours=1),
            expires_at=now + timedelta(days=1), state='graded', answers=[],
            submitted_at=now + timedelta(hours=2), row_version=2))
        s.add(ResultRow(attempt_id='retake-started-last', earned=100, possible=100,
            percent=100, passed=1, by_chapter={}, by_bloom={},
            questions=[{'question_id':'q1', 'earned':100, 'possible':100}]))
        s.commit()
    objective = repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})[0]
    assert objective['mean_score'] == pytest.approx((100+50+40)/3)
    assert repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})['timeline'][0]['mean_score'] == pytest.approx((100+50+40)/3)


@pytest.mark.parametrize('earned,possible,percent,passed', [
    (-1,100,0,0), (150,100,100,1), (0,0,0,0), (20,100,99,0),
    (20,100,-1,0), (20,100,101,1), (20,100,20,7),
])
def test_corrupt_graded_result_totals_never_count_as_objective_evidence(
    sql_evidence, earned, possible, percent, passed
):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        result = s.get(ResultRow,'a1')
        result.earned, result.possible, result.percent, result.passed = earned, possible, percent, passed
        s.commit()
    objective=repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})[0]
    assert objective['assessed_count']==2
    assert objective['aggregate_suppressed'] is True
    trends=repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})
    assert trends['timeline']==() and trends['recurrent_errors']==()


def test_rounded_consistent_grade_remains_valid_in_both_projections(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        result = s.get(ResultRow,'a1')
        result.earned, result.possible, result.percent, result.passed = 1, 3, 33, 0
        s.commit()
    objective=repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})[0]
    assert objective['assessed_count']==3 and objective['mean_score']==pytest.approx(40)
    assert len(repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})['timeline'])==1


def test_nonfinite_result_totals_are_rejected_before_query_aggregation():
    from app.modules.pedagogical_intelligence.infrastructure import _valid_graded_result
    for abnormal in (float('nan'), float('inf'), float('-inf')):
        assert _valid_graded_result(Obj(earned=abnormal,possible=100,percent=0,passed=0)) is False
        assert _valid_graded_result(Obj(earned=0,possible=abnormal,percent=0,passed=0)) is False
        assert _valid_graded_result(Obj(earned=0,possible=100,percent=abnormal,passed=0)) is False

# v0.49.13: audit grade-to-objective mapping chronology and published-gradebook
# candidate references; no automatic certification of manually attributed sources.
from app.modules.gradebook.infrastructure.sqlalchemy_repo import GradebookRow, ComponentRow, MarkRow
from app.modules.assessment.domain.score_integrity import make_auto_sum_snapshot
from app.modules.pedagogical_intelligence.infrastructure import _mapping_timing


def test_mapping_timing_is_distinct_from_grade_integrity():
    stamp=datetime(2026,10,13,tzinfo=timezone.utc)
    attempt=Obj(started_at=stamp, submitted_at=stamp+timedelta(minutes=20))
    assert _mapping_timing(Obj(created_at=stamp-timedelta(days=1)),attempt)=='mapped_before_attempt'
    assert _mapping_timing(Obj(created_at=stamp+timedelta(minutes=2)),attempt)=='mapped_during_attempt'
    assert _mapping_timing(Obj(created_at=stamp+timedelta(days=1)),attempt)=='retrospective_mapping'
    assert _mapping_timing(Obj(created_at=None),attempt)=='unknown'


def test_retroactive_question_mapping_is_disclosed_separately_from_score_quality(sql_evidence):
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with sql_evidence() as s:
        s.get(PedagogicalQuestionObjectiveRow,'q1').created_at=datetime(2026,10,14,tzinfo=timezone.utc)
        s.get(PedagogicalQuestionObjectiveRow,'q2').created_at=datetime(2026,10,12,tzinfo=timezone.utc)
        s.commit()
    rows=repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})
    lo=next(r for r in rows if r['objective_id']=='lo1')
    assert lo['assessed_count']==3
    assert lo['mapping_provenance']=='contains_retrospective_mapping'
    trend=repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})
    assert trend['timeline'][0]['mapping_provenance']=='contains_retrospective_mapping'
    assert trend['recurrent_errors'][0]['mapping_provenance']=='contains_retrospective_mapping'
    # The evidence itself was legacy; changing mapping provenance must not
    # silently promote it to a verified grading snapshot.
    assert lo['evidence_integrity']=='legacy_unverified'


def test_mapping_confidence_is_not_high_for_retrospective_associations():
    class RetroMappingRepo(ObjectiveRepo):
        def objective_signals(self,*args,**kwargs):
            return ({'objective_id':'lo1','objective_title':'X','learner_count':12,'assessed_count':12,
                     'mean_score':30,'failure_count':9,'attendance_rate':None,
                     'evidence_integrity':'verified_snapshot_v2',
                     'mapping_provenance':'contains_retrospective_mapping'},)
    result=CanonicalPedagogicalIntelligenceService(RetroMappingRepo(),Campus(),Teaching()).objective_report('teacher','i1','o1')
    assert result['objectives'][0]['insight']['confidence']=='low'
    assert 'cartographie' in result['objectives'][0]['insight']['reason']


def _published_gradebook_sources(sf, scores=(20,20,20), refs=('a1','a2','a3'),
                                 *, published=True, mark_state='validated'):
    now=datetime(2026,10,13,tzinfo=timezone.utc)
    with sf() as s:
        s.add(GradebookRow(id='gb1',institution_id='i1',offering_id='o1',title='Notes',
            state='published' if published else 'open',pass_percent=60,row_version=1,
            created_by='teacher',created_at=now,updated_at=now))
        s.add(ComponentRow(id='exam1',institution_id='i1',gradebook_id='gb1',title='Exam',
            kind='exam',weight_percent=100,max_score=20,source_assignment_id=None,
            position=1,created_at=now))
        for idx,aid in enumerate(('a1','a2','a3')):
            attempt=s.get(AttemptRow,aid)
            result=s.get(ResultRow,aid)
            result.questions=[dict(question_id=qid,earned=100,possible=100,correct=True)
                              for qid in attempt.question_ids]
            result.earned=result.possible=100*len(attempt.question_ids)
            result.percent=100;result.passed=1
            snapshot,digest=make_auto_sum_snapshot(result,attempt,
                {qid:('cc1',100) for qid in attempt.question_ids},'cc1',60)
            result.grading_contract_version=2
            result.grading_snapshot=snapshot; result.grading_snapshot_sha256=digest
            s.add(MarkRow(id=f'm{idx}',institution_id='i1',gradebook_id='gb1',
                component_id='exam1',student_account_id=f'learner{idx+1}',
                score=scores[idx],state=mark_state,
                source_ref='assessment:'+refs[idx] if refs[idx] else None,
                validated_by='teacher',row_version=1,created_at=now,updated_at=now,
                attendance='present',note=None))
        s.commit()


def test_canonical_candidate_sources_corroborate_with_real_sql_without_certifying_publication(sql_evidence):
    _published_gradebook_sources(sql_evidence)
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    found=repo.gradebook_assessment_reconciliation('i1','o1',{'learner1','learner2','learner3'})
    assert found['status']=='candidate_scores_consistent'
    assert found['candidate_count']==3 and found['score_discrepancies']==0
    assert found['authoritative_source_link'] is False and found['official_grade_modified'] is False
    with sql_evidence() as s:
        assert s.get(MarkRow,'m0').score==20
        assert s.get(ResultRow,'a1').percent==100


def test_canonical_candidate_sources_reject_mismatches_and_tenant_spoofing(sql_evidence):
    _published_gradebook_sources(sql_evidence,scores=(20,12,20), refs=('a1','a2','at'))
    out=SqlObjectiveEvidenceRepository(sql_evidence).gradebook_assessment_reconciliation(
        'i1','o1',{'learner1','learner2','learner3'})
    assert out['status']=='manual_review_required'
    assert out['score_discrepancies']==2
    assert 'assessment:at' not in str(out) and 'learner3' not in str(out)


def test_candidate_link_reuse_fails_closed(sql_evidence):
    _published_gradebook_sources(sql_evidence,refs=('a1','a1','a1'))
    out=SqlObjectiveEvidenceRepository(sql_evidence).gradebook_assessment_reconciliation(
        'i1','o1',{'learner1','learner2','learner3'})
    assert out['status']=='manual_review_required'
    assert out['score_discrepancies']>=2


@pytest.mark.parametrize('allowed', [set(), {'learner1'}, {'learner1','learner2'}])
def test_gradebook_reconciliation_suppresses_small_rosters(sql_evidence,allowed):
    _published_gradebook_sources(sql_evidence)
    out=SqlObjectiveEvidenceRepository(sql_evidence).gradebook_assessment_reconciliation('i1','o1',allowed)
    assert out['candidate_count'] is None and out['score_discrepancies'] is None
    assert out['status'] in {'suppressed','no_candidate_links'}


def test_reconciliation_cannot_read_other_institution_gradebook(sql_evidence):
    _published_gradebook_sources(sql_evidence)
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    with pytest.raises(ValueError,match='pedintel_offering_curriculum_link_required'):
        repo.gradebook_assessment_reconciliation('i2','o1',{'learner1','learner2','learner3'})


def test_no_published_gradebook_must_not_present_candidate_verification(sql_evidence):
    _published_gradebook_sources(sql_evidence,published=False)
    out=SqlObjectiveEvidenceRepository(sql_evidence).gradebook_assessment_reconciliation(
        'i1','o1',{'learner1','learner2','learner3'})
    assert out['status']=='no_published_gradebook' and out['candidate_count'] is None


def test_corroboration_rejects_unverified_legacy_and_nonvalidated_mark(sql_evidence):
    _published_gradebook_sources(sql_evidence)
    with sql_evidence() as s:
        s.get(ResultRow,'a1').grading_contract_version=0
        s.get(ResultRow,'a1').grading_snapshot=None
        s.get(ResultRow,'a1').grading_snapshot_sha256=None
        s.get(MarkRow,'m1').state='draft'
        s.commit()
    out=SqlObjectiveEvidenceRepository(sql_evidence).gradebook_assessment_reconciliation(
        'i1','o1',{'learner1','learner2','learner3'})
    assert out['status']=='manual_review_required' and out['score_discrepancies']==2


def test_reconciliation_requires_staff_auth_before_repo_query():
    class StaffRepo(Repo):
        def gradebook_assessment_reconciliation(self,*a):
            raise AssertionError('must not query sensitive marks for student')
    obj=CanonicalPedagogicalIntelligenceService(StaffRepo(),Campus('student'),Teaching())
    with pytest.raises(PermissionError,match='pedintel_teaching_staff_required'):
        obj.gradebook_assessment_reconciliation('student','i1','o1')


def test_reconciliation_staff_endpoint_uses_enrolled_roster():
    class SpyRepo(Repo):
        def gradebook_assessment_reconciliation(self,i,o,allowed_accounts):
            assert (i,o,allowed_accounts)==('i1','o1',{'student1'})
            return {'status':'suppressed'}
    out=CanonicalPedagogicalIntelligenceService(SpyRepo(),Campus(),Teaching()).gradebook_assessment_reconciliation('teacher','i1','o1')
    assert out['status']=='suppressed'


def test_corroboration_rejects_changed_snapshot_hash_and_nonfinite_mark(sql_evidence):
    _published_gradebook_sources(sql_evidence)
    with sql_evidence() as s:
        s.get(ResultRow,'a1').grading_snapshot_sha256='0'*64
        s.get(MarkRow,'m1').score=float('nan')
        s.commit()
    out=SqlObjectiveEvidenceRepository(sql_evidence).gradebook_assessment_reconciliation(
        'i1','o1',{'learner1','learner2','learner3'})
    assert out['status']=='manual_review_required' and out['score_discrepancies']==2


def test_corroboration_refuses_gradebook_and_attempt_from_different_offering(sql_evidence):
    _published_gradebook_sources(sql_evidence)
    with sql_evidence() as s:
        s.get(PedagogicalBlueprintOfferingRow,'bp1').offering_id='o2'
        s.commit()
    out=SqlObjectiveEvidenceRepository(sql_evidence).gradebook_assessment_reconciliation(
        'i1','o1',{'learner1','learner2','learner3'})
    assert out['status']=='manual_review_required' and out['score_discrepancies']==3


def test_contemporaneous_objective_mapping_is_not_marked_retrospective(sql_evidence):
    now=datetime(2026,10,12,tzinfo=timezone.utc)
    with sql_evidence() as s:
        for qid in ('q1','q2'):
            s.get(PedagogicalQuestionObjectiveRow,qid).created_at=now
        s.commit()
    repo=SqlObjectiveEvidenceRepository(sql_evidence)
    out=repo.objective_signals('i1','o1',{'learner1','learner2','learner3'})
    assert next(r for r in out if r['objective_id']=='lo1')['mapping_provenance']=='mapped_before_attempt'
    trends=repo.objective_trends('i1','o1',{'learner1','learner2','learner3'})
    assert trends['timeline'][0]['mapping_provenance']=='mapped_before_attempt'


def test_mapping_provenance_is_redacted_when_two_learners(sql_evidence):
    out=SqlObjectiveEvidenceRepository(sql_evidence).objective_signals('i1','o1',{'learner1','learner2'})
    assert next(r for r in out if r['objective_id']=='lo1')['mapping_provenance']=='suppressed'

from datetime import UTC,datetime,timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.shared.infrastructure.database import Base
from app.modules.campus.infrastructure.sqlalchemy_repo import SqlAlchemyCampusRepository
from app.modules.teaching.infrastructure.sqlalchemy_repo import SqlAlchemyTeachingRepository
from app.modules.assignments.infrastructure.sqlalchemy_repo import SqlAlchemyAssignmentRepository
from app.modules.gradebook.infrastructure.sqlalchemy_repo import SqlAlchemyGradebookRepository
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import SqlAlchemyCampusOperationsRepository
from app.modules.institutional_analytics.infrastructure.sqlalchemy_repo import SqlAlchemyInstitutionalAnalyticsRepository
from app.modules.institutional_analytics.application.service import InstitutionalAnalyticsService
from app.modules.campus.application.service import CampusService
from app.modules.campus.domain.model import CampusRole,UnitKind,PeriodKind
from app.modules.teaching.domain.model import TeacherRole
from app.modules.teaching.application.service import TeachingService
from app.modules.assignments.application.service import AssignmentService
from app.modules.gradebook.application.service import GradebookService
from app.modules.campus_operations.application.service import CampusOperationsService

NOW=datetime(2026,9,26,8,tzinfo=UTC)
def clock():return NOW

def env():
 e=create_engine('sqlite+pysqlite:///:memory:');Base.metadata.create_all(e);sf=sessionmaker(e,expire_on_commit=False)
 c=SqlAlchemyCampusRepository(sf);t=SqlAlchemyTeachingRepository(sf);a=SqlAlchemyAssignmentRepository(sf);g=SqlAlchemyGradebookRepository(sf);o=SqlAlchemyCampusOperationsRepository(sf)
 cs=CampusService(c,clock);ts=TeachingService(t,c,clock);ass=AssignmentService(a,c,t,clock);gs=GradebookService(g,c,t,a,clock);ops=CampusOperationsService(o,c,t,clock,secret='q'*32,proximity_secret='p'*32)
 ia=InstitutionalAnalyticsService(SqlAlchemyInstitutionalAnalyticsRepository(sf),c,t)
 return cs,ts,ass,gs,ops,ia

def seed():
 cs,ts,ass,gs,ops,ia=env();i=cs.create_institution('owner',name='Université Test',slug='universite-test',legal_name='',country_code='CD',city='Lubumbashi',logo_url=None);cs.invite_member('owner',i.id,account_id='teacher',role=CampusRole.TEACHER,unit_id=None);cs.accept_invitation('teacher',i.id);cs.invite_member('owner',i.id,account_id='student',role=CampusRole.STUDENT,unit_id=None);cs.accept_invitation('student',i.id)
 u=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Médecine',code='MED',parent_id=None);year=cs.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2026-2027',starts_on=NOW.date(),ends_on=(NOW+timedelta(days=300)).date(),parent_id=None);p=cs.add_period('owner',i.id,kind=PeriodKind.SEMESTER,name='S1',starts_on=NOW.date(),ends_on=(NOW+timedelta(days=100)).date(),parent_id=year.id);co=cs.create_cohort('owner',i.id,program_unit_id=u.id,academic_period_id=p.id,name='BAC1',level='1');cs.enroll('owner',i.id,cohort_id=co.id,student_account_id='student')
 course=ts.create_course('owner',i.id,code='BIO',title='Biologie',description='',credits=4);off=ts.create_offering('owner',i.id,course_id=course.id,cohort_id=co.id,academic_period_id=p.id,label='BIO S1');ts.assign_teacher('owner',i.id,off.id,teacher_account_id='teacher',role=TeacherRole.LEAD);off=ts.publish_offering('owner',i.id,off.id,off.row_version)
 return (cs,ts,ass,gs,ops,ia,i,p,co,off)

def test_dashboard_is_institutional_and_teacher_scoped():
 *_,ia,i,p,co,off=seed();d=ia.dashboard('owner',i.id,academic_period_id=p.id);assert d['population']['active_enrollments'] is None;assert '_student_results' not in d  # v3: one learner suppressed
 try:ia.dashboard('teacher',i.id)
 except PermissionError as e:assert 'teacher_scope_required' in str(e)
 else:assert False
 assert ia.dashboard('teacher',i.id,offering_id=off.id)['population']['offerings'] is None  # v3: no small cell

def test_student_cannot_access_institutional_analytics():
 *_,ia,i,p,co,off=seed()
 try:ia.dashboard('student',i.id,offering_id=off.id)
 except PermissionError:pass
 else:assert False

def test_metric_definitions_are_versioned_and_institutional_only():
 *_,ia,i,p,co,off=seed();xs=ia.definitions('owner',i.id);assert len(xs)>=5;assert all(x.version>=1 and x.privacy_class=='institutional' for x in xs)

def test_signals_are_explainable_not_labels_or_accusations():
 cs,ts,ass,gs,ops,ia,i,p,co,off=seed();s=ts.add_session('teacher',i.id,off.id,title='Cours',starts_at=NOW,ends_at=NOW+timedelta(hours=2));ts.complete_session('teacher',i.id,s.id,summary='fait',next_topic='suite',expected_version=s.row_version)
 d=ia.dashboard('owner',i.id,offering_id=off.id);assert d['teaching']['completion_rate'] is None  # v3: small cohort, no released rate;assert isinstance(ia.signals('owner',i.id,offering_id=off.id),tuple)

def test_immutable_snapshots_and_comparison_contract():
 *_,ia,i,p,co,off=seed()
 a=ia.capture_snapshot('owner',i.id,academic_period_id=p.id,offering_id=off.id)
 b=ia.capture_snapshot('owner',i.id,academic_period_id=p.id,offering_id=off.id)
 assert len(a['content_sha256'])==64 and len(b['content_sha256'])==64
 assert a['content_sha256']!=b['content_sha256']  # per-archive random HMAC nonce
 h=ia.history('owner',i.id,scope_type='offering',scope_id=off.id,academic_period_id=p.id)
 assert len(h)==2 and h[0]['payload'] is None and h[0]['privacy_status']=='current_scope_suppressed'
 c=ia.compare_snapshots('owner',i.id,scope_type='offering',scope_id=off.id,academic_period_id=p.id)
 assert c['available'] is False and c['reason']=='unverified_or_privacy_suppressed_snapshots'

def test_unit_rollup_uses_descendant_programs_only():
 cs,ts,ass,gs,ops,ia,i,p,co,off=seed()
 root=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Sciences de santé',code='SANTE',parent_id=None)
 program=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Pharmacie',code='PHA',parent_id=root.id)
 co2=cs.create_cohort('owner',i.id,program_unit_id=program.id,academic_period_id=p.id,name='PHA1',level='1')
 cs.enroll('owner',i.id,cohort_id=co2.id,student_account_id='student')
 course=ts.create_course('owner',i.id,code='CHM',title='Chimie',description='',credits=4)
 off2=ts.create_offering('owner',i.id,course_id=course.id,cohort_id=co2.id,academic_period_id=p.id,label='CHM S1')
 d=ia.unit_dashboard('owner',i.id,root.id,academic_period_id=p.id)
 assert d['scope']['academic_unit_id']==root.id and d['population']['offerings'] is None

def test_csv_export_contains_only_aggregated_institutional_metrics():
 *_,ia,i,p,co,off=seed();body=ia.export_csv('owner',i.id,offering_id=off.id)
 assert 'section,metric,value' in body and 'attendance,attendance_rate' in body
 assert 'student' not in body.lower() and '_student_results' not in body

def test_pedagogical_intelligence_is_aggregate_and_privacy_safe():
 *_,ia,i,p,co,off=seed();d=ia.pedagogical_intelligence('owner',i.id,offering_id=off.id)
 assert d['assessment']['attempts'] is None and d['assessment']['by_bloom']=={}  # lineage not certified
 assert d['interpretation']['automatic_judgement'] is False
 assert 'student' not in str(d).lower() and 'answer' not in str(d).lower()

def test_executive_report_has_explicit_privacy_contract():
 *_,ia,i,p,co,off=seed();r=ia.executive_report('owner',i.id,academic_period_id=p.id,offering_id=off.id)
 assert r['contract_version']==3 and r['generated_from']=='governed_institutional_sources_only'
 assert all(v is False for v in r['privacy'].values())
 assert set(r['kpis'])=={'population','teaching','attendance','assignments','results'}

def test_faculty_report_pedagogy_cannot_escape_authorized_unit_scope():
 cs,ts,ass,gs,ops,ia,i,p,co,off=seed()
 faculty=cs.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Faculté A',code='FA',parent_id=None)
 program=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Programme A',code='PA',parent_id=faculty.id)
 co2=cs.create_cohort('owner',i.id,program_unit_id=program.id,academic_period_id=p.id,name='A1',level='1')
 cs.invite_member('owner',i.id,account_id='fa',role=CampusRole.FACULTY_ADMIN,unit_id=faculty.id);cs.accept_invitation('fa',i.id)
 r=ia.executive_report('fa',i.id,academic_period_id=p.id,academic_unit_id=faculty.id)
 assert r['scope']['academic_unit_id']==faculty.id and r['pedagogical_intelligence']['assessment']['attempts'] is None

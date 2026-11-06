from datetime import datetime,timezone
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.shared.infrastructure.database import Base
from app.modules.student_success.infrastructure.sqlalchemy_repo import SqlSuccessRepository
from app.modules.student_success.application.service import StudentSuccessService
from app.modules.campus.domain.model import CampusRole,MembershipState

class Campus:
 def membership(self,i,a):
  if i!='university-a' or a not in {'officer','learner','outsider'}:return None
  return SimpleNamespace(role={'officer':CampusRole.ACADEMIC_ADMIN,'learner':CampusRole.STUDENT,'outsider':CampusRole.STUDENT}[a],state=MembershipState.ACTIVE)
class Students:
 def get(self,sid):
  if sid=='student-1':return SimpleNamespace(id=sid,institution_id='university-a',account_id='learner')
 def by_account(self,i,a):
  if i=='university-a' and a=='learner':return self.get('student-1')
@pytest.fixture
def service(tmp_path):
 engine=create_engine('sqlite:///'+str(tmp_path/'success.sqlite'))
 Base.metadata.create_all(engine)
 yield StudentSuccessService(SqlSuccessRepository(sessionmaker(bind=engine)),Campus(),Students(),lambda:datetime.now(timezone.utc))
 engine.dispose()
def test_lifecycle_and_atomic_timeline(service):
 c=service.create('officer','university-a','student-1','academic','high','Repeated course failure')
 assert len(service.timeline('officer','university-a',c.id))==1
 n=service.transition('officer','university-a',c.id,'in_progress',1,'Advisor contacted')
 assert n.version==2
 assert len(service.timeline('officer','university-a',c.id))==2
 with pytest.raises(ValueError,match='concurrent'):service.transition('officer','university-a',c.id,'resolved',1,'Wrong version')
 assert len(service.timeline('officer','university-a',c.id))==2
 assert service.transition('officer','university-a',c.id,'resolved',2,'Tutoring scheduled').state=='resolved'
def test_tenant_student_privacy_and_permissions(service):
 c=service.create('officer','university-a','student-1','attendance','medium','Missing multiple sessions')
 assert service.get('learner','university-a',c.id).id==c.id
 assert len(service.list('learner','university-a'))==1
 with pytest.raises(PermissionError):service.create('learner','university-a','student-1','academic','high','Repeated course failure')
 with pytest.raises(PermissionError):service.get('outsider','university-a',c.id)
 with pytest.raises(PermissionError):service.get('officer','university-b',c.id)
 with pytest.raises(ValueError):service.create('officer','university-a','foreign-student','academic','high','Repeated course failure')
def test_no_invalid_transitions_or_unsupported_predictive_claims(service):
 c=service.create('officer','university-a','student-1','engagement','low','Learner asked for help')
 with pytest.raises(ValueError,match='invalid_transition'):service.transition('officer','university-a',c.id,'resolved',1,'Not yet assessed')
 with pytest.raises(ValueError,match='note_required'):service.transition('officer','university-a',c.id,'in_progress',1,'bad')
 with pytest.raises(ValueError,match='category'):service.create('officer','university-a','student-1','diagnosis','high','Sensitive diagnosis')

def test_deterministic_early_warning_deduplicates(service):
 class EvidenceRepo(type(service.repo)):
  pass
 service.repo.evidence=lambda i,sid,aid: (
  (SimpleNamespace(passed=False,evidence_hash='a'),SimpleNamespace(passed=False,evidence_hash='b')),
  tuple(SimpleNamespace(status=x,attendance_session_id=str(n)) for n,x in enumerate(['absent','absent','present','absent']))
 )
 first=service.scan('officer','university-a','student-1')
 assert first['predictive_model'] is False and first['method']=='deterministic_rules_v1'
 assert len(first['created'])==2
 second=service.scan('officer','university-a','student-1')
 assert len(second['created'])==0 and len(second['existing'])==2
 assert {x.category for x in first['created']}=={'academic','attendance'}

def test_early_warning_requires_staff_and_does_not_infer_without_evidence(service):
 service.repo.evidence=lambda *args:((),())
 with pytest.raises(PermissionError):service.scan('learner','university-a','student-1')
 r=service.scan('officer','university-a','student-1')
 assert r['created']==() and r['attendance_rate'] is None and r['failed_results']==0

def test_action_plan_lifecycle_and_timeline(service):
 c=service.create('officer','university-a','student-1','academic','high','Repeated course failure')
 p=service.create_plan('officer','university-a',c.id,'Recover failed courses this semester','2026-12-20')
 a=service.add_action('officer','university-a',c.id,'Weekly tutoring session','officer','2026-11-01')
 assert service.list_actions('learner','university-a',c.id)[0].id==a.id
 with pytest.raises(ValueError,match='pending_actions'):service.close_plan('officer','university-a',c.id,1,'All objectives met')
 done=service.complete_action('officer','university-a',c.id,a.id,1,'Tutoring cycle completed')
 assert done.state=='completed' and done.version==2
 assert service.close_plan('officer','university-a',c.id,1,'All objectives met').state=='completed'
 assert [e.action for e in service.timeline('officer','university-a',c.id)][-4:]==['plan_created','action_added','action_completed','plan_completed']

def test_action_plan_guards_duplicates_dates_and_closed_cases(service):
 c=service.create('officer','university-a','student-1','attendance','medium','Missing multiple sessions')
 service.create_plan('officer','university-a',c.id,'Restore regular attendance quickly')
 with pytest.raises(ValueError,match='active_plan_exists'):service.create_plan('officer','university-a',c.id,'Second competing action plan')
 with pytest.raises(ValueError,match='invalid_due_date'):service.add_action('officer','university-a',c.id,'Advisor meeting','officer','not-a-date')
 c2=service.create('officer','university-a','student-1','other','low','Administrative support needed')
 service.transition('officer','university-a',c2.id,'closed',1,'Issue handled')
 with pytest.raises(ValueError,match='closed_case'):service.create_plan('officer','university-a',c2.id,'Should never be created')

def test_action_completion_optimistic_lock(service):
 c=service.create('officer','university-a','student-1','engagement','medium','Learner needs structured follow up')
 service.create_plan('officer','university-a',c.id,'Maintain regular advisor follow up')
 a=service.add_action('officer','university-a',c.id,'Advisor follow up call','officer')
 with pytest.raises(ValueError,match='concurrent'):service.complete_action('officer','university-a',c.id,a.id,2,'Completed successfully')
 assert service.repo.get_action(a.id).state=='pending'

def test_plan_reassessment_tracks_evolution(service):
 c=service.create('officer','university-a','student-1','academic','high','Repeated course failure')
 service.create_plan('officer','university-a',c.id,'Recover academic performance this semester')
 service.repo.evidence=lambda *args:((SimpleNamespace(passed=False,evidence_hash='f1'),SimpleNamespace(passed=False,evidence_hash='f2')),tuple(SimpleNamespace(status=x,attendance_session_id=str(n)) for n,x in enumerate(['absent','present','absent','present'])))
 baseline=service.reassess_plan('officer','university-a',c.id)
 assert baseline.outcome=='baseline' and baseline.failed_results==2 and baseline.attendance_rate==50.0
 service.repo.evidence=lambda *args:((SimpleNamespace(passed=True,evidence_hash='p1'),SimpleNamespace(passed=False,evidence_hash='f2')),tuple(SimpleNamespace(status=x,attendance_session_id=str(n)) for n,x in enumerate(['present','present','present','absent'])))
 followup=service.reassess_plan('officer','university-a',c.id)
 assert followup.outcome=='improved' and followup.failed_results==1 and followup.attendance_rate==75.0
 assert [x.outcome for x in service.assessments('learner','university-a',c.id)]==['baseline','improved']
 assert service.timeline('officer','university-a',c.id)[-1].action=='plan_reassessed'

def test_dashboard_overdue_and_permissions(service):
 c=service.create('officer','university-a','student-1','attendance','high','Persistent attendance difficulties')
 service.create_plan('officer','university-a',c.id,'Restore regular attendance this semester','2020-01-01')
 service.add_action('officer','university-a',c.id,'Meet academic advisor','officer','2020-01-01')
 d=service.dashboard('officer','university-a')
 assert d['open_cases']==1 and d['high_severity_open']==1 and d['overdue_plans']==1 and d['overdue_actions']==1
 with pytest.raises(PermissionError):service.dashboard('learner','university-a')


def test_case_cannot_close_with_active_support_plan(service):
 c=service.create('officer','university-a','student-1','academic','high','Repeated course failure')
 service.create_plan('officer','university-a',c.id,'Support student until objectives are completed')
 with pytest.raises(ValueError,match='active_plan_blocks_case_closure'):
  service.transition('officer','university-a',c.id,'closed',1,'Closing without completing support')
 assert service.get('officer','university-a',c.id).state=='open'
 assert len(service.timeline('officer','university-a',c.id))==2

def test_reassessment_does_not_call_missing_attendance_an_improvement(service):
 c=service.create('officer','university-a','student-1','academic','high','Repeated course failure')
 service.create_plan('officer','university-a',c.id,'Follow up academic progress over the semester')
 service.repo.evidence=lambda *args:((SimpleNamespace(passed=False,evidence_hash='f1'),),tuple(SimpleNamespace(status='absent',attendance_session_id=str(n)) for n in range(4)))
 first=service.reassess_plan('officer','university-a',c.id)
 assert first.attendance_rate==0
 service.repo.evidence=lambda *args:((SimpleNamespace(passed=False,evidence_hash='f1'),),())
 second=service.reassess_plan('officer','university-a',c.id)
 assert second.outcome=='stable'


def test_reassessment_sparse_attendance_is_insufficient(service):
 c=service.create('officer','university-a','student-1','attendance','medium','Insufficient attendance history')
 service.create_plan('officer','university-a',c.id,'Improve student attendance consistently')
 service.repo.evidence=lambda *args:((),(SimpleNamespace(status='present',attendance_session_id='s1'),))
 first=service.reassess_plan('officer','university-a',c.id)
 assert first.outcome=='insufficient'
 service.repo.evidence=lambda *args:((),(SimpleNamespace(status='present',attendance_session_id='s2'),))
 second=service.reassess_plan('officer','university-a',c.id)
 assert second.outcome=='insufficient'

def test_reassessment_lost_comparable_sources_is_insufficient(service):
 c=service.create('officer','university-a','student-1','academic','medium','Review evidence availability')
 service.create_plan('officer','university-a',c.id,'Review course outcomes and attendance')
 service.repo.evidence=lambda *args:((SimpleNamespace(passed=False,evidence_hash='f1'),),())
 assert service.reassess_plan('officer','university-a',c.id).outcome=='baseline'
 service.repo.evidence=lambda *args:((),(SimpleNamespace(status='present',attendance_session_id='s1'),))
 assert service.reassess_plan('officer','university-a',c.id).outcome=='insufficient'

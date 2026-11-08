from datetime import UTC,date,datetime,timedelta
import pytest
from app.modules.campus.application.service import CampusService
from app.modules.campus.domain.model import *
from app.modules.teaching.application.service import TeachingService
from app.modules.gradebook.application.service import GradebookService
from app.modules.gradebook.domain.model import *
from test_campus_lot22 import Repo as CampusRepo
from test_teaching_lot23 import Repo as TeachingRepo
class Repo:
 def __init__(self):self.g={};self.c={};self.m={};self.s={}
 def gradebook(self,i,id):x=self.g.get(id);return x if x and x.institution_id==i else None
 def for_offering(self,i,o):return next((x for x in self.g.values() if x.institution_id==i and x.offering_id==o),None)
 def save_gradebook(self,x,expected=None):
  old=self.g.get(x.id)
  if old and expected is not None and old.row_version!=expected:raise ValueError('gradebook_concurrent_modification')
  self.g[x.id]=x
 def save_component(self,x):self.c[x.id]=x
 def components(self,g):return tuple(sorted((x for x in self.c.values() if x.gradebook_id==g),key=lambda x:x.position))
 def component(self,i,id):x=self.c.get(id);return x if x and x.institution_id==i else None
 def mark(self,i,c,s):return self.m.get((c,s))
 def save_mark(self,x,expected=None):
  old=self.m.get((x.component_id,x.student_account_id))
  if old and expected is not None and old.row_version!=expected:raise ValueError('gradebook_concurrent_modification')
  self.m[(x.component_id,x.student_account_id)]=x
 def marks(self,g,stu=None):return tuple(x for x in self.m.values() if x.gradebook_id==g and (stu is None or x.student_account_id==stu))
 def session(self,i,id):
  x=self.s.get(id);return x if x and x.institution_id==i else None
 def sessions_for_gradebook(self,i,g):return tuple(x for x in self.s.values() if x.institution_id==i and x.gradebook_id==g)
 def save_session(self,x,expected=None):
  old=self.s.get(x.id)
  if old and expected is not None and old.row_version!=expected:raise ValueError('gradebook_concurrent_modification')
  self.s[x.id]=x
class AssignRepo:
 def assignment(self,i,id):return None
 def submissions(self,a):return ()
 def grade_for_submission(self,s):return None
def setup():
 now=lambda:datetime(2026,9,25,18,tzinfo=UTC);cr=CampusRepo();cs=CampusService(cr,now);i=cs.create_institution('owner',name='Université',slug='univ');p=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Médecine',code='MED');y=cs.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2026',starts_on=date(2026,9,1),ends_on=date(2027,7,1));co=cs.create_cohort('owner',i.id,program_unit_id=p.id,academic_period_id=y.id,name='BAC1',level='L1')
 for a,r in [('teach',CampusRole.TEACHER),('stu',CampusRole.STUDENT)]:cs.invite_member('owner',i.id,account_id=a,role=r);cs.accept_invitation(a,i.id)
 cs.enroll('owner',i.id,cohort_id=co.id,student_account_id='stu');cr.enrollments_for_student=lambda ii,a:tuple(x for x in cr.e.values() if x.institution_id==ii and x.student_account_id==a);cr.enrollments_for_cohort=lambda c:tuple(x for x in cr.e.values() if x.cohort_id==c)
 tr=TeachingRepo();ts=TeachingService(tr,cr,now);c=ts.create_course('owner',i.id,code='ANA',title='Anatomie');o=ts.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='ANA');ts.assign_teacher('owner',i.id,o.id,teacher_account_id='teach');ts.publish_offering('teach',i.id,o.id,1)
 return GradebookService(Repo(),cr,tr,AssignRepo(),now),i,o

def test_weighted_gradebook_private_until_publication():
 s,i,o=setup();g=s.create('teach',i.id,o.id,pass_percent=50);c1=s.add_component('teach',i.id,g.id,title='Interro',kind='test',weight_percent=40,max_score=20);c2=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=60,max_score=20);g=s.open('teach',i.id,g.id,1);s.set_mark('teach',i.id,g.id,c1.id,'stu',score=16);s.set_mark('teach',i.id,g.id,c2.id,'stu',score=14)
 with pytest.raises(PermissionError,match='not_published'):s.result('stu',i.id,g.id)
 g=s.lock('teach',i.id,g.id,2);g=s.publish('teach',i.id,g.id,3);r=s.result('stu',i.id,g.id);assert r.complete and r.published and r.percent==74 and r.passed

def test_weights_must_equal_100_before_open():
 s,i,o=setup();g=s.create('teach',i.id,o.id);s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=60,max_score=20)
 with pytest.raises(ValueError,match='total_100'):s.open('teach',i.id,g.id,1)

def test_student_cannot_write_marks_and_retraction_hides_result():
 s,i,o=setup();g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20);g=s.open('teach',i.id,g.id,1)
 with pytest.raises(PermissionError):s.set_mark('stu',i.id,g.id,c.id,'stu',score=20)
 s.set_mark('teach',i.id,g.id,c.id,'stu',score=12);g=s.lock('teach',i.id,g.id,2);g=s.publish('teach',i.id,g.id,3);assert s.result('stu',i.id,g.id).percent==60
 with pytest.raises(PermissionError,match='academic_admin'):s.retract('teach',i.id,g.id,4,'Erreur de saisie')
 s.retract('owner',i.id,g.id,4,'Erreur de saisie')
 with pytest.raises(PermissionError):s.result('stu',i.id,g.id)

def test_cross_offering_source_and_score_bounds_are_rejected():
 s,i,o=setup();g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20);g=s.open('teach',i.id,g.id,1)
 with pytest.raises(ValueError,match='invalid_score'):s.set_mark('teach',i.id,g.id,c.id,'stu',score=21)

def test_absence_exemption_and_deliberation_locking():
 s,i,o=setup();g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20);g=s.open('teach',i.id,g.id,1)
 s.set_mark('teach',i.id,g.id,c.id,'stu',attendance='absent')
 r=s.result('teach',i.id,g.id,'stu');assert r.complete and r.percent==0 and not r.passed
 g=s.lock('teach',i.id,g.id,2)
 with pytest.raises(ValueError,match='locked'):s.set_mark('teach',i.id,g.id,c.id,'stu',score=10)
 with pytest.raises(PermissionError,match='academic_admin'):s.unlock_exceptionally('teach',i.id,g.id,3,'PV de délibération')

def test_justified_absence_requires_reason_and_blocks_publication():
 s,i,o=setup();g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20);g=s.open('teach',i.id,g.id,1)
 with pytest.raises(ValueError,match='reason_required'):s.set_mark('teach',i.id,g.id,c.id,'stu',attendance='justified_absence')
 s.set_mark('teach',i.id,g.id,c.id,'stu',attendance='justified_absence',note='Certificat médical')
 assert not s.result('teach',i.id,g.id,'stu').complete
 g=s.lock('teach',i.id,g.id,2)
 with pytest.raises(ValueError,match='incomplete'):s.publish('teach',i.id,g.id,3)

def test_exam_session_validation():
 s,i,o=setup();g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20)
 start=datetime(2026,10,1,8,tzinfo=UTC);x=s.create_exam_session('teach',i.id,g.id,c.id,kind='regular',starts_at=start,ends_at=start+timedelta(hours=2),room='A1')
 assert x.room=='A1' and x.state==ExamSessionState.SCHEDULED
 with pytest.raises(ValueError,match='time_invalid'):s.create_exam_session('teach',i.id,g.id,c.id,kind='regular',starts_at=start,ends_at=start)

def test_publication_requires_deliberation_lock():
 s,i,o=setup();g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20);g=s.open('teach',i.id,g.id,1);s.set_mark('teach',i.id,g.id,c.id,'stu',score=15)
 with pytest.raises(ValueError,match='deliberation_lock_required'):s.publish('teach',i.id,g.id,2)

def test_exam_session_overlap_and_lifecycle_are_controlled():
 s,i,o=setup();g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20);start=datetime(2026,10,1,8,tzinfo=UTC)
 x=s.create_exam_session('teach',i.id,g.id,c.id,kind='regular',starts_at=start,ends_at=start+timedelta(hours=2))
 with pytest.raises(ValueError,match='overlap'):s.create_exam_session('teach',i.id,g.id,c.id,kind='makeup',starts_at=start+timedelta(hours=1),ends_at=start+timedelta(hours=3))
 with pytest.raises(ValueError,match='cancel_reason_required'):s.transition_exam_session('teach',i.id,x.id,1,'cancelled')
 y=s.transition_exam_session('teach',i.id,x.id,1,'cancelled','Salle indisponible');assert y.state==ExamSessionState.CANCELLED and y.row_version==2

from datetime import UTC,datetime,date
from types import SimpleNamespace
import pytest
from app.modules.academic_delivery.application.service import AcademicDeliveryService
from app.modules.academic_catalog.domain.model import CurriculumVersion,CurriculumCourse,CurriculumState,CurriculumCohortBinding
from app.modules.campus.domain.model import Membership,MembershipState,CampusRole,Cohort,AcademicPeriod,PeriodKind
from app.modules.student_records.domain.model import StudentRecord,StudentState,AcademicRegistration,RegistrationState,StudentCourseRegistration,CourseRegistrationState

NOW=datetime(2026,10,8,tzinfo=UTC)
class Repo:
 def __init__(self):self.link=None;self.cr=None;self.state=None;self.published=[]
 def link_for_offering(self,i,o):return self.link if self.link and self.link.institution_id==i and self.link.offering_id==o else None
 def save_link(self,x):self.link=x
 def course_registration(self,s,c):return self.cr if self.cr and self.cr.student_id==s and self.cr.curriculum_course_id==c else None
 def set_course_registration_state(self,r,s):self.state=s
 def save_published_result(self,x):self.published.append(x);return x
class Campus:
 def membership(self,i,a):return Membership('m',i,a,CampusRole.ACADEMIC_ADMIN if a=='admin' else CampusRole.STUDENT,MembershipState.ACTIVE,None,None,NOW,1,NOW,NOW)
 def cohort(self,i,c):return Cohort(c,i,'program','year','M1','M1',True,1,NOW,NOW)
 def period(self,i,p):return AcademicPeriod(p,i,PeriodKind.SEMESTER,'S1',date(2026,9,1),date(2027,1,31),'year',True,1,NOW)
class Teaching:
 def offering(self,i,o):return SimpleNamespace(id=o,institution_id=i,cohort_id='cohort',academic_period_id='sem')
class Academic:
 def binding_for_cohort(self,i,c):return CurriculumCohortBinding('b','cur',c,'admin',NOW)
 def curriculum(self,i,c):return CurriculumVersion('cur',i,'program','MED','Medicine',1,CurriculumState.PUBLISHED,'year',None,1,'admin',NOW,NOW)
 def courses(self,c):return (CurriculumCourse('cc','cur',1,'UE1','ANA','Anatomie',5,100,1),)
class Students:
 def __init__(self):self.student=StudentRecord('stu','inst','student','M-1','r','app','program','cur','cohort','A','B',None,None,None,None,StudentState.ACTIVE,1,NOW,NOW)
 def by_account(self,i,a):return self.student if a=='student' and i=='inst' else None
 def registrations(self,s):return (AcademicRegistration('reg','stu','inst','year','cohort','cur',RegistrationState.ENROLLED,'admin',NOW,1),)
def service():
 r=Repo();st=Students();return AcademicDeliveryService(r,Campus(),Teaching(),Academic(),st,lambda:NOW),r

def test_offering_is_bound_to_published_cohort_curriculum_course():
 s,r=service();x=s.bind_offering('admin','inst','off','cc');assert x.curriculum_id=='cur' and x.curriculum_course_id=='cc';assert s.bind_offering('admin','inst','off','cc').id==x.id

def test_offering_rejects_course_outside_cohort_curriculum():
 s,_=service()
 with pytest.raises(ValueError,match='course_not_in'):s.bind_offering('admin','inst','off','other')

def test_student_eligibility_requires_real_course_registration():
 s,r=service();s.bind_offering('admin','inst','off','cc')
 with pytest.raises(PermissionError,match='course_registration_required'):s.assert_student_eligible('student','inst','off')
 r.cr=StudentCourseRegistration('cr','reg','stu','cc',1,'ANA','Anatomie',5,CourseRegistrationState.ENROLLED,NOW)
 assert s.assert_student_eligible('student','inst','off').id=='cr'

def test_published_result_updates_canonical_student_course_state():
 s,r=service();s.bind_offering('admin','inst','off','cc');r.cr=StudentCourseRegistration('cr','reg','stu','cc',1,'ANA','Anatomie',5,CourseRegistrationState.ENROLLED,NOW)
 assert s.record_published_result('admin','inst','off','student',passed=True,complete=True,published=True)==CourseRegistrationState.VALIDATED
 assert r.state==CourseRegistrationState.VALIDATED
 with pytest.raises(ValueError,match='final_result_required'):s.record_published_result('admin','inst','off','student',passed=False,complete=False,published=True)

def test_gradebook_enforces_delivery_eligibility_and_syncs_published_result():
 from tests.test_gradebook_lot25 import setup
 s,i,o=setup()
 class Delivery:
  def __init__(self):self.checked=[];self.synced=[]
  def assert_student_eligible(self,a,iid,oid):self.checked.append((a,iid,oid));return True
  def record_published_result(self,a,iid,oid,student,**kw):self.synced.append((student,kw))
 d=Delivery();s.delivery=d
 g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20);g=s.open('teach',i.id,g.id,1)
 s.set_mark('teach',i.id,g.id,c.id,'stu',score=15);g=s.lock('teach',i.id,g.id,2);s.publish('teach',i.id,g.id,3)
 assert any(x[0]=='stu' for x in d.checked)
 assert len(d.synced)==1 and d.synced[0][0]=='stu'
 assert d.synced[0][1]['passed'] is True and d.synced[0][1]['published'] is True
 assert d.synced[0][1]['gradebook_id']==g.id and d.synced[0][1]['percent']==75.0

def test_canonical_publication_preflights_all_students_before_state_change():
 from tests.test_gradebook_lot25 import setup
 from app.modules.gradebook.domain.model import GradebookState
 s,i,o=setup()
 class Delivery:
  def assert_student_eligible(self,*args):raise PermissionError('missing_canonical_registration')
  def record_published_result(self,*args,**kwargs):raise AssertionError('must_not_write')
 g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20)
 g=s.open('teach',i.id,g.id,1);s.set_mark('teach',i.id,g.id,c.id,'stu',score=15);g=s.lock('teach',i.id,g.id,2)
 s.delivery=Delivery()
 with pytest.raises(PermissionError,match='missing_canonical_registration'):s.publish('teach',i.id,g.id,3)
 assert s.repo.gradebook(i.id,g.id).state==GradebookState.LOCKED

def test_canonical_gradebook_cannot_retract_without_student_result_reversal():
 from tests.test_gradebook_lot25 import setup
 from app.modules.gradebook.domain.model import GradebookState
 s,i,o=setup()
 class Delivery:
  def assert_student_eligible(self,*args):return True
  def record_published_result(self,*args,**kwargs):return None
 s.delivery=Delivery()
 g=s.create('teach',i.id,o.id);c=s.add_component('teach',i.id,g.id,title='Examen',kind='exam',weight_percent=100,max_score=20)
 g=s.open('teach',i.id,g.id,1);s.set_mark('teach',i.id,g.id,c.id,'stu',score=15);g=s.lock('teach',i.id,g.id,2);g=s.publish('teach',i.id,g.id,3)
 with pytest.raises(ValueError,match='canonical_result_reversal_required'):s.retract('owner',i.id,g.id,4,'Correction officielle')
 assert s.repo.gradebook(i.id,g.id).state==GradebookState.PUBLISHED


def test_published_result_persists_gradebook_percent_and_evidence_provenance():
 s,r=service();s.bind_offering('admin','inst','off','cc');r.cr=StudentCourseRegistration('cr','reg','stu','cc',1,'ANA','Anatomie',5,CourseRegistrationState.ENROLLED,NOW)
 s.record_published_result('admin','inst','off','student',passed=True,complete=True,published=True,gradebook_id='gb',percent=82.25,components=('Exam:16.45/20',))
 assert len(r.published)==1
 x=r.published[0];assert x.gradebook_id=='gb' and x.percent==82.25 and x.passed is True and len(x.evidence_hash)==64

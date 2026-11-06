from datetime import UTC,date,datetime,timedelta
import pytest
from app.modules.campus.application.service import CampusService
from app.modules.campus.domain.model import *
from app.modules.teaching.application.service import TeachingService
from app.modules.teaching.domain.model import *
from app.modules.assignments.application.service import AssignmentService
from app.modules.assignments.domain.model import *
from test_campus_lot22 import Repo as CampusRepo
from test_teaching_lot23 import Repo as TeachingRepo
class Repo:
 def __init__(self):self.a={};self.c={};self.s={};self.g={};self.f=[];self.groups={};self.items={};self.rp=[]
 def assignment(self,i,id):x=self.a.get(id);return x if x and x.institution_id==i else None
 def save_assignment(self,x,expected=None):
  old=self.a.get(x.id)
  if old and expected is not None and old.row_version!=expected:raise ValueError('assignment_concurrent_modification')
  self.a[x.id]=x
 def assignments_for_offering(self,o):return tuple(x for x in self.a.values() if x.offering_id==o)
 def save_criterion(self,x):self.c[x.id]=x
 def criteria(self,a):return tuple(sorted((x for x in self.c.values() if x.assignment_id==a),key=lambda x:x.position))
 def submission(self,i,id):x=self.s.get(id);return x if x and x.institution_id==i else None
 def save_submission(self,x,expected=None):self.s[x.id]=x
 def submissions_for_student(self,a,stu):return tuple(x for x in self.s.values() if x.assignment_id==a and x.student_account_id==stu)
 def submissions(self,a):return tuple(x for x in self.s.values() if x.assignment_id==a)
 def grade_for_submission(self,s):return self.g.get(s)
 def save_grade(self,x):self.g[x.submission_id]=x
 def save_similarity(self,x):
  self.f=[z for z in self.f if z.id!=x.id];self.f.append(x)
 def similarity(self,id):return next((z for z in self.f if z.id==id),None)
 def save_group(self,x):self.groups[(x.assignment_id,x.group_key)]=x
 def group(self,a,k):return self.groups.get((a,k))
 def save_auto_item(self,x):self.items[x.id]=x
 def auto_items(self,a):return tuple(x for x in self.items.values() if x.assignment_id==a)
 def save_reopen(self,x):self.rp.append(x)
 def reopens(self,a):return tuple(x for x in self.rp if x.assignment_id==a)
def setup(now=None):
 clock=[now or datetime(2026,9,25,12,tzinfo=UTC)];nowf=lambda:clock[0];cr=CampusRepo();cs=CampusService(cr,nowf);i=cs.create_institution('owner',name='Université',slug='univ');p=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Médecine',code='MED');y=cs.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2026',starts_on=date(2026,9,1),ends_on=date(2027,7,1));co=cs.create_cohort('owner',i.id,program_unit_id=p.id,academic_period_id=y.id,name='BAC1',level='L1')
 for a,r in [('teach',CampusRole.TEACHER),('stu',CampusRole.STUDENT),('stu2',CampusRole.STUDENT)]:cs.invite_member('owner',i.id,account_id=a,role=r);cs.accept_invitation(a,i.id)
 cs.enroll('owner',i.id,cohort_id=co.id,student_account_id='stu');cs.enroll('owner',i.id,cohort_id=co.id,student_account_id='stu2');cr.enrollments_for_student=lambda ii,a:tuple(x for x in cr.e.values() if x.institution_id==ii and x.student_account_id==a)
 tr=TeachingRepo();ts=TeachingService(tr,cr,nowf);c=ts.create_course('owner',i.id,code='ANA',title='Anatomie');o=ts.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='ANA');ts.assign_teacher('owner',i.id,o.id,teacher_account_id='teach');ts.publish_offering('teach',i.id,o.id,1)
 return AssignmentService(Repo(),cr,tr,nowf),i,o,clock
def test_assignment_submission_and_human_grade():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP1',due_at=clock[0]+timedelta(days=1),max_score=20);s.add_criterion('teach',i.id,a.id,label='Raisonnement',max_points=20);a=s.publish('teach',i.id,a.id,1);sub=s.submit('stu',i.id,a.id,text_content='Réponse argumentée');g=s.propose_grade('teach',i.id,sub.id,proposed_score=15,feedback='Bonne structure',confidence=.7);assert g.final_score is None;g=s.validate_grade('teach',i.id,sub.id,final_score=16);assert g.final_score==16 and g.validated_by=='teach'
def test_late_attempt_and_attempt_limit():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]-timedelta(hours=1),closes_at=clock[0]+timedelta(days=1));a=s.publish('teach',i.id,a.id,1);sub=s.submit('stu',i.id,a.id,text_content='x');assert sub.state==SubmissionState.LATE
 with pytest.raises(ValueError,match='attempt_limit'):s.submit('stu',i.id,a.id,text_content='again')
def test_rubric_total_must_match():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]+timedelta(days=1),max_score=20);s.add_criterion('teach',i.id,a.id,label='A',max_points=10)
 with pytest.raises(ValueError,match='rubric_total_mismatch'):s.publish('teach',i.id,a.id,1)
def test_similarity_is_review_flag_not_accusation():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]+timedelta(days=1),max_attempts=1);a=s.publish('teach',i.id,a.id,1);s.submit('stu',i.id,a.id,text_content='cellule membrane noyau cytoplasme énergie');s.submit('stu2',i.id,a.id,text_content='cellule membrane noyau cytoplasme énergie');flags=s.similarity_flags('teach',i.id,a.id);assert flags and flags[0].review_state=='needs_review'
def test_non_enrolled_or_other_student_cannot_grade():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]+timedelta(days=1));a=s.publish('teach',i.id,a.id,1);sub=s.submit('stu',i.id,a.id,text_content='x')
 with pytest.raises(PermissionError):s.validate_grade('stu2',i.id,sub.id,final_score=10)

def test_state_machine_and_results_publication():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]+timedelta(days=1));a=s.publish('teach',i.id,a.id,1);a=s.transition('teach',i.id,a.id,to_state='grading',expected_version=2);a=s.transition('teach',i.id,a.id,to_state='results_published',expected_version=3);assert a.state==AssignmentState.RESULTS_PUBLISHED
def test_group_membership_is_authoritative():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='G',kind=AssignmentKind.GROUP,due_at=clock[0]+timedelta(days=1));s.create_group('teach',i.id,a.id,group_key='G1',members=['stu','stu2']);a=s.publish('teach',i.id,a.id,1);sub=s.submit('stu',i.id,a.id,text_content='collectif',group_key='G1');assert sub.group_key=='G1'
def test_deterministic_and_sympy_grading():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='Math',due_at=clock[0]+timedelta(days=1),max_score=20);q=s.add_auto_item('teach',i.id,a.id,kind='symbolic',prompt='expr',expected_answer='2*x+2',points=20);a=s.publish('teach',i.id,a.id,1);sub=s.submit('stu',i.id,a.id,text_content='answers');g=s.deterministic_grade('teach',i.id,sub.id,answers={q.id:'2*(x+1)'});assert g.proposed_score==20 and g.confidence==1
def test_reopen_is_explicit_and_auditable_contract():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]-timedelta(days=2),closes_at=clock[0]-timedelta(days=1));a=s.publish('teach',i.id,a.id,1)
 with pytest.raises(ValueError,match='closed'):s.submit('stu',i.id,a.id,text_content='x')
 s.grant_reopen('teach',i.id,a.id,until=clock[0]+timedelta(hours=2),reason='Incident réseau',student_account_id='stu');assert s.submit('stu',i.id,a.id,text_content='x')
def test_similarity_review_never_auto_accuses():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]+timedelta(days=1));a=s.publish('teach',i.id,a.id,1);s.submit('stu',i.id,a.id,text_content='cellule membrane noyau cytoplasme énergie');s.submit('stu2',i.id,a.id,text_content='cellule membrane noyau cytoplasme énergie');f=s.similarity_flags('teach',i.id,a.id)[0];r=s.review_similarity('teach',i.id,f.id,decision='cleared');assert r.review_state=='cleared'


def test_results_are_private_until_explicit_complete_publication():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]+timedelta(days=1));a=s.publish('teach',i.id,a.id,1);sub=s.submit('stu',i.id,a.id,text_content='x');s.validate_grade('teach',i.id,sub.id,final_score=17,feedback='Validé');a=s.transition('teach',i.id,a.id,to_state='grading',expected_version=2)
 with pytest.raises(PermissionError,match='results_not_published'):s.student_result('stu',i.id,a.id)
 a=s.publish_results('teach',i.id,a.id,expected_version=3);r=s.student_result('stu',i.id,a.id);assert r.final_score==17 and r.max_score==20 and r.published

def test_results_publication_requires_all_submissions_graded():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]+timedelta(days=1));a=s.publish('teach',i.id,a.id,1);s.submit('stu',i.id,a.id,text_content='x');s.submit('stu2',i.id,a.id,text_content='y');a=s.transition('teach',i.id,a.id,to_state='grading',expected_version=2)
 with pytest.raises(ValueError,match='incomplete_grading'):s.publish_results('teach',i.id,a.id,expected_version=3)

def test_result_retraction_is_explicit_and_hides_student_result():
 s,i,o,clock=setup();a=s.create('teach',i.id,o.id,title='TP',due_at=clock[0]+timedelta(days=1));a=s.publish('teach',i.id,a.id,1);sub=s.submit('stu',i.id,a.id,text_content='x');s.validate_grade('teach',i.id,sub.id,final_score=18);a=s.transition('teach',i.id,a.id,to_state='grading',expected_version=2);a=s.publish_results('teach',i.id,a.id,expected_version=3);a=s.retract_results('teach',i.id,a.id,expected_version=4,reason='Erreur de barème')
 with pytest.raises(PermissionError):s.student_result('stu',i.id,a.id)

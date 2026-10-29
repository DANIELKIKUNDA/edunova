from datetime import UTC,date,datetime,timedelta
import pytest
from app.modules.campus.application.service import CampusService
from app.modules.campus.domain.model import *
from app.modules.teaching.application.service import TeachingService
from app.modules.teaching.domain.model import *
from test_campus_lot22 import Repo as CampusRepo
class Repo:
 def __init__(self):self.c={};self.o={};self.a={};self.s={};self.r={};self.sy={};self.t={};self.rr={}
 def course(self,i,id):x=self.c.get(id);return x if x and x.institution_id==i else None
 def course_by_code(self,i,code):return next((x for x in self.c.values() if x.institution_id==i and x.code==code.upper()),None)
 def save_course(self,x):self.c[x.id]=x
 def offering(self,i,id):x=self.o.get(id);return x if x and x.institution_id==i else None
 def save_offering(self,x,expected=None):
  old=self.o.get(x.id)
  if old and expected is not None and old.row_version!=expected:raise ValueError('teaching_concurrent_modification')
  self.o[x.id]=x
 def list_offerings(self,i):return tuple(x for x in self.o.values() if x.institution_id==i)
 def assignment(self,o,a):return self.a.get((o,a))
 def save_assignment(self,x):self.a[(x.offering_id,x.teacher_account_id)]=x
 def list_assignments(self,o):return tuple(x for (oo,_),x in self.a.items() if oo==o and x.active)
 def session(self,i,id):x=self.s.get(id);return x if x and x.institution_id==i else None
 def save_session(self,x,expected=None):self.s[x.id]=x
 def list_sessions(self,o):return tuple(x for x in self.s.values() if x.offering_id==o)
 def resource(self,i,id):x=self.r.get(id);return x if x and x.institution_id==i else None
 def save_resource(self,x,expected=None):self.r[x.id]=x
 def list_resources(self,o):return tuple(x for x in self.r.values() if x.offering_id==o)
 def syllabus(self,i,id):x=self.sy.get(id);return x if x and x.institution_id==i else None
 def list_syllabi(self,o):return tuple(x for x in self.sy.values() if x.offering_id==o)
 def save_syllabus(self,x,expected=None):
  old=self.sy.get(x.id)
  if old and expected is not None and old.row_version!=expected:raise ValueError('teaching_concurrent_modification')
  self.sy[x.id]=x
 def topic(self,i,id):x=self.t.get(id);return x if x and x.institution_id==i else None
 def list_topics(self,sy):return tuple(sorted((x for x in self.t.values() if x.syllabus_id==sy),key=lambda x:x.position))
 def save_topic(self,x,expected=None):
  old=self.t.get(x.id)
  if old and expected is not None and old.row_version!=expected:raise ValueError('teaching_concurrent_modification')
  self.t[x.id]=x
 def list_resource_revisions(self,r):return tuple(x for x in self.rr.values() if x.resource_id==r)
 def save_resource_revision(self,x):self.rr[x.id]=x

def setup():
 now=lambda:datetime(2026,9,25,10,tzinfo=UTC);cr=CampusRepo();cs=CampusService(cr,now);i=cs.create_institution('owner',name='Université',slug='univ');p=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Médecine',code='MED');y=cs.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2026',starts_on=date(2026,9,1),ends_on=date(2027,7,1));co=cs.create_cohort('owner',i.id,program_unit_id=p.id,academic_period_id=y.id,name='BAC1',level='L1')
 for a,r in [('teach',CampusRole.TEACHER),('stu',CampusRole.STUDENT)]:cs.invite_member('owner',i.id,account_id=a,role=r);cs.accept_invitation(a,i.id)
 cs.enroll('owner',i.id,cohort_id=co.id,student_account_id='stu');cr.enrollments_for_student=lambda ii,a:tuple(x for x in cr.e.values() if x.institution_id==ii and x.student_account_id==a)
 return TeachingService(Repo(),cr,now),i,co,y
def test_full_delivery_flow_and_student_visibility():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='ANA101',title='Anatomie',credits=6);o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='Anatomie BAC1');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach');o=s.publish_offering('teach',i.id,o.id,1);assert s.my_offerings('stu',i.id)[0].id==o.id
 r=s.add_resource('teach',i.id,o.id,title='Chapitre 1',resource_type='pdf',uri='library://x',source_revision='rev-1');s.publish_resource('teach',i.id,r.id,1);ss=s.add_session('teach',i.id,o.id,title='Ostéologie',starts_at=s.now(),ends_at=s.now()+timedelta(hours=2));ss=s.complete_session('teach',i.id,ss.id,summary='Introduction au squelette',next_topic='Crâne',expected_version=1);d=s.offering_detail('stu',i.id,o.id);assert d['resources'][0].state==ResourceState.PUBLISHED and d['sessions'][0].state==SessionState.COMPLETED
def test_unassigned_teacher_cannot_modify_offering():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='A',title='A');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='A')
 with pytest.raises(PermissionError,match='write_forbidden'):s.add_resource('teach',i.id,o.id,title='x',resource_type='pdf',uri='x')
def test_publish_requires_teacher():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='A',title='A');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='A')
 with pytest.raises(ValueError,match='teacher_required'):s.publish_offering('owner',i.id,o.id,1)
def test_cross_tenant_course_access_denied():
 s,i,co,y=setup();other=CampusService(s.campus_repo,s.now).create_institution('other',name='Other',slug='other');c=s.create_course('owner',i.id,code='A',title='A')
 with pytest.raises(PermissionError):s.create_offering('other',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='bad')
def test_concurrent_publish_rejected():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='A',title='A');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='A');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach')
 with pytest.raises(ValueError,match='concurrent'):s.publish_offering('teach',i.id,o.id,99)

def test_syllabus_outcomes_progress_and_knowledge_graph_refs():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='PHY',title='Physiologie');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='Physio');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach');o=s.publish_offering('teach',i.id,o.id,1)
 sy=s.create_syllabus('teach',i.id,o.id,title='Plan officiel',learning_outcomes=['Expliquer le potentiel membranaire']);t=s.add_syllabus_topic('teach',i.id,sy.id,title='Membrane',learning_objectives=['Analyser les gradients'],concept_refs=['kg:membrane'],planned_minutes=120);sy=s.approve_syllabus('teach',i.id,sy.id,1);t=s.update_topic_progress('teach',i.id,t.id,state='taught',expected_version=1);p=s.teaching_progress('stu',i.id,o.id);assert p['completion_percent']==100 and p['syllabus_version']==1 and t.concept_refs==('kg:membrane',)
def test_only_lead_or_admin_can_approve_syllabus():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='BIO',title='Bio');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='Bio');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach',role=TeacherRole.ASSISTANT);sy=s.create_syllabus('teach',i.id,o.id,title='Plan');s.add_syllabus_topic('teach',i.id,sy.id,title='Cellule')
 with pytest.raises(PermissionError,match='approval_forbidden'):s.approve_syllabus('teach',i.id,sy.id,1)
def test_resource_revision_returns_to_draft_and_keeps_history():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='CHEM',title='Chimie');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='Chimie');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach');r=s.add_resource('teach',i.id,o.id,title='Support',resource_type='pdf',uri='v1');r=s.publish_resource('teach',i.id,r.id,1);r=s.revise_resource('teach',i.id,r.id,title='Support corrigé',uri='v2',change_note='erratum',expected_version=2);assert r.state==ResourceState.DRAFT and len(s.repo.list_resource_revisions(r.id))==1
def test_progress_denies_non_enrolled_student():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='X',title='X');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='X');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach');s.publish_offering('teach',i.id,o.id,1);s.campus_repo.e.clear()
 with pytest.raises(PermissionError):s.teaching_progress('stu',i.id,o.id)

def test_session_requires_existing_published_offering():
 s,i,co,y=setup()
 with pytest.raises(ValueError,match='offering_not_found'):s.add_session('owner',i.id,'missing',title='x',starts_at=s.now(),ends_at=s.now()+timedelta(hours=1))
 c=s.create_course('owner',i.id,code='D',title='D');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='D');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach')
 with pytest.raises(ValueError,match='not_published'):s.add_session('teach',i.id,o.id,title='x',starts_at=s.now(),ends_at=s.now()+timedelta(hours=1))

def test_cannot_remove_last_lead_from_published_offering():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='L',title='L');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='L');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach');s.publish_offering('teach',i.id,o.id,1)
 with pytest.raises(ValueError,match='lead_required'):s.deactivate_teacher('owner',i.id,o.id,'teach')

def test_cancel_and_retire_are_versioned():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='R',title='R');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='R');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach');s.publish_offering('teach',i.id,o.id,1)
 ss=s.add_session('teach',i.id,o.id,title='x',starts_at=s.now(),ends_at=s.now()+timedelta(hours=1));assert s.cancel_session('teach',i.id,ss.id,1).state==SessionState.CANCELLED
 r=s.add_resource('teach',i.id,o.id,title='r',resource_type='pdf',uri='x');r=s.publish_resource('teach',i.id,r.id,1);assert s.retire_resource('teach',i.id,r.id,2).state==ResourceState.RETIRED

def test_new_approved_syllabus_supersedes_previous():
 s,i,co,y=setup();c=s.create_course('owner',i.id,code='S',title='S');o=s.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='S');s.assign_teacher('owner',i.id,o.id,teacher_account_id='teach')
 a=s.create_syllabus('teach',i.id,o.id,title='v1');s.add_syllabus_topic('teach',i.id,a.id,title='one');a=s.approve_syllabus('teach',i.id,a.id,1)
 b=s.create_syllabus('teach',i.id,o.id,title='v2');s.add_syllabus_topic('teach',i.id,b.id,title='two');b=s.approve_syllabus('teach',i.id,b.id,1)
 assert s.repo.syllabus(i.id,a.id).state==SyllabusState.SUPERSEDED and b.state==SyllabusState.APPROVED

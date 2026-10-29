from datetime import UTC,date,datetime,timedelta
import pytest
from app.modules.campus.application.service import CampusService
from app.modules.campus.domain.model import *
from app.modules.teaching.application.service import TeachingService
from app.modules.campus_operations.application.service import CampusOperationsService
from app.modules.campus_operations.domain.model import *
from test_campus_lot22 import Repo as CampusRepo
from test_teaching_lot23 import Repo as TeachingRepo
class Repo:
 def __init__(self):self.p={};self.s={};self.r={};self.d={};self.an={};self.ab={};self.ev={}
 def policy(self,i):return self.p.get(i)
 def save_policy(self,x):self.p[x.institution_id]=x
 def attendance_session(self,i,id):x=self.s.get(id);return x if x and x.institution_id==i else None
 def attendance_for_teaching_session(self,i,t):return next((x for x in self.s.values() if x.institution_id==i and x.teaching_session_id==t),None)
 def save_session(self,x,expected=None):
  old=self.s.get(x.id)
  if old and expected is not None and old.row_version!=expected:raise ValueError('attendance_concurrent_modification')
  self.s[x.id]=x
 def bound_device(self,i,a):return self.d.get((i,a))
 def bind_device(self,i,a,d,now):self.d[(i,a)]=d
 def record(self,sid,a):return self.r.get((sid,a))
 def save_record(self,x,expected=None):self.r[(x.attendance_session_id,x.student_account_id)]=x
 def records(self,sid):return tuple(x for (s,_),x in self.r.items() if s==sid)
 def announcement(self,i,id):return self.an.get(id)
 def save_announcement(self,x,expected=None):self.an[x.id]=x
 def announcements(self,i):return tuple(x for x in self.an.values() if x.institution_id==i)
 def absence_request(self,i,id):return self.ab.get(id)
 def absence_for_student_session(self,sid,a):return next((x for x in self.ab.values() if x.attendance_session_id==sid and x.student_account_id==a),None)
 def save_absence(self,x,expected=None):self.ab[x.id]=x
 def absences(self,i):return tuple(x for x in self.ab.values() if x.institution_id==i)
 def event(self,i,id):return self.ev.get(id)
 def save_event(self,x,expected=None):self.ev[x.id]=x
 def events(self,i):return tuple(x for x in self.ev.values() if x.institution_id==i)
def setup():
 clock=[datetime(2026,9,25,8,tzinfo=UTC)];now=lambda:clock[0];cr=CampusRepo();cs=CampusService(cr,now);i=cs.create_institution('owner',name='Université',slug='universite');p=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Med',code='MED');y=cs.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2026',starts_on=date(2026,9,1),ends_on=date(2027,7,1));co=cs.create_cohort('owner',i.id,program_unit_id=p.id,academic_period_id=y.id,name='BAC1',level='L1')
 for a,r in [('teach',CampusRole.TEACHER),('stu',CampusRole.STUDENT),('stu2',CampusRole.STUDENT)]:cs.invite_member('owner',i.id,account_id=a,role=r);cs.accept_invitation(a,i.id)
 cs.enroll('owner',i.id,cohort_id=co.id,student_account_id='stu');cr.enrollments_for_cohort=lambda c:tuple(x for x in cr.e.values() if x.cohort_id==c);cr.enrollments_for_student=lambda i,a:tuple(x for x in cr.e.values() if x.institution_id==i and x.student_account_id==a)
 tr=TeachingRepo();ts=TeachingService(tr,cr,now);c=ts.create_course('owner',i.id,code='CAR',title='Cardio');o=ts.create_offering('owner',i.id,course_id=c.id,cohort_id=co.id,academic_period_id=y.id,label='CAR');ts.assign_teacher('owner',i.id,o.id,teacher_account_id='teach');o=ts.publish_offering('teach',i.id,o.id,1);sess=ts.add_session('teach',i.id,o.id,title='IC',starts_at=clock[0],ends_at=clock[0]+timedelta(hours=2))
 return CampusOperationsService(Repo(),cr,tr,now,secret='test-secret'),i,sess,clock
def test_rotating_qr_device_binding_and_replay_control():
 s,i,ts,clock=setup();a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);s.bind_device('stu',i.id,'device-12345');token=s.qr_token('teach',i.id,a.id);r=s.scan('stu',i.id,a.id,token,device_id='device-12345');assert r.review==AttendanceReview.CLEAR and r.status==AttendanceStatus.PRESENT
 with pytest.raises(ValueError,match='already'):s.scan('stu',i.id,a.id,token,device_id='device-12345')
def test_qr_expires_quickly_and_is_session_scoped():
 s,i,ts,clock=setup();a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);tok=s.qr_token('teach',i.id,a.id);clock[0]+=timedelta(seconds=40)
 with pytest.raises(ValueError,match='expired'):s.scan('stu',i.id,a.id,tok,device_id='device-12345')
def test_unbound_or_wrong_device_is_flagged_not_accused():
 s,i,ts,clock=setup();a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);tok=s.qr_token('teach',i.id,a.id);r=s.scan('stu',i.id,a.id,tok,device_id='unknown-device');assert r.review==AttendanceReview.NEEDS_REVIEW and r.risk_score>=70
def test_non_enrolled_student_cannot_mark_presence():
 s,i,ts,clock=setup();a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);tok=s.qr_token('teach',i.id,a.id)
 with pytest.raises(PermissionError,match='enrollment'):s.scan('stu2',i.id,a.id,tok,device_id='x-device-123')
def test_location_policy_flags_remote_scan_for_review():
 s,i,ts,clock=setup();s.configure_policy('owner',i.id,require_location=True,location_latitude=-11.66,location_longitude=27.49,radius_meters=50,max_accuracy_meters=20);a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);s.bind_device('stu',i.id,'device-12345');tok=s.qr_token('teach',i.id,a.id);r=s.scan('stu',i.id,a.id,tok,device_id='device-12345',latitude=-11.66,longitude=27.48,accuracy_m=10);assert r.review==AttendanceReview.NEEDS_REVIEW
def test_signed_proximity_is_independent_short_lived_proof():
 s,i,ts,clock=setup();s.configure_policy('owner',i.id,proximity_mode='signed_beacon',proximity_ttl_seconds=5);a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);s.bind_device('stu',i.id,'device-12345');qr=s.qr_token('teach',i.id,a.id);prox=s.proximity_token('teach',i.id,a.id);r=s.scan('stu',i.id,a.id,qr,device_id='device-12345',proximity_token=prox);assert r.review==AttendanceReview.CLEAR

def test_shared_qr_without_signed_proximity_is_flagged_high_risk():
 s,i,ts,clock=setup();s.configure_policy('owner',i.id,proximity_mode='signed_beacon',proximity_ttl_seconds=5);a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);s.bind_device('stu',i.id,'device-12345');qr=s.qr_token('teach',i.id,a.id);r=s.scan('stu',i.id,a.id,qr,device_id='device-12345');assert r.review==AttendanceReview.NEEDS_REVIEW and r.risk_score>=80 and 'signed_proximity_failed' in r.evidence

def test_expired_proximity_proof_is_rejected_even_when_qr_still_valid():
 s,i,ts,clock=setup();s.configure_policy('owner',i.id,qr_ttl_seconds=30,proximity_mode='signed_beacon',proximity_ttl_seconds=5);a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);s.bind_device('stu',i.id,'device-12345');qr=s.qr_token('teach',i.id,a.id);prox=s.proximity_token('teach',i.id,a.id);clock[0]+=timedelta(seconds=12);r=s.scan('stu',i.id,a.id,qr,device_id='device-12345',proximity_token=prox);assert r.review==AttendanceReview.NEEDS_REVIEW and 'signed_proximity_failed' in r.evidence


def test_institutional_announcement_workflow_and_retraction():
 s,i,ts,clock=setup();x=s.create_announcement('owner',i.id,'Rentrée','Bienvenue','students');assert x.state==AnnouncementState.PUBLISHED;assert s.announcements('stu',i.id)[0].title=='Rentrée';y=s.retract_announcement('owner',i.id,x.id,'information remplacée',1);assert y.state==AnnouncementState.RETRACTED and not s.announcements('stu',i.id)

def test_absence_justification_requires_human_decision_and_updates_record():
 s,i,ts,clock=setup();a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);s.bind_device('stu',i.id,'device-12345');tok=s.qr_token('teach',i.id,a.id);r=s.scan('stu',i.id,a.id,tok,device_id='device-12345');q=s.submit_absence('stu',i.id,a.id,'Consultation médicale','local://proof.pdf');assert q.state==AbsenceRequestState.PENDING;y=s.decide_absence('teach',i.id,q.id,'approved','justificatif vérifié',1);assert y.state==AbsenceRequestState.APPROVED;assert s.repo.record(a.id,'stu').status==AttendanceStatus.JUSTIFIED

def test_operational_calendar_is_auditable_and_student_visible():
 s,i,ts,clock=setup();x=s.create_event('teach',i.id,'change','Salle modifiée',clock[0]+timedelta(days=1),clock[0]+timedelta(days=1,hours=2),offering_id=ts.offering_id,details='Nouvelle salle B12',location='B12');assert s.calendar('stu',i.id)[0].id==x.id;y=s.update_event_state('teach',i.id,x.id,'cancelled','cours reporté',1);assert y.state==CalendarEventState.CANCELLED

def test_operations_dashboard_aggregates_daily_campus_signals():
 s,i,ts,clock=setup();a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);s.bind_device('stu',i.id,'device-12345');s.scan('stu',i.id,a.id,s.qr_token('teach',i.id,a.id),device_id='device-12345');s.create_announcement('owner',i.id,'Info','Message');d=s.operations_dashboard('owner',i.id);assert d['teaching_sessions']>=1 and d['attendance_records']==1 and d['announcements_active']==1

def test_closing_attendance_materializes_missing_enrolled_students_as_absent():
 s,i,ts,clock=setup();a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);a=s.close('teach',i.id,a.id,2);r=s.repo.record(a.id,'stu');assert r is not None and r.status==AttendanceStatus.ABSENT and r.method=='closure'

def test_approved_absence_before_close_is_materialized_as_justified():
 s,i,ts,clock=setup();a=s.create_attendance('teach',i.id,ts.id);a=s.open('teach',i.id,a.id,1);q=s.submit_absence('stu',i.id,a.id,'Hospitalisation','local://proof');s.decide_absence('teach',i.id,q.id,'approved','preuve vérifiée',1);s.close('teach',i.id,a.id,2);assert s.repo.record(a.id,'stu').status==AttendanceStatus.JUSTIFIED

def test_campus_notifications_use_remote_push_channel_for_server_originated_events():
 from app.modules.engagement.domain.model import DeliveryChannel
 class Engagement:
  def __init__(self): self.intents=[]
  def schedule(self,intent): self.intents.append(intent); return True
 s,i,ts,clock=setup(); e=Engagement(); s.engagement=e
 now=clock[0]
 s.create_announcement('owner',i.id,'TP déplacé','Nouvelle salle','students')
 assert e.intents and all(x.channel==DeliveryChannel.PUSH for x in e.intents)

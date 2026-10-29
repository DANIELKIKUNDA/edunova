from __future__ import annotations
import base64,hashlib,hmac,json,math,os,time,uuid
from dataclasses import replace
from datetime import timedelta
from app.modules.engagement.domain.model import NotificationIntent,EngagementCategory,DeliveryChannel
from app.modules.campus.domain.model import CampusRole,MembershipState
from app.modules.campus_operations.domain.model import *
class CampusOperationsService:
 def __init__(self,repo,campus,teaching,now,audit=None,secret=None,proximity_secret=None,engagement=None,delivery=None):self.repo=repo;self.campus=campus;self.teaching=teaching;self.now=now;self.audit=audit;self.engagement=engagement;self.delivery=delivery;self.secret=(secret or os.getenv('ATTENDANCE_QR_SECRET') or 'development-attendance-secret-change-me').encode();self.proximity_secret=(proximity_secret or os.getenv('ATTENDANCE_PROXIMITY_SECRET') or 'development-proximity-secret-change-me').encode()
 def _notify(self,account,title,body,key,link='/campus'):
  if not self.engagement:return False
  now=self.now();return self.engagement.schedule(NotificationIntent(id=f'cn_{uuid.uuid4().hex}',account_id=account,dedupe_key=key,category=EngagementCategory.SYSTEM,channel=DeliveryChannel.PUSH,title=title,body=body,deep_link=link,fire_at=now,expires_at=now+timedelta(days=7),priority=85))
 def _announcement_targets(self,i,x):
  if x.offering_id:
   off=self.teaching.offering(i,x.offering_id)
   if not off:return ()
   students=[e.student_account_id for e in self.campus.enrollments_for_cohort(off.cohort_id) if e.active]
   teachers=[t.teacher_account_id for t in self.teaching.list_assignments(x.offering_id) if t.active]
   return tuple(students if x.audience in {'students','offering'} else teachers if x.audience=='teachers' else students+teachers)
  members=self.campus.list_members(i);return tuple(m.account_id for m in members if m.state==MembershipState.ACTIVE and (x.audience=='institution' or x.audience=='students' and m.role==CampusRole.STUDENT or x.audience=='teachers' and m.role==CampusRole.TEACHER))
 def _audit(self,a,action,t,id,meta=None):
  if self.audit:self.audit.write(actor_account_id=a,action=action,target_type=t,target_id=id,metadata=meta or {})
 def _member(self,a,i):
  m=self.campus.membership(i,a)
  if not m or m.state!=MembershipState.ACTIVE:raise PermissionError('campus_active_membership_required')
  return m
 def _staff(self,a,i,offering):
  m=self._member(a,i)
  if m.role in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}:return m
  ta=self.teaching.assignment(offering,a)
  if m.role!=CampusRole.TEACHER or not ta or not ta.active:raise PermissionError('attendance_teacher_required')
  return m
 def policy(self,i):return self.repo.policy(i) or AttendancePolicy('default',i,15,True,False,None,None,80,50,False,ProximityMode.NONE,10,1,self.now())
 def configure_policy(self,a,i,qr_ttl_seconds=15,require_device_binding=True,require_location=False,location_latitude=None,location_longitude=None,radius_meters=80,max_accuracy_meters=50,require_network_proof=False,proximity_mode='none',proximity_ttl_seconds=10):
  m=self._member(a,i)
  if m.role not in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}:raise PermissionError('attendance_admin_required')
  if not 5<=qr_ttl_seconds<=60 or not 5<=proximity_ttl_seconds<=30 or not 10<=radius_meters<=1000 or not 5<=max_accuracy_meters<=500 or (require_location and (location_latitude is None or location_longitude is None)):raise ValueError('attendance_policy_invalid')
  pm=ProximityMode(proximity_mode)
  old=self.repo.policy(i);x=AttendancePolicy(old.id if old else f'ap_{uuid.uuid4().hex}',i,qr_ttl_seconds,require_device_binding,require_location,location_latitude,location_longitude,radius_meters,max_accuracy_meters,require_network_proof,pm,proximity_ttl_seconds,(old.row_version+1 if old else 1),self.now());self.repo.save_policy(x);self._audit(a,'attendance.policy.updated','institution',i,{'qr_ttl':qr_ttl_seconds});return x
 def create_attendance(self,a,i,teaching_session_id,opens_at=None,closes_at=None):
  ts=self.teaching.session(i,teaching_session_id)
  if not ts:raise ValueError('teaching_session_not_found')
  self._staff(a,i,ts.offering_id)
  if self.repo.attendance_for_teaching_session(i,teaching_session_id):raise ValueError('attendance_session_exists')
  now=self.now();op=opens_at or ts.starts_at;cl=closes_at or min(ts.ends_at,op+timedelta(minutes=30))
  if cl<=op:raise ValueError('attendance_window_invalid')
  x=AttendanceSession(f'att_{uuid.uuid4().hex}',i,teaching_session_id,ts.offering_id,AttendanceSessionState.DRAFT,op,cl,0,1,a,now,now);self.repo.save_session(x);return x
 def open(self,a,i,sid,expected_version):
  x=self.repo.attendance_session(i,sid)
  if not x:raise ValueError('attendance_session_not_found')
  self._staff(a,i,x.offering_id)
  if x.row_version!=expected_version or x.state!=AttendanceSessionState.DRAFT:raise ValueError('attendance_invalid_transition')
  y=replace(x,state=AttendanceSessionState.OPEN,qr_epoch=x.qr_epoch+1,row_version=x.row_version+1,updated_at=self.now());self.repo.save_session(y,x.row_version);self._audit(a,'attendance.opened','attendance_session',sid);return y
 def close(self,a,i,sid,expected_version):
  x=self.repo.attendance_session(i,sid);self._staff(a,i,x.offering_id)
  if x.row_version!=expected_version or x.state!=AttendanceSessionState.OPEN:raise ValueError('attendance_invalid_transition')
  y=replace(x,state=AttendanceSessionState.CLOSED,row_version=x.row_version+1,updated_at=self.now());self.repo.save_session(y,x.row_version)
  off=self.teaching.offering(i,x.offering_id);now=self.now()
  if off:
   for e in self.campus.enrollments_for_cohort(off.cohort_id):
    if e.active and not self.repo.record(sid,e.student_account_id):
     if self.delivery:
      try:self.delivery.assert_student_eligible(e.student_account_id,i,x.offering_id)
      except (PermissionError,ValueError):continue
     req=self.repo.absence_for_student_session(sid,e.student_account_id);justified=bool(req and req.state==AbsenceRequestState.APPROVED)
     self.repo.save_record(AttendanceRecord(f'ar_{uuid.uuid4().hex}',i,sid,e.student_account_id,AttendanceStatus.JUSTIFIED if justified else AttendanceStatus.ABSENT,now,'closure',None,0,AttendanceReview.CONFIRMED if justified else AttendanceReview.CLEAR,'approved_absence_on_close' if justified else 'auto_absent_on_close',1,now))
  self._audit(a,'attendance.closed','attendance_session',sid);return y
 def qr_token(self,a,i,sid):
  x=self.repo.attendance_session(i,sid);self._staff(a,i,x.offering_id)
  if x.state!=AttendanceSessionState.OPEN:raise ValueError('attendance_not_open')
  p=self.policy(i);slot=int(self.now().timestamp())//p.qr_ttl_seconds;payload={'v':1,'i':i,'s':sid,'e':x.qr_epoch,'t':slot};raw=json.dumps(payload,separators=(',',':'),sort_keys=True).encode();sig=hmac.new(self.secret,raw,hashlib.sha256).digest();return base64.urlsafe_b64encode(raw+sig).decode().rstrip('=')
 def _verify(self,token,i,sid):
  try:
   data=base64.urlsafe_b64decode(token+'='*(-len(token)%4));raw,sig=data[:-32],data[-32:]
   if not hmac.compare_digest(sig,hmac.new(self.secret,raw,hashlib.sha256).digest()):raise ValueError
   p=json.loads(raw);pol=self.policy(i);slot=int(self.now().timestamp())//pol.qr_ttl_seconds
   if p['i']!=i or p['s']!=sid or p['t'] not in {slot,slot-1}:raise ValueError
   x=self.repo.attendance_session(i,sid)
   if not x or x.state!=AttendanceSessionState.OPEN or p['e']!=x.qr_epoch or not(x.opens_at<=self.now()<=x.closes_at):raise ValueError
   return x,pol
  except Exception:raise ValueError('attendance_qr_invalid_or_expired')
 def proximity_token(self,a,i,sid):
  x=self.repo.attendance_session(i,sid);self._staff(a,i,x.offering_id)
  if x.state!=AttendanceSessionState.OPEN:raise ValueError('attendance_not_open')
  p=self.policy(i)
  if p.proximity_mode!=ProximityMode.SIGNED_BEACON:raise ValueError('attendance_proximity_not_enabled')
  slot=int(self.now().timestamp())//p.proximity_ttl_seconds;payload={'v':1,'i':i,'s':sid,'e':x.qr_epoch,'p':slot};raw=json.dumps(payload,separators=(',',':'),sort_keys=True).encode();sig=hmac.new(self.proximity_secret,raw,hashlib.sha256).digest();return base64.urlsafe_b64encode(raw+sig).decode().rstrip('=')
 def _verify_proximity(self,token,i,sid,x,p):
  if p.proximity_mode==ProximityMode.NONE:return True
  if not token:return False
  try:
   data=base64.urlsafe_b64decode(token+'='*(-len(token)%4));raw,sig=data[:-32],data[-32:]
   if not hmac.compare_digest(sig,hmac.new(self.proximity_secret,raw,hashlib.sha256).digest()):return False
   q=json.loads(raw);slot=int(self.now().timestamp())//p.proximity_ttl_seconds
   return q.get('i')==i and q.get('s')==sid and q.get('e')==x.qr_epoch and q.get('p') in {slot,slot-1}
  except Exception:return False
 def bind_device(self,a,i,device_id):
  m=self._member(a,i)
  if m.role!=CampusRole.STUDENT or len(device_id.strip())<8:raise ValueError('attendance_device_invalid')
  existing=self.repo.bound_device(i,a)
  if existing and existing!=device_id:raise PermissionError('attendance_device_change_requires_admin')
  self.repo.bind_device(i,a,device_id,self.now());return {'bound':True,'device_id':device_id}
 def scan(self,a,i,sid,token,device_id=None,latitude=None,longitude=None,accuracy_m=None,network_proof=False,proximity_token=None):
  m=self._member(a,i)
  if m.role!=CampusRole.STUDENT:raise PermissionError('attendance_student_required')
  x,p=self._verify(token,i,sid)
  off=self.teaching.offering(i,x.offering_id)
  if not off or not any(e.active and e.student_account_id==a for e in self.campus.enrollments_for_cohort(off.cohort_id)):raise PermissionError('attendance_enrollment_required')
  if self.delivery:self.delivery.assert_student_eligible(a,i,x.offering_id)
  if self.repo.record(sid,a):raise ValueError('attendance_already_recorded')
  risk=0;ev=[]
  if p.require_device_binding:
   bound=self.repo.bound_device(i,a)
   if not bound or bound!=device_id:risk+=70;ev.append('device_binding_failed')
  if p.require_network_proof:risk+=20;ev.append('legacy_network_proof_untrusted')
  if p.proximity_mode==ProximityMode.SIGNED_BEACON and not self._verify_proximity(proximity_token,i,sid,x,p):risk+=80;ev.append('signed_proximity_failed')
  if p.require_location:
   if None in (latitude,longitude,accuracy_m,p.location_latitude,p.location_longitude):risk+=50;ev.append('location_missing')
   else:
    if accuracy_m>p.max_accuracy_meters:risk+=25;ev.append('location_accuracy_low')
    r=6371000;dlat=math.radians(latitude-p.location_latitude);dlon=math.radians(longitude-p.location_longitude);aa=math.sin(dlat/2)**2+math.cos(math.radians(p.location_latitude))*math.cos(math.radians(latitude))*math.sin(dlon/2)**2;dist=2*r*math.asin(math.sqrt(aa))
    if dist>p.radius_meters:risk+=70;ev.append(f'outside_radius:{int(dist)}m')
  risk=min(100,risk);review=AttendanceReview.NEEDS_REVIEW if risk>=40 else AttendanceReview.CLEAR;now=self.now();status=AttendanceStatus.LATE if now>x.opens_at+timedelta(minutes=10) else AttendanceStatus.PRESENT
  rec=AttendanceRecord(f'ar_{uuid.uuid4().hex}',i,sid,a,status,now,'dynamic_qr',device_id,risk,review,','.join(ev),1,now);self.repo.save_record(rec);self._audit(a,'attendance.scanned','attendance_record',rec.id,{'risk':risk,'review':review.value});return rec
 def review(self,a,i,sid,student,status,decision,reason,expected_version):
  x=self.repo.attendance_session(i,sid);self._staff(a,i,x.offering_id);r=self.repo.record(sid,student)
  if not r or r.row_version!=expected_version or not reason.strip():raise ValueError('attendance_review_invalid')
  y=replace(r,status=AttendanceStatus(status),review=AttendanceReview(decision),evidence=(r.evidence+';review:'+reason.strip()).strip(';'),row_version=r.row_version+1,updated_at=self.now());self.repo.save_record(y,r.row_version);self._audit(a,'attendance.reviewed','attendance_record',r.id,{'decision':decision,'reason':reason});return y
 def roster(self,a,i,sid):
  x=self.repo.attendance_session(i,sid);self._staff(a,i,x.offering_id);return self.repo.records(sid)
 def create_announcement(self,a,i,title,body,audience='institution',offering_id=None,publish_at=None):
  m=self._member(a,i)
  if m.role not in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.TEACHER}:raise PermissionError('announcement_staff_required')
  if m.role==CampusRole.TEACHER:
   if not offering_id:raise PermissionError('announcement_teacher_offering_required')
   self._staff(a,i,offering_id)
  if audience not in {'institution','students','teachers','offering'} or audience=='offering' and not offering_id or not title.strip() or not body.strip():raise ValueError('announcement_invalid')
  now=self.now();pa=publish_at or now;state=AnnouncementState.PUBLISHED if pa<=now else AnnouncementState.SCHEDULED
  x=Announcement(f'an_{uuid.uuid4().hex}',i,offering_id,title.strip(),body.strip(),audience,state,pa,now if state==AnnouncementState.PUBLISHED else None,a,1,now,now);self.repo.save_announcement(x);self._audit(a,'announcement.created','announcement',x.id,{'audience':audience,'state':state.value});
  if state==AnnouncementState.PUBLISHED:
   for target in self._announcement_targets(i,x):self._notify(target,title.strip(),body.strip(),f'announcement:{x.id}',f'/campus/announcements/{x.id}')
  return x
 def retract_announcement(self,a,i,id,reason,expected_version):
  x=self.repo.announcement(i,id)
  if not x or x.row_version!=expected_version or x.state not in {AnnouncementState.PUBLISHED,AnnouncementState.SCHEDULED} or not reason.strip():raise ValueError('announcement_retract_invalid')
  self._staff(a,i,x.offering_id) if x.offering_id else self._member(a,i)
  y=replace(x,state=AnnouncementState.RETRACTED,row_version=x.row_version+1,updated_at=self.now());self.repo.save_announcement(y,x.row_version);self._audit(a,'announcement.retracted','announcement',id,{'reason':reason});return y
 def announcements(self,a,i):
  m=self._member(a,i);items=self.repo.announcements(i);now=self.now();result=[]
  for x in items:
   if x.state==AnnouncementState.SCHEDULED and x.publish_at<=now:
    x=replace(x,state=AnnouncementState.PUBLISHED,published_at=now,row_version=x.row_version+1,updated_at=now);self.repo.save_announcement(x,x.row_version-1)
    for target in self._announcement_targets(i,x):self._notify(target,x.title,x.body,f'announcement:{x.id}',f'/campus/announcements/{x.id}')
   if x.state!=AnnouncementState.PUBLISHED:continue
   if x.audience=='students' and m.role!=CampusRole.STUDENT:continue
   if x.audience=='teachers' and m.role!=CampusRole.TEACHER:continue
   if x.offering_id:
    off=self.teaching.offering(i,x.offering_id)
    if m.role==CampusRole.STUDENT and (not off or not any(e.active and e.student_account_id==a for e in self.campus.enrollments_for_cohort(off.cohort_id))):continue
    if m.role==CampusRole.TEACHER and not self.teaching.assignment(x.offering_id,a):continue
   result.append(x)
  return tuple(result)
 def submit_absence(self,a,i,sid,reason,evidence_uri=None):
  m=self._member(a,i)
  if m.role!=CampusRole.STUDENT or not reason.strip():raise ValueError('absence_request_invalid')
  sess=self.repo.attendance_session(i,sid)
  if not sess:raise ValueError('attendance_session_not_found')
  off=self.teaching.offering(i,sess.offering_id)
  if not off or not any(e.active and e.student_account_id==a for e in self.campus.enrollments_for_cohort(off.cohort_id)):raise PermissionError('attendance_enrollment_required')
  if self.delivery:self.delivery.assert_student_eligible(a,i,x.offering_id)
  if self.repo.absence_for_student_session(sid,a):raise ValueError('absence_request_exists')
  now=self.now();x=AbsenceRequest(f'abs_{uuid.uuid4().hex}',i,sid,a,reason.strip(),evidence_uri,AbsenceRequestState.PENDING,None,None,1,now,now);self.repo.save_absence(x);self._audit(a,'absence.submitted','absence_request',x.id);return x
 def decide_absence(self,a,i,id,decision,reason,expected_version):
  x=self.repo.absence_request(i,id)
  if not x or x.row_version!=expected_version or x.state!=AbsenceRequestState.PENDING or decision not in {'approved','rejected'} or not reason.strip():raise ValueError('absence_decision_invalid')
  sess=self.repo.attendance_session(i,x.attendance_session_id);self._staff(a,i,sess.offering_id)
  now=self.now();y=replace(x,state=AbsenceRequestState(decision),decision_reason=reason.strip(),decided_by=a,row_version=x.row_version+1,updated_at=now);self.repo.save_absence(y,x.row_version)
  if decision=='approved':
   r=self.repo.record(x.attendance_session_id,x.student_account_id)
   if r:
    z=replace(r,status=AttendanceStatus.JUSTIFIED,review=AttendanceReview.CONFIRMED,evidence=(r.evidence+';absence_approved:'+id).strip(';'),row_version=r.row_version+1,updated_at=now);self.repo.save_record(z,r.row_version)
  self._audit(a,'absence.decided','absence_request',id,{'decision':decision,'reason':reason});self._notify(x.student_account_id,'Justificatif d’absence',f'Décision : {decision}. {reason}',f'absence:{id}:{decision}',f'/campus/absences/{id}');return y
 def absence_requests(self,a,i):
  m=self._member(a,i);xs=self.repo.absences(i)
  return tuple(x for x in xs if m.role!=CampusRole.STUDENT or x.student_account_id==a)
 def create_event(self,a,i,kind,title,starts_at,ends_at,details='',location=None,offering_id=None,cohort_id=None,source_ref=None):
  m=self._member(a,i)
  if m.role not in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.TEACHER}:raise PermissionError('calendar_staff_required')
  if offering_id:self._staff(a,i,offering_id)
  if ends_at<=starts_at or not title.strip():raise ValueError('calendar_event_invalid')
  now=self.now();x=CalendarEvent(f'cev_{uuid.uuid4().hex}',i,offering_id,cohort_id,CalendarEventKind(kind),title.strip(),details.strip(),starts_at,ends_at,location,CalendarEventState.SCHEDULED,source_ref,1,a,now,now);self.repo.save_event(x);self._audit(a,'calendar.created','calendar_event',x.id,{'kind':kind});
  if cohort_id:
   for e in self.campus.enrollments_for_cohort(cohort_id):
    if e.active:self._notify(e.student_account_id,title.strip(),details.strip() or title.strip(),f'calendar:{x.id}',f'/campus/calendar/{x.id}')
  return x
 def update_event_state(self,a,i,id,state,reason,expected_version):
  x=self.repo.event(i,id)
  if not x or x.row_version!=expected_version or state not in {'cancelled','completed'} or not reason.strip():raise ValueError('calendar_transition_invalid')
  if x.offering_id:self._staff(a,i,x.offering_id)
  else:
   m=self._member(a,i)
   if m.role not in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}:raise PermissionError('calendar_admin_required')
  y=replace(x,state=CalendarEventState(state),row_version=x.row_version+1,updated_at=self.now());self.repo.save_event(y,x.row_version);self._audit(a,'calendar.state_changed','calendar_event',id,{'state':state,'reason':reason});return y
 def calendar(self,a,i):
  m=self._member(a,i);xs=self.repo.events(i)
  if m.role!=CampusRole.STUDENT:return xs
  cohorts={e.cohort_id for e in self.campus.enrollments_for_student(i,a) if e.active};return tuple(x for x in xs if x.cohort_id is None or x.cohort_id in cohorts)
 def operations_dashboard(self,a,i):
  m=self._member(a,i)
  if m.role not in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.FACULTY_ADMIN,CampusRole.TEACHER}:raise PermissionError('operations_staff_required')
  events=self.repo.events(i);absences=self.repo.absences(i);anns=self.repo.announcements(i)
  sessions=[]
  for off in self.teaching.list_offerings(i):
   sessions.extend(self.teaching.list_sessions(off.id))
  att=[]
  for ts in sessions:
   s=self.repo.attendance_for_teaching_session(i,ts.id)
   if s:att.extend(self.repo.records(s.id))
  total=len(att);return {'institution_id':i,'teaching_sessions':len(sessions),'attendance_records':total,'present':sum(r.status==AttendanceStatus.PRESENT for r in att),'late':sum(r.status==AttendanceStatus.LATE for r in att),'justified':sum(r.status==AttendanceStatus.JUSTIFIED for r in att),'needs_review':sum(r.review==AttendanceReview.NEEDS_REVIEW for r in att),'absence_requests_pending':sum(x.state==AbsenceRequestState.PENDING for x in absences),'announcements_active':sum(x.state in {AnnouncementState.PUBLISHED,AnnouncementState.SCHEDULED} for x in anns),'calendar_upcoming':sum(x.state==CalendarEventState.SCHEDULED and x.ends_at>=self.now() for x in events)}

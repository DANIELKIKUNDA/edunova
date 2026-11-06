from dataclasses import replace
import json
from uuid import uuid4
from app.modules.student_records.domain.model import *
from app.modules.admissions_center.domain.model import ReviewState
from app.modules.campus.domain.model import CampusRole,Membership,MembershipState
WRITE={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}
class StudentRecordService:
 def __init__(self,repo,campus,campus_repo,admissions,apps,catalog,academic_repo,now,audit=None):self.repo=repo;self.campus=campus;self.campus_repo=campus_repo;self.admissions=admissions;self.apps=apps;self.catalog=catalog;self.academic_repo=academic_repo;self.now=now;self.audit=audit
 def _auth(self,a,i):return self.campus.membership(a,i,WRITE)
 def _event(self,a,s,event,old=None,note=None):self.repo.event(StudentEvent(uuid4().hex,s.id,a,event,old.value if hasattr(old,'value') else old,s.state.value,note,self.now()))
 def _audit(self,a,action,s,meta=None):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type='student_record',entity_id=s.id,metadata=meta or {})
 def matriculate(self,a,i,review_id,cohort_id):
  self._auth(a,i);r=self.admissions.repo.get(review_id)
  if not r or r.institution_id!=i or r.state!=ReviewState.ADMITTED:raise ValueError('student_admitted_review_required')
  old=self.repo.by_admission(review_id)
  if old:return old
  app=self.apps.get(r.application_id);campaign=self.catalog.campaign_any(app.campaign_id);co=self.campus_repo.cohort(i,cohort_id)
  if not campaign or not co or not co.active:raise ValueError('student_valid_campaign_cohort_required')
  if co.program_unit_id!=campaign.program_unit_id or co.academic_period_id!=campaign.academic_year_id:raise ValueError('student_cohort_campaign_mismatch')
  binding=self.academic_repo.binding_for_cohort(i,cohort_id)
  if not binding or binding.curriculum_id!=campaign.curriculum_id:raise ValueError('student_cohort_curriculum_mismatch')
  existing=self.repo.by_account(i,app.account_id)
  if existing:raise ValueError('student_record_already_exists')
  inst=self.campus_repo.institution(i);year=self.campus_repo.period(i,campaign.academic_year_id);prefix=f'{inst.slug[:8].upper()}-{year.starts_on.year}'
  matricule=self.repo.next_matricule(i,campaign.academic_year_id,prefix);n=self.now();s=StudentRecord(uuid4().hex,i,app.account_id,matricule,review_id,app.id,campaign.program_unit_id,campaign.curriculum_id,cohort_id,app.given_names,app.family_name,app.birth_date,app.nationality_code,app.email,app.phone_number,StudentState.ACTIVE,1,n,n);self.repo.save(s)
  m=self.campus_repo.membership(i,app.account_id)
  if m and m.state==MembershipState.ACTIVE and m.role!=CampusRole.STUDENT:raise ValueError('student_account_has_incompatible_campus_role')
  if not m:
   m=Membership(uuid4().hex,i,app.account_id,CampusRole.STUDENT,MembershipState.ACTIVE,campaign.program_unit_id,a,n,1,n,n);self.campus_repo.save_membership(m)
  elif m.state!=MembershipState.ACTIVE:
   m=replace(m,role=CampusRole.STUDENT,state=MembershipState.ACTIVE,unit_id=campaign.program_unit_id,joined_at=n,row_version=m.row_version+1,updated_at=n);self.campus_repo.save_membership(m,m.row_version-1)
  self.campus.enroll(a,i,cohort_id=cohort_id,student_account_id=app.account_id)
  reg=AcademicRegistration(uuid4().hex,s.id,i,campaign.academic_year_id,cohort_id,campaign.curriculum_id,RegistrationState.ENROLLED,a,n,1);self.repo.save_registration(reg);self._snapshot_courses(s,reg);self._event(a,s,'matriculated');self._audit(a,'student.matriculated',s,{'matricule':matricule,'cohort_id':cohort_id});return s
 def dossier(self,a,i,sid):
  m=self.campus.membership(a,i);s=self.repo.get(sid)
  if not s or s.institution_id!=i:raise ValueError('student_record_not_found')
  if m.role==CampusRole.STUDENT and s.account_id!=a:raise PermissionError('student_record_forbidden')
  return {'student':s,'registrations':self.repo.registrations(sid),'courses':self.repo.course_registrations(sid),'events':self.repo.events(sid),'administrative_history':self.repo.administrative_history(sid)}
 def my_dossier(self,a,i):
  self.campus.membership(a,i);s=self.repo.by_account(i,a)
  if not s:raise ValueError('student_record_not_found')
  return self.dossier(a,i,s.id)
 def change_state(self,a,i,sid,expected,state,note=None):
  self._auth(a,i);s=self.repo.get(sid)
  if not s or s.institution_id!=i:raise ValueError('student_record_not_found')
  if s.row_version!=expected:raise ValueError('student_record_concurrent_modification')
  target=StudentState(state);allowed={StudentState.ACTIVE:{StudentState.SUSPENDED,StudentState.WITHDRAWN,StudentState.GRADUATED},StudentState.SUSPENDED:{StudentState.ACTIVE,StudentState.WITHDRAWN},StudentState.WITHDRAWN:{StudentState.ARCHIVED},StudentState.GRADUATED:{StudentState.ARCHIVED},StudentState.ARCHIVED:set()}
  if target not in allowed[s.state]:raise ValueError('student_invalid_state_transition')
  n=self.now();y=replace(s,state=target,row_version=s.row_version+1,updated_at=n);self.repo.save(y,s.row_version);self._event(a,y,'state_changed',s.state,note);self._audit(a,'student.state_changed',y,{'from':s.state.value,'to':target.value});return y

 def _snapshot_courses(self,s,reg):
  courses=self.academic_repo.courses(reg.curriculum_id);rows=[StudentCourseRegistration(uuid4().hex,reg.id,s.id,c.id,c.semester,c.code,c.title,c.credits,CourseRegistrationState.ENROLLED,self.now()) for c in courses];self.repo.save_course_registrations(rows);return rows
 def register_academic_year(self,a,i,sid,cohort_id):
  self._auth(a,i);s=self.repo.get(sid)
  if not s or s.institution_id!=i or s.state!=StudentState.ACTIVE:raise ValueError('student_active_record_required')
  co=self.campus_repo.cohort(i,cohort_id)
  if not co or not co.active or co.program_unit_id!=s.program_unit_id:raise ValueError('student_compatible_cohort_required')
  binding=self.academic_repo.binding_for_cohort(i,cohort_id)
  if not binding:raise ValueError('student_cohort_curriculum_required')
  old=self.repo.registration(sid,co.academic_period_id)
  if old:return old
  regs=self.repo.registrations(sid)
  if regs and regs[-1].state not in {RegistrationState.COMPLETED,RegistrationState.WITHDRAWN}:raise ValueError('student_previous_registration_must_be_closed')
  if regs:
   previous=self.campus_repo.period(i,regs[-1].academic_year_id)
   current=self.campus_repo.period(i,co.academic_period_id)
   if previous and current and current.starts_on<=previous.starts_on:raise ValueError('student_academic_year_must_progress')
  n=self.now();reg=AcademicRegistration(uuid4().hex,sid,i,co.academic_period_id,cohort_id,binding.curriculum_id,RegistrationState.ENROLLED,a,n,1);self.repo.save_registration(reg);self._snapshot_courses(s,reg)
  y=replace(s,cohort_id=cohort_id,curriculum_id=binding.curriculum_id,row_version=s.row_version+1,updated_at=n);self.repo.save(y,s.row_version);self.campus.enroll(a,i,cohort_id=cohort_id,student_account_id=s.account_id);self._event(a,y,'academic_year_registered',s.state,cohort_id);self._audit(a,'student.academic_year_registered',y,{'cohort_id':cohort_id,'academic_year_id':co.academic_period_id});return reg

 def _history(self,a,s,action,reason,before=None,after=None):
  if not reason or len(reason.strip())<3:raise ValueError('student_administrative_reason_required')
  h=StudentAdministrativeHistory(uuid4().hex,s.id,s.institution_id,a,action,reason.strip(),json.dumps(before,sort_keys=True,default=str) if before is not None else None,json.dumps(after,sort_keys=True,default=str) if after is not None else None,self.now());self.repo.add_administrative_history(h);return h
 def correct_identity(self,a,i,sid,expected,reason,**changes):
  self._auth(a,i);s=self.repo.get(sid)
  if not s or s.institution_id!=i:raise ValueError('student_record_not_found')
  if s.row_version!=expected:raise ValueError('student_record_concurrent_modification')
  allowed={'given_names','family_name','birth_date','nationality_code','email','phone_number'};changes={k:v for k,v in changes.items() if k in allowed and v is not None and v!=getattr(s,k)}
  if not changes:raise ValueError('student_identity_no_change')
  before={k:getattr(s,k) for k in changes};n=self.now();y=replace(s,**changes,row_version=s.row_version+1,updated_at=n);self.repo.save(y,s.row_version);self._history(a,y,'identity_correction',reason,before,changes);self._event(a,y,'identity_corrected',s.state,reason);self._audit(a,'student.identity_corrected',y,{'fields':sorted(changes)});return y
 def change_registration_state(self,a,i,sid,registration_id,expected,state,reason):
  if not reason or len(reason.strip())<3:raise ValueError('student_administrative_reason_required')
  self._auth(a,i);s=self.repo.get(sid)
  if not s or s.institution_id!=i:raise ValueError('student_record_not_found')
  reg=next((x for x in self.repo.registrations(sid) if x.id==registration_id),None)
  if not reg or reg.institution_id!=i:raise ValueError('student_registration_not_found')
  if reg.row_version!=expected:raise ValueError('student_registration_concurrent_modification')
  target=RegistrationState(state);allowed={RegistrationState.ENROLLED:{RegistrationState.SUSPENDED,RegistrationState.WITHDRAWN,RegistrationState.COMPLETED,RegistrationState.CANCELLED},RegistrationState.SUSPENDED:{RegistrationState.ENROLLED,RegistrationState.WITHDRAWN,RegistrationState.CANCELLED},RegistrationState.WITHDRAWN:set(),RegistrationState.COMPLETED:set(),RegistrationState.CANCELLED:set()}
  if target not in allowed[reg.state]:raise ValueError('student_invalid_registration_transition')
  y=replace(reg,state=target,row_version=reg.row_version+1);self.repo.save_registration(y,reg.row_version);self._history(a,s,'registration_state_changed',reason,{'registration_id':reg.id,'state':reg.state.value},{'registration_id':reg.id,'state':target.value});self._event(a,s,'registration_state_changed',s.state,f'{reg.state.value}->{target.value}: {reason}');self._audit(a,'student.registration_state_changed',s,{'registration_id':reg.id,'from':reg.state.value,'to':target.value});return y

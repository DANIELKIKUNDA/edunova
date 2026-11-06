from dataclasses import replace
from uuid import uuid4
from hashlib import sha256
from datetime import date
import json
from app.modules.student_success.domain.model import SuccessCase,SuccessEvent,SuccessPlan,SuccessAction,SuccessAssessment
from app.modules.campus.domain.model import CampusRole,MembershipState

STAFF={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.TEACHER}
CATEGORIES={'academic','attendance','engagement','wellbeing','other'}
SEVERITIES={'low','medium','high'}
TRANSITIONS={'open':{'in_progress','closed'},'in_progress':{'resolved','closed'},'resolved':{'closed','in_progress'},'closed':set()}
class StudentSuccessService:
 def __init__(self,repo,campus,student_repo,now):self.repo=repo;self.campus=campus;self.students=student_repo;self.now=now
 def _member(self,a,i):
  m=self.campus.membership(i,a)
  if not m or m.state!=MembershipState.ACTIVE:raise PermissionError('success_membership_required')
  return m
 def _staff(self,a,i):
  m=self._member(a,i)
  if m.role not in STAFF:raise PermissionError('success_staff_required')
  return m
 def _student(self,i,sid):
  x=self.students.get(sid)
  if not x or x.institution_id!=i:raise ValueError('success_student_not_found')
  return x
 def create(self,a,i,sid,category,severity,description):
  self._staff(a,i);self._student(i,sid)
  if category not in CATEGORIES or severity not in SEVERITIES:raise ValueError('success_invalid_category_or_severity')
  if not 10<=len(description.strip())<=2000:raise ValueError('success_description_length')
  n=self.now();c=SuccessCase(uuid4().hex,i,sid,category,severity,description.strip(),'open',None,a,n,n,1)
  self.repo.save_with_event(c,SuccessEvent(uuid4().hex,c.id,a,'created','',n));return c
 def get(self,a,i,cid):
  m=self._member(a,i);c=self.repo.get(cid)
  if not c or c.institution_id!=i:raise ValueError('success_case_not_found')
  if m.role not in STAFF and self._student(i,c.student_id).account_id!=a:raise PermissionError('success_case_forbidden')
  return c
 def list(self,a,i,sid=None):
  m=self._member(a,i)
  if m.role not in STAFF:
   own=self.students.by_account(i,a)
   if not own:raise PermissionError('success_case_forbidden')
   if sid and sid!=own.id:raise PermissionError('success_case_forbidden')
   sid=own.id
  elif sid:self._student(i,sid)
  return self.repo.list(i,sid)
 def transition(self,a,i,cid,state,expected_version,note,assigned_to=None):
  self._staff(a,i);c=self.get(a,i,cid)
  if c.version!=expected_version:raise ValueError('success_case_concurrent_modification')
  if state not in TRANSITIONS[c.state]:raise ValueError('success_invalid_transition')
  if state=='closed' and self.repo.active_plan(cid):raise ValueError('success_active_plan_blocks_case_closure')
  if not 5<=len(note.strip())<=2000:raise ValueError('success_note_required')
  if assigned_to is not None:self._staff(assigned_to,i)
  n=self.now();new=replace(c,state=state,assigned_to=assigned_to if assigned_to is not None else c.assigned_to,version=c.version+1,updated_at=n)
  self.repo.save_with_event(new,SuccessEvent(uuid4().hex,c.id,a,state,note.strip(),n),expected_version);return new
 def timeline(self,a,i,cid):
  self.get(a,i,cid);return self.repo.events(cid)
 def scan(self,a,i,sid):
  self._staff(a,i);stu=self._student(i,sid)
  results,attendance=self.repo.evidence(i,sid,stu.account_id)
  failed=[r for r in results if not r.passed]
  total=len(attendance);present=sum(r.status in ('present','late') for r in attendance);rate=round(present/total*100,2) if total else None
  rules=[]
  if len(failed)>=2:rules.append(('academic','high','published_failures',f'{len(failed)} published course results are failed.',[r.evidence_hash for r in failed]))
  elif len(failed)==1:rules.append(('academic','medium','published_failures','1 published course result is failed.',[failed[0].evidence_hash]))
  if total>=3 and rate<75:rules.append(('attendance','high' if rate<60 else 'medium','attendance_rate',f'Attendance rate is {rate}% across {total} closed-session records.',[f'{r.attendance_session_id}:{r.status}' for r in attendance]))
  created=[];existing=[]
  for category,severity,kind,desc,evidence in rules:
   payload=json.dumps(sorted(evidence),separators=(',',':'));digest=sha256(payload.encode()).hexdigest();key=f'{sid}:{kind}:{digest}'
   old=self.repo.by_source(i,key)
   if old:existing.append(old);continue
   n=self.now();c=SuccessCase(uuid4().hex,i,sid,category,severity,desc,'open',None,a,n,n,1,'deterministic_rule',key,digest)
   self.repo.save_with_event(c,SuccessEvent(uuid4().hex,c.id,a,'auto_detected',f'Deterministic rule {kind}; no predictive model or diagnosis.',n));created.append(c)
  return {'student_id':sid,'published_results':len(results),'failed_results':len(failed),'attendance_records':total,'attendance_rate':rate,'created':tuple(created),'existing':tuple(existing),'method':'deterministic_rules_v1','predictive_model':False}
 def create_plan(self,a,i,cid,objective,target_date=None):
  self._staff(a,i);c=self.get(a,i,cid)
  if c.state=='closed':raise ValueError('success_closed_case_plan_forbidden')
  if self.repo.active_plan(cid):raise ValueError('success_active_plan_exists')
  if not 10<=len(objective.strip())<=2000:raise ValueError('success_objective_length')
  if target_date:
   try: date.fromisoformat(target_date)
   except ValueError: raise ValueError('success_invalid_target_date')
  n=self.now();p=SuccessPlan(uuid4().hex,cid,i,c.student_id,objective.strip(),'active',target_date,a,n,n,1)
  self.repo.save_plan_with_event(p,SuccessEvent(uuid4().hex,cid,a,'plan_created',objective.strip(),n));return p
 def get_plan(self,a,i,cid):
  self.get(a,i,cid);p=self.repo.active_plan(cid)
  if not p:raise ValueError('success_active_plan_not_found')
  return p
 def add_action(self,a,i,cid,title,assigned_to,due_date=None):
  self._staff(a,i);p=self.get_plan(a,i,cid);self._staff(assigned_to,i)
  if not 5<=len(title.strip())<=500:raise ValueError('success_action_title_length')
  if due_date:
   try: date.fromisoformat(due_date)
   except ValueError: raise ValueError('success_invalid_due_date')
  n=self.now();x=SuccessAction(uuid4().hex,p.id,title.strip(),assigned_to,due_date,'pending',None,n,None,1)
  self.repo.add_action_with_event(x,SuccessEvent(uuid4().hex,cid,a,'action_added',title.strip(),n));return x
 def list_actions(self,a,i,cid):
  p=self.get_plan(a,i,cid);return self.repo.actions(p.id)
 def complete_action(self,a,i,cid,aid,expected_version,note):
  self._staff(a,i);p=self.get_plan(a,i,cid);x=self.repo.get_action(aid)
  if not x or x.plan_id!=p.id:raise ValueError('success_action_not_found')
  if x.version!=expected_version:raise ValueError('success_action_concurrent_modification')
  if x.state!='pending':raise ValueError('success_action_not_pending')
  if a!=x.assigned_to and self._member(a,i).role not in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}:raise PermissionError('success_action_completion_forbidden')
  if not 5<=len(note.strip())<=2000:raise ValueError('success_note_required')
  n=self.now();new=replace(x,state='completed',completion_note=note.strip(),completed_at=n,version=x.version+1)
  self.repo.save_action_with_event(new,SuccessEvent(uuid4().hex,cid,a,'action_completed',note.strip(),n),expected_version);return new

 def reassess_plan(self,a,i,cid):
  self._staff(a,i);p=self.get_plan(a,i,cid);stu=self._student(i,p.student_id)
  results,attendance=self.repo.evidence(i,p.student_id,stu.account_id)
  failed=sum(not r.passed for r in results);total=len(attendance);present=sum(r.status in ('present','late') for r in attendance);rate=round(present/total*100,2) if total else None
  evidence=[getattr(r,'evidence_hash','') for r in results]+[f'{r.attendance_session_id}:{r.status}' for r in attendance]
  digest=sha256(json.dumps(sorted(evidence),separators=(',',':')).encode()).hexdigest()
  previous=self.repo.assessments(p.id);outcome='baseline'
  if previous:
   prev=previous[-1]
   if not results and total<3:outcome='insufficient'
   else:
    comparable_results=bool(results) and prev.published_results>0
    comparable_attendance=total>=3 and prev.attendance_records>=3
    if not comparable_results and not comparable_attendance:outcome='insufficient'
    better=(comparable_results and failed<prev.failed_results) or (comparable_attendance and rate>=prev.attendance_rate+5)
    worse=(comparable_results and failed>prev.failed_results) or (comparable_attendance and rate<=prev.attendance_rate-5)
    outcome='improved' if better and not worse else 'worsened' if worse and not better else 'stable'
  elif not results and total<3:outcome='insufficient'
  n=self.now();x=SuccessAssessment(uuid4().hex,p.id,cid,i,p.student_id,failed,len(results),total,rate,outcome,digest,a,n)
  self.repo.add_assessment_with_event(x,SuccessEvent(uuid4().hex,cid,a,'plan_reassessed',f'Outcome {outcome}; deterministic evidence comparison.',n));return x
 def assessments(self,a,i,cid):
  p=self.get_plan(a,i,cid);return self.repo.assessments(p.id)
 def dashboard(self,a,i):
  self._staff(a,i);return self.repo.dashboard(i,date.today().isoformat())
 def close_plan(self,a,i,cid,expected_version,note):
  self._staff(a,i);p=self.get_plan(a,i,cid)
  if p.version!=expected_version:raise ValueError('success_plan_concurrent_modification')
  if any(x.state=='pending' for x in self.repo.actions(p.id)):raise ValueError('success_plan_pending_actions')
  if not 5<=len(note.strip())<=2000:raise ValueError('success_note_required')
  n=self.now();new=replace(p,state='completed',updated_at=n,version=p.version+1)
  self.repo.save_plan_with_event(new,SuccessEvent(uuid4().hex,cid,a,'plan_completed',note.strip(),n),expected_version);return new


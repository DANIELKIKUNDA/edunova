from dataclasses import replace
from uuid import uuid4
from app.modules.gradebook.domain.model import *
from app.modules.campus.domain.model import CampusRole,MembershipState
class GradebookService:
 def __init__(self,repo,campus,teaching,assignments,now,audit=None,delivery=None):self.repo=repo;self.campus=campus;self.teaching=teaching;self.assignments=assignments;self.now=now;self.audit=audit;self.delivery=delivery
 def _audit(self,a,act,t,id,meta=None):
  if self.audit:self.audit.record(actor_id=a,action=act,target_type=t,target_id=id,metadata=meta or {})
 def _member(self,a,i):
  m=self.campus.membership(i,a)
  if not m or m.state!=MembershipState.ACTIVE:raise PermissionError('gradebook_active_membership_required')
  return m
 def _staff(self,a,i,o):
  m=self._member(a,i)
  if m.role in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}:return
  ta=self.teaching.assignment(o,a)
  if m.role==CampusRole.TEACHER and ta and ta.active:return
  raise PermissionError('gradebook_staff_required')
 def _student(self,a,i,o):
  self._member(a,i);off=self.teaching.offering(i,o)
  if not off:raise ValueError('offering_not_found')
  if self.delivery:
   self.delivery.assert_student_eligible(a,i,o);return
  if not any(e.active and e.cohort_id==off.cohort_id for e in self.campus.enrollments_for_student(i,a)):raise PermissionError('gradebook_student_enrollment_required')
 def create(self,a,i,o,*,title='Résultats académiques',pass_percent=50):
  self._staff(a,i,o)
  if not self.teaching.offering(i,o):raise ValueError('offering_not_found')
  if self.repo.for_offering(i,o):raise ValueError('gradebook_already_exists')
  if not 0<=pass_percent<=100:raise ValueError('gradebook_invalid_pass_percent')
  n=self.now();x=Gradebook(uuid4().hex,i,o,title.strip() or 'Résultats académiques',GradebookState.DRAFT,float(pass_percent),1,a,n,n);self.repo.save_gradebook(x);self._audit(a,'gradebook.created','gradebook',x.id);return x
 def add_component(self,a,i,gid,*,title,kind,weight_percent,max_score,source_assignment_id=None):
  g=self.repo.gradebook(i,gid)
  if not g:raise ValueError('gradebook_not_found')
  self._staff(a,i,g.offering_id)
  if g.state!=GradebookState.DRAFT:raise ValueError('gradebook_structure_locked')
  if weight_percent<=0 or max_score<=0:raise ValueError('gradebook_invalid_component')
  comps=self.repo.components(g.id)
  if sum(c.weight_percent for c in comps)+weight_percent>100.0001:raise ValueError('gradebook_weight_overflow')
  if source_assignment_id:
   ass=self.assignments.assignment(i,source_assignment_id)
   if not ass or ass.offering_id!=g.offering_id:raise ValueError('gradebook_assignment_source_mismatch')
  c=GradeComponent(uuid4().hex,i,g.id,title.strip(),ComponentKind(kind),float(weight_percent),float(max_score),source_assignment_id,len(comps)+1,self.now());self.repo.save_component(c);return c
 def open(self,a,i,gid,expected_version):
  g=self.repo.gradebook(i,gid)
  if not g:raise ValueError('gradebook_not_found')
  self._staff(a,i,g.offering_id)
  if g.row_version!=expected_version:raise ValueError('gradebook_concurrent_modification')
  if g.state!=GradebookState.DRAFT:raise ValueError('gradebook_invalid_transition')
  if abs(sum(c.weight_percent for c in self.repo.components(g.id))-100)>1e-6:raise ValueError('gradebook_weights_must_total_100')
  y=replace(g,state=GradebookState.OPEN,row_version=g.row_version+1,updated_at=self.now());self.repo.save_gradebook(y,g.row_version);return y
 def set_mark(self,a,i,gid,cid,student,*,score=None,validate=True,expected_version=None,source_ref=None,attendance='present',note=None):
  g=self.repo.gradebook(i,gid);c=self.repo.component(i,cid)
  if not g or not c or c.gradebook_id!=gid:raise ValueError('gradebook_component_not_found')
  self._staff(a,i,g.offering_id);self._student(student,i,g.offering_id)
  if g.state not in {GradebookState.OPEN,GradebookState.LOCKED}:raise ValueError('gradebook_not_open')
  if g.state==GradebookState.LOCKED:raise ValueError('gradebook_locked')
  attendance=AttendanceOutcome(attendance)
  if attendance==AttendanceOutcome.PRESENT:
   if score is None or not 0<=score<=c.max_score:raise ValueError('gradebook_invalid_score')
  elif score is not None:raise ValueError('gradebook_nonpresent_score_forbidden')
  if attendance in {AttendanceOutcome.JUSTIFIED_ABSENCE,AttendanceOutcome.EXEMPT} and not (note or '').strip():raise ValueError('gradebook_nonpresent_reason_required')
  old=self.repo.mark(i,cid,student);n=self.now();x=StudentMark(old.id if old else uuid4().hex,i,g.id,c.id,student,float(score) if score is not None else None,MarkState.VALIDATED if validate else MarkState.DRAFT,source_ref,a if validate else None,(old.row_version+1 if old else 1),old.created_at if old else n,n,attendance,(note or '').strip() or None);self.repo.save_mark(x,expected_version if old else None);self._audit(a,'gradebook.mark.set','student_mark',x.id,{'validated':validate});return x
 def import_assignment_results(self,a,i,gid,cid):
  g=self.repo.gradebook(i,gid);c=self.repo.component(i,cid)
  if not g or not c or c.gradebook_id!=gid or not c.source_assignment_id:raise ValueError('gradebook_assignment_component_required')
  self._staff(a,i,g.offering_id);ass=self.assignments.assignment(i,c.source_assignment_id)
  if not ass or ass.state.value!='results_published':raise ValueError('gradebook_assignment_results_not_published')
  count=0
  for sub in self.assignments.submissions(ass.id):
   grade=self.assignments.grade_for_submission(sub.id)
   if not grade or grade.final_score is None:continue
   scaled=float(grade.final_score)/ass.max_score*c.max_score
   self.set_mark(a,i,g.id,c.id,sub.student_account_id,score=scaled,source_ref=f'assignment:{ass.id}:{sub.id}');count+=1
  return count
 def result(self,a,i,gid,student=None):
  g=self.repo.gradebook(i,gid)
  if not g:raise ValueError('gradebook_not_found')
  stu=student or a
  if student:self._staff(a,i,g.offering_id)
  else:self._student(a,i,g.offering_id)
  if not student and g.state!=GradebookState.PUBLISHED:raise PermissionError('gradebook_results_not_published')
  comps=self.repo.components(g.id);marks={m.component_id:m for m in self.repo.marks(g.id,stu) if m.state==MarkState.VALIDATED};parts=[];total=0.;complete=True
  for c in comps:
   m=marks.get(c.id)
   if not m:complete=False;parts.append(f'{c.title}:pending');continue
   if m.attendance in {AttendanceOutcome.JUSTIFIED_ABSENCE,AttendanceOutcome.EXEMPT}:complete=False;parts.append(f'{c.title}:{m.attendance.value}');continue
   score=0.0 if m.attendance==AttendanceOutcome.ABSENT else m.score
   if score is None:complete=False;parts.append(f'{c.title}:pending');continue
   pct=score/c.max_score*100;total+=pct*c.weight_percent/100;parts.append(f'{c.title}:{score}/{c.max_score}')
  return AcademicResult(g.id,stu,round(total,2),bool(complete and total>=g.pass_percent),complete,tuple(parts),g.state==GradebookState.PUBLISHED)
 def lock(self,a,i,gid,expected_version):
  g=self.repo.gradebook(i,gid)
  if not g:raise ValueError('gradebook_not_found')
  self._staff(a,i,g.offering_id)
  if g.row_version!=expected_version:raise ValueError('gradebook_concurrent_modification')
  if g.state!=GradebookState.OPEN:raise ValueError('gradebook_invalid_transition')
  y=replace(g,state=GradebookState.LOCKED,row_version=g.row_version+1,updated_at=self.now());self.repo.save_gradebook(y,g.row_version);self._audit(a,'gradebook.locked','gradebook',g.id);return y
 def unlock_exceptionally(self,a,i,gid,expected_version,reason):
  g=self.repo.gradebook(i,gid)
  if not g:raise ValueError('gradebook_not_found')
  m=self._member(a,i)
  if m.role not in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}:raise PermissionError('gradebook_academic_admin_required')
  if g.row_version!=expected_version:raise ValueError('gradebook_concurrent_modification')
  if g.state!=GradebookState.LOCKED or not reason.strip():raise ValueError('gradebook_invalid_unlock')
  y=replace(g,state=GradebookState.OPEN,row_version=g.row_version+1,updated_at=self.now());self.repo.save_gradebook(y,g.row_version);self._audit(a,'gradebook.unlocked_exceptionally','gradebook',g.id,{'reason':reason.strip()});return y
 def create_exam_session(self,a,i,gid,cid,*,kind,starts_at,ends_at,room=None,instructions=None):
  g=self.repo.gradebook(i,gid);c=self.repo.component(i,cid)
  if not g or not c or c.gradebook_id!=gid:raise ValueError('gradebook_component_not_found')
  self._staff(a,i,g.offering_id)
  if c.kind not in {ComponentKind.EXAM,ComponentKind.TEST,ComponentKind.ORAL,ComponentKind.PRACTICAL}:raise ValueError('gradebook_session_component_kind_invalid')
  if ends_at<=starts_at:raise ValueError('gradebook_session_time_invalid')
  if hasattr(self.repo,'sessions_for_gradebook'):
   for e in self.repo.sessions_for_gradebook(i,gid):
    if e.state!=ExamSessionState.CANCELLED and starts_at<e.ends_at and ends_at>e.starts_at:raise ValueError('gradebook_exam_session_overlap')
  n=self.now();x=ExamSession(uuid4().hex,i,gid,cid,ExamSessionKind(kind),ExamSessionState.SCHEDULED,starts_at,ends_at,(room or '').strip() or None,(instructions or '').strip() or None,1,a,n,n);self.repo.save_session(x);self._audit(a,'gradebook.exam_session.scheduled','exam_session',x.id);return x
 def transition_exam_session(self,a,i,sid,expected_version,target,reason=None):
  x=self.repo.session(i,sid) if hasattr(self.repo,'session') else None
  if not x:raise ValueError('gradebook_exam_session_not_found')
  g=self.repo.gradebook(i,x.gradebook_id)
  if not g:raise ValueError('gradebook_not_found')
  self._staff(a,i,g.offering_id)
  if x.row_version!=expected_version:raise ValueError('gradebook_concurrent_modification')
  target=ExamSessionState(target)
  allowed={ExamSessionState.SCHEDULED:{ExamSessionState.CLOSED,ExamSessionState.CANCELLED}}
  if target not in allowed.get(x.state,set()):raise ValueError('gradebook_exam_session_invalid_transition')
  if target==ExamSessionState.CANCELLED and not (reason or '').strip():raise ValueError('gradebook_exam_session_cancel_reason_required')
  y=replace(x,state=target,row_version=x.row_version+1,updated_at=self.now());self.repo.save_session(y,x.row_version)
  self._audit(a,'gradebook.exam_session.'+target.value,'exam_session',x.id,{'reason':(reason or '').strip()})
  return y
 def publish(self,a,i,gid,expected_version):
  g=self.repo.gradebook(i,gid)
  if not g:raise ValueError('gradebook_not_found')
  self._staff(a,i,g.offering_id)
  if g.row_version!=expected_version:raise ValueError('gradebook_concurrent_modification')
  if g.state!=GradebookState.LOCKED:raise ValueError('gradebook_deliberation_lock_required')
  off=self.teaching.offering(i,g.offering_id);students=[e.student_account_id for e in self.campus.enrollments_for_cohort(off.cohort_id) if e.active]
  if any(not self.result(a,i,g.id,s).complete for s in students):raise ValueError('gradebook_incomplete_results')
  # Preflight all canonical course registrations before changing the publication state.
  # Otherwise a late eligibility failure can leave a published gradebook with partial student updates.
  if self.delivery:
   for student in students:self.delivery.assert_student_eligible(student,i,g.offering_id)
  y=replace(g,state=GradebookState.PUBLISHED,row_version=g.row_version+1,updated_at=self.now());self.repo.save_gradebook(y,g.row_version)
  if self.delivery:
   for student in students:
    r=self.result(a,i,g.id,student);self.delivery.record_published_result(a,i,g.offering_id,student,passed=r.passed,complete=r.complete,published=True,gradebook_id=g.id,percent=r.percent,components=r.components)
  self._audit(a,'gradebook.results.published','gradebook',g.id,{'students':len(students)});return y
 def retract(self,a,i,gid,expected_version,reason):
  g=self.repo.gradebook(i,gid)
  if not g:raise ValueError('gradebook_not_found')
  m=self._member(a,i)
  if m.role not in {CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}:raise PermissionError('gradebook_academic_admin_required')
  if g.state!=GradebookState.PUBLISHED or g.row_version!=expected_version or not reason.strip():raise ValueError('gradebook_invalid_retraction')
  # Retraction must not leave canonical StudentCourseRegistration marked VALIDATED/FAILED.
  # Until a governed reversal is available, reject this unsafe operation.
  if self.delivery:raise ValueError('gradebook_canonical_result_reversal_required')
  y=replace(g,state=GradebookState.OPEN,row_version=g.row_version+1,updated_at=self.now());self.repo.save_gradebook(y,g.row_version);self._audit(a,'gradebook.results.retracted','gradebook',g.id,{'reason':reason.strip()});return y

from __future__ import annotations
from dataclasses import replace
from uuid import uuid4
from app.modules.campus.domain.model import CampusRole,MembershipState
from app.modules.teaching.domain.model import *
ADMIN={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.FACULTY_ADMIN}
class TeachingService:
 def __init__(self,repo,campus_repo,now,audit=None):self.repo=repo;self.campus_repo=campus_repo;self.now=now;self.audit=audit
 def _audit(self,a,action,t,id,meta=None):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type=t,entity_id=id,metadata=meta or {})
 def _member(self,a,i):
  m=self.campus_repo.membership(i,a)
  if not m or m.state!=MembershipState.ACTIVE:raise PermissionError('teaching_membership_required')
  return m
 def _writable(self,i):
  x=self.campus_repo.institution(i)
  if not x or x.state.value!='active':raise PermissionError('teaching_institution_not_writable')
 def _scope_offering(self,m,i,o):
  off=self.repo.offering(i,o)
  if not off:raise ValueError('teaching_offering_not_found')
  if m.role==CampusRole.FACULTY_ADMIN:
   cohort=self.campus_repo.cohort(i,off.cohort_id)
   if not cohort:raise ValueError('teaching_invalid_academic_scope')
   self.campus_repo.list_units(i) # fail early if repository contract is incomplete
   allowed=self._descendant_units(i,m.unit_id)
   if not m.unit_id or cohort.program_unit_id not in allowed:raise PermissionError('teaching_scope_forbidden')
  return off
 def _descendant_units(self,i,root):
  units=self.campus_repo.list_units(i);children={}
  for u in units:children.setdefault(u.parent_id,[]).append(u.id)
  seen={root} if root else set();stack=[root] if root else []
  while stack:
   for child in children.get(stack.pop(),[]):
    if child not in seen:seen.add(child);stack.append(child)
  return seen
 def _teacher_for(self,a,i,o):
  m=self._member(a,i);self._scope_offering(m,i,o)
  if m.role in ADMIN:return m
  ass=self.repo.assignment(o,a)
  if m.role==CampusRole.TEACHER and ass and ass.active:return m
  raise PermissionError('teaching_offering_write_forbidden')
 def create_course(self,a,i,*,code,title,description='',credits=None):
  m=self._member(a,i);self._writable(i)
  if m.role not in ADMIN:raise PermissionError('teaching_admin_required')
  if self.repo.course_by_code(i,code):raise ValueError('teaching_course_code_exists')
  n=self.now();x=Course(uuid4().hex,i,code.strip().upper(),title.strip(),description.strip(),credits,CourseState.DRAFT,1,a,n,n);self.repo.save_course(x);self._audit(a,'teaching.course.created','teaching_course',x.id);return x
 def create_offering(self,a,i,*,course_id,cohort_id,academic_period_id,label):
  m=self._member(a,i);self._writable(i)
  if m.role not in ADMIN:raise PermissionError('teaching_admin_required')
  if not self.repo.course(i,course_id):raise ValueError('teaching_course_not_found')
  c=self.campus_repo.cohort(i,cohort_id);p=self.campus_repo.period(i,academic_period_id)
  if not c or not p:raise ValueError('teaching_invalid_academic_scope')
  if m.role==CampusRole.FACULTY_ADMIN and c.program_unit_id not in self._descendant_units(i,m.unit_id):raise PermissionError('teaching_scope_forbidden')
  n=self.now();x=CourseOffering(uuid4().hex,i,course_id,cohort_id,academic_period_id,label.strip(),CourseState.DRAFT,1,n,n);self.repo.save_offering(x);self._audit(a,'teaching.offering.created','teaching_offering',x.id);return x
 def assign_teacher(self,a,i,offering_id,*,teacher_account_id,role=TeacherRole.LEAD):
  m=self._member(a,i);self._writable(i)
  if m.role not in ADMIN:raise PermissionError('teaching_admin_required')
  o=self.repo.offering(i,offering_id);tm=self.campus_repo.membership(i,teacher_account_id)
  if not o:raise ValueError('teaching_offering_not_found')
  if m.role==CampusRole.FACULTY_ADMIN:self._scope_offering(m,i,offering_id)
  if not tm or tm.state!=MembershipState.ACTIVE or tm.role!=CampusRole.TEACHER:raise ValueError('teaching_active_teacher_required')
  old=self.repo.assignment(offering_id,teacher_account_id)
  if old and old.active:return old
  x=TeacherAssignment(old.id if old else uuid4().hex,i,offering_id,teacher_account_id,role,True,old.created_at if old else self.now());self.repo.save_assignment(x);self._audit(a,'teaching.teacher.assigned','teaching_assignment',x.id);return x
 def publish_offering(self,a,i,offering_id,expected_version):
  self._teacher_for(a,i,offering_id);self._writable(i);x=self.repo.offering(i,offering_id)
  if not x:raise ValueError('teaching_offering_not_found')
  if x.row_version!=expected_version:raise ValueError('teaching_concurrent_modification')
  if not self.repo.list_assignments(offering_id):raise ValueError('teaching_teacher_required_before_publish')
  if x.state==CourseState.ARCHIVED:raise ValueError('teaching_offering_archived')
  y=replace(x,state=CourseState.PUBLISHED,row_version=x.row_version+1,updated_at=self.now());self.repo.save_offering(y,x.row_version);self._audit(a,'teaching.offering.published','teaching_offering',x.id);return y
 def add_session(self,a,i,offering_id,*,title,starts_at,ends_at):
  self._teacher_for(a,i,offering_id);self._writable(i)
  off=self.repo.offering(i,offering_id)
  if off.state!=CourseState.PUBLISHED:raise ValueError('teaching_offering_not_published')
  if starts_at>=ends_at:raise ValueError('teaching_invalid_session_time')
  n=self.now();x=TeachingSession(uuid4().hex,i,offering_id,title.strip(),starts_at,ends_at,SessionState.PLANNED,'','',1,a,n,n);self.repo.save_session(x);self._audit(a,'teaching.session.planned','teaching_session',x.id);return x
 def complete_session(self,a,i,session_id,*,summary,next_topic='',expected_version):
  x=self.repo.session(i,session_id)
  if not x:raise ValueError('teaching_session_not_found')
  self._teacher_for(a,i,x.offering_id);self._writable(i)
  if x.row_version!=expected_version:raise ValueError('teaching_concurrent_modification')
  if not summary.strip():raise ValueError('teaching_session_summary_required')
  y=replace(x,state=SessionState.COMPLETED,summary=summary.strip(),next_topic=next_topic.strip(),row_version=x.row_version+1,updated_at=self.now());self.repo.save_session(y,x.row_version);self._audit(a,'teaching.session.completed','teaching_session',x.id);return y
 def add_resource(self,a,i,offering_id,*,title,resource_type,uri,source_revision=None):
  self._teacher_for(a,i,offering_id);self._writable(i);off=self.repo.offering(i,offering_id)
  if off.state==CourseState.ARCHIVED:raise ValueError('teaching_offering_archived')
  n=self.now();x=CourseResource(uuid4().hex,i,offering_id,title.strip(),resource_type.strip(),uri.strip(),source_revision,ResourceState.DRAFT,1,a,n,n);self.repo.save_resource(x);self._audit(a,'teaching.resource.created','teaching_resource',x.id);return x
 def publish_resource(self,a,i,resource_id,expected_version):
  x=self.repo.resource(i,resource_id)
  if not x:raise ValueError('teaching_resource_not_found')
  self._teacher_for(a,i,x.offering_id);self._writable(i)
  if x.row_version!=expected_version:raise ValueError('teaching_concurrent_modification')
  y=replace(x,state=ResourceState.PUBLISHED,row_version=x.row_version+1,updated_at=self.now());self.repo.save_resource(y,x.row_version);self._audit(a,'teaching.resource.published','teaching_resource',x.id);return y

 def create_syllabus(self,a,i,offering_id,*,title,overview='',learning_outcomes=()):
  self._teacher_for(a,i,offering_id);self._writable(i)
  if not title.strip():raise ValueError('teaching_syllabus_title_required')
  versions=self.repo.list_syllabi(offering_id);v=max((x.version for x in versions),default=0)+1;n=self.now()
  x=Syllabus(uuid4().hex,i,offering_id,v,title.strip(),overview.strip(),tuple(x.strip() for x in learning_outcomes if x.strip()),SyllabusState.DRAFT,1,a,None,n,n);self.repo.save_syllabus(x);self._audit(a,'teaching.syllabus.created','teaching_syllabus',x.id,{'version':v});return x
 def add_syllabus_topic(self,a,i,syllabus_id,*,title,description='',learning_objectives=(),concept_refs=(),planned_minutes=0):
  sy=self.repo.syllabus(i,syllabus_id)
  if not sy:raise ValueError('teaching_syllabus_not_found')
  self._teacher_for(a,i,sy.offering_id);self._writable(i)
  if sy.state!=SyllabusState.DRAFT:raise ValueError('teaching_syllabus_locked')
  if not title.strip() or planned_minutes<0:raise ValueError('teaching_invalid_topic')
  topics=self.repo.list_topics(syllabus_id);x=SyllabusTopic(uuid4().hex,i,syllabus_id,len(topics)+1,title.strip(),description.strip(),tuple(z.strip() for z in learning_objectives if z.strip()),tuple(z.strip() for z in concept_refs if z.strip()),planned_minutes,TopicState.PLANNED,1,self.now());self.repo.save_topic(x);return x
 def approve_syllabus(self,a,i,syllabus_id,expected_version):
  sy=self.repo.syllabus(i,syllabus_id)
  if not sy:raise ValueError('teaching_syllabus_not_found')
  m=self._member(a,i);self._writable(i)
  if m.role not in ADMIN and not (m.role==CampusRole.TEACHER and self.repo.assignment(sy.offering_id,a) and self.repo.assignment(sy.offering_id,a).role==TeacherRole.LEAD):raise PermissionError('teaching_syllabus_approval_forbidden')
  if sy.row_version!=expected_version:raise ValueError('teaching_concurrent_modification')
  if not self.repo.list_topics(syllabus_id):raise ValueError('teaching_syllabus_topic_required')
  for previous in self.repo.list_syllabi(sy.offering_id):
   if previous.id!=sy.id and previous.state==SyllabusState.APPROVED:
    superseded=replace(previous,state=SyllabusState.SUPERSEDED,row_version=previous.row_version+1,updated_at=self.now());self.repo.save_syllabus(superseded,previous.row_version)
  y=replace(sy,state=SyllabusState.APPROVED,row_version=sy.row_version+1,approved_by=a,updated_at=self.now());self.repo.save_syllabus(y,sy.row_version);self._audit(a,'teaching.syllabus.approved','teaching_syllabus',sy.id);return y
 def update_topic_progress(self,a,i,topic_id,*,state,expected_version):
  t=self.repo.topic(i,topic_id)
  if not t:raise ValueError('teaching_topic_not_found')
  sy=self.repo.syllabus(i,t.syllabus_id);self._teacher_for(a,i,sy.offering_id);self._writable(i)
  if sy.state!=SyllabusState.APPROVED:raise ValueError('teaching_syllabus_not_approved')
  if t.row_version!=expected_version:raise ValueError('teaching_concurrent_modification')
  y=replace(t,state=TopicState(state),row_version=t.row_version+1,updated_at=self.now());self.repo.save_topic(y,t.row_version);self._audit(a,'teaching.topic.progressed','teaching_topic',t.id,{'state':y.state.value});return y
 def revise_resource(self,a,i,resource_id,*,title,uri,source_revision=None,change_note='',expected_version):
  x=self.repo.resource(i,resource_id)
  if not x:raise ValueError('teaching_resource_not_found')
  self._teacher_for(a,i,x.offering_id);self._writable(i)
  if x.row_version!=expected_version:raise ValueError('teaching_concurrent_modification')
  revs=self.repo.list_resource_revisions(resource_id);rev=ResourceRevision(uuid4().hex,i,resource_id,len(revs)+1,title.strip(),uri.strip(),source_revision,change_note.strip(),a,self.now());self.repo.save_resource_revision(rev)
  y=replace(x,title=title.strip(),uri=uri.strip(),source_revision=source_revision,state=ResourceState.DRAFT,row_version=x.row_version+1,updated_at=self.now());self.repo.save_resource(y,x.row_version);self._audit(a,'teaching.resource.revised','teaching_resource',x.id,{'revision':rev.revision_no});return y
 def teaching_progress(self,a,i,offering_id):
  if offering_id not in {o.id for o in self.my_offerings(a,i)}:raise PermissionError('teaching_offering_read_forbidden')
  approved=[x for x in self.repo.list_syllabi(offering_id) if x.state==SyllabusState.APPROVED]
  if not approved:return {'planned_topics':0,'taught_topics':0,'completion_percent':0,'syllabus_version':None}
  sy=max(approved,key=lambda x:x.version);ts=self.repo.list_topics(sy.id);done=sum(t.state==TopicState.TAUGHT for t in ts);return {'planned_topics':len(ts),'taught_topics':done,'completion_percent':round(done*100/len(ts)) if ts else 0,'syllabus_version':sy.version}
 def my_offerings(self,a,i):
  m=self._member(a,i)
  if m.role==CampusRole.STUDENT:
   cohort_ids={e.cohort_id for e in self.campus_repo.enrollments_for_student(i,a) if e.active};return tuple(o for o in self.repo.list_offerings(i) if o.cohort_id in cohort_ids and o.state==CourseState.PUBLISHED)
  if m.role==CampusRole.TEACHER:return tuple(o for o in self.repo.list_offerings(i) if self.repo.assignment(o.id,a) and self.repo.assignment(o.id,a).active)
  if m.role==CampusRole.FACULTY_ADMIN:
   allowed=self._descendant_units(i,m.unit_id);return tuple(o for o in self.repo.list_offerings(i) if (self.campus_repo.cohort(i,o.cohort_id) and self.campus_repo.cohort(i,o.cohort_id).program_unit_id in allowed))
  if m.role in ADMIN:return self.repo.list_offerings(i)
  return ()
 def deactivate_teacher(self,a,i,offering_id,teacher_account_id):
  m=self._member(a,i);self._writable(i)
  if m.role not in ADMIN:raise PermissionError('teaching_admin_required')
  self._scope_offering(m,i,offering_id);x=self.repo.assignment(offering_id,teacher_account_id)
  if not x or not x.active:raise ValueError('teaching_assignment_not_found')
  if x.role==TeacherRole.LEAD and len([z for z in self.repo.list_assignments(offering_id) if z.role==TeacherRole.LEAD])<=1 and self.repo.offering(i,offering_id).state==CourseState.PUBLISHED:raise ValueError('teaching_lead_required')
  y=replace(x,active=False);self.repo.save_assignment(y);self._audit(a,'teaching.teacher.deactivated','teaching_assignment',x.id);return y
 def cancel_session(self,a,i,session_id,expected_version):
  x=self.repo.session(i,session_id)
  if not x:raise ValueError('teaching_session_not_found')
  self._teacher_for(a,i,x.offering_id);self._writable(i)
  if x.row_version!=expected_version:raise ValueError('teaching_concurrent_modification')
  if x.state==SessionState.COMPLETED:raise ValueError('teaching_completed_session_immutable')
  y=replace(x,state=SessionState.CANCELLED,row_version=x.row_version+1,updated_at=self.now());self.repo.save_session(y,x.row_version);self._audit(a,'teaching.session.cancelled','teaching_session',x.id);return y
 def retire_resource(self,a,i,resource_id,expected_version):
  x=self.repo.resource(i,resource_id)
  if not x:raise ValueError('teaching_resource_not_found')
  self._teacher_for(a,i,x.offering_id);self._writable(i)
  if x.row_version!=expected_version:raise ValueError('teaching_concurrent_modification')
  y=replace(x,state=ResourceState.RETIRED,row_version=x.row_version+1,updated_at=self.now());self.repo.save_resource(y,x.row_version);self._audit(a,'teaching.resource.retired','teaching_resource',x.id);return y
 def offering_detail(self,a,i,offering_id):
  allowed={o.id for o in self.my_offerings(a,i)}
  if offering_id not in allowed:raise PermissionError('teaching_offering_read_forbidden')
  return {'offering':self.repo.offering(i,offering_id),'sessions':self.repo.list_sessions(offering_id),'resources':tuple(r for r in self.repo.list_resources(offering_id) if r.state==ResourceState.PUBLISHED or r.created_by==a),'teachers':self.repo.list_assignments(offering_id)}

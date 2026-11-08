from dataclasses import replace
from uuid import uuid4
from app.modules.service_desk.domain.model import *
from app.modules.campus.domain.model import CampusRole,MembershipState
STAFF={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.FACULTY_ADMIN}
TRANS={RequestState.SUBMITTED:{RequestState.IN_REVIEW,RequestState.CANCELLED},RequestState.IN_REVIEW:{RequestState.ACTION_REQUIRED,RequestState.APPROVED,RequestState.REJECTED},RequestState.ACTION_REQUIRED:{RequestState.IN_REVIEW,RequestState.CANCELLED},RequestState.APPROVED:{RequestState.FULFILLED}}
class ServiceDeskService:
 def __init__(self,repo,campus,students,now,audit=None):self.repo=repo;self.campus=campus;self.students=students;self.now=now;self.audit=audit
 def _staff(self,a,i):
  m=self.campus.membership(i,a)
  if not m or m.state!=MembershipState.ACTIVE or m.role not in STAFF:raise PermissionError('service_desk_staff_required')
 def _event_obj(self,x,a,t,n=None):return RequestEvent(uuid4().hex,x.id,a,t,n,self.now())
 def _audit(self,x,a,t):self.audit and self.audit.record(actor_id=a,action='service_desk.'+t,target_type='service_request',target_id=x.id,metadata={})
 def create(self,a,i,student_id,kind,subject,details):
  st=self.students.get(student_id)
  if not st or st.institution_id!=i or st.account_id!=a:raise PermissionError('service_request_student_scope_required')
  subject=subject.strip();details=details.strip()
  if len(subject)<3 or len(subject)>200:raise ValueError('service_request_subject_invalid')
  n=self.now();x=ServiceRequest(uuid4().hex,i,student_id,a,RequestKind(kind),subject,details,RequestState.SUBMITTED,None,None,None,None,1,n,n);e=self._event_obj(x,a,'submitted');self.repo.create_with_event(x,e);self._audit(x,a,'submitted');return x
 def get(self,a,i,rid):
  x=self.repo.get(i,rid)
  if not x:raise ValueError('service_request_not_found')
  if a!=x.requester_account_id:self._staff(a,i)
  return x
 def mine(self,a,i,student_id):
  st=self.students.get(student_id)
  if not st or st.institution_id!=i or st.account_id!=a:raise PermissionError('service_request_student_scope_required')
  return self.repo.list_student(i,student_id)
 def transition(self,a,i,rid,state,expected_version,note=''):
  x=self.get(a,i,rid);target=RequestState(state)
  if x.version!=expected_version:raise ValueError('service_request_concurrent_modification')
  if target not in TRANS.get(x.state,set()):raise ValueError('service_request_invalid_transition')
  if target==RequestState.CANCELLED:
   if a!=x.requester_account_id:raise PermissionError('service_request_student_cancel_only')
  else:self._staff(a,i)
  if target in {RequestState.ACTION_REQUIRED,RequestState.REJECTED} and not note.strip():raise ValueError('service_request_reason_required')
  y=replace(x,state=target,decision_reason=note.strip() or x.decision_reason,version=x.version+1,updated_at=self.now());t='state.'+target.value;e=self._event_obj(y,a,t,note.strip() or None);self.repo.save_with_event(y,expected_version,e);self._audit(y,a,t);return y
 def assign(self,a,i,rid,assignee,expected_version):
  self._staff(a,i);x=self.get(a,i,rid);m=self.campus.membership(i,assignee)
  if not m or m.state!=MembershipState.ACTIVE or m.role not in STAFF:raise ValueError('service_request_assignee_invalid')
  if x.version!=expected_version:raise ValueError('service_request_concurrent_modification')
  y=replace(x,assigned_to=assignee,version=x.version+1,updated_at=self.now());e=self._event_obj(y,a,'assigned',assignee);self.repo.save_with_event(y,expected_version,e);self._audit(y,a,'assigned');return y
 def fulfill(self,a,i,rid,document_ref,sha256_hex,expected_version):
  self._staff(a,i);x=self.get(a,i,rid)
  if x.state!=RequestState.APPROVED:raise ValueError('service_request_not_approved')
  if len(sha256_hex)!=64 or any(c not in '0123456789abcdefABCDEF' for c in sha256_hex):raise ValueError('service_request_sha256_invalid')
  if not document_ref.strip():raise ValueError('service_request_document_required')
  if x.version!=expected_version:raise ValueError('service_request_concurrent_modification')
  y=replace(x,state=RequestState.FULFILLED,output_document_ref=document_ref.strip(),output_sha256=sha256_hex.lower(),version=x.version+1,updated_at=self.now());e=self._event_obj(y,a,'fulfilled');self.repo.save_with_event(y,expected_version,e);self._audit(y,a,'fulfilled');return y
 def queue(self,a,i,state=None,assigned_to=None,limit=100,offset=0):
  self._staff(a,i)
  if state is not None:state=RequestState(state).value
  if not 1<=limit<=200 or offset<0:raise ValueError('service_request_pagination_invalid')
  return self.repo.list_queue(i,state,assigned_to,limit,offset)
 def dashboard(self,a,i):
  self._staff(a,i)
  return self.repo.status_counts(i)
 def timeline(self,a,i,rid):
  x=self.get(a,i,rid)
  events=self.repo.events(x.id)
  # Internal assignment notes and staff-only metadata must not leak into student self-service.
  if a==x.requester_account_id:
   return [replace(e,note=None) if e.event_type=='assigned' else e for e in events]
  return events

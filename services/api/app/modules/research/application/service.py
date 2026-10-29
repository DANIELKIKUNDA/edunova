from dataclasses import replace
from uuid import uuid4
from hashlib import sha256
from app.modules.research.domain.model import *
from app.modules.campus.domain.model import CampusRole,MembershipState
from app.modules.student_records.domain.model import StudentState,RegistrationState
STAFF={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ACADEMIC_ADMIN}
TRANS={ResearchState.PROPOSED:{ResearchState.APPROVED,ResearchState.CANCELLED},ResearchState.APPROVED:{ResearchState.IN_PROGRESS,ResearchState.CANCELLED},ResearchState.IN_PROGRESS:{ResearchState.READY_FOR_DEFENSE,ResearchState.CANCELLED},ResearchState.READY_FOR_DEFENSE:{ResearchState.DEFENDED,ResearchState.IN_PROGRESS}}
class ResearchService:
 def __init__(self,repo,campus,students,now,audit=None):self.repo=repo;self.campus=campus;self.students=students;self.now=now;self.audit=audit
 def _staff(self,a,i):
  m=self.campus.membership(i,a)
  if not m or m.state!=MembershipState.ACTIVE or m.role not in STAFF:raise PermissionError('research_academic_officer_required')
 def _audit(self,a,act,id):
  if self.audit:self.audit.record(actor_id=a,action=act,target_type='research',target_id=id,metadata={})
 def create(self,a,i,student_id,academic_registration_id,kind,title,supervisor_account_id):
  self._staff(a,i);st=self.students.get(student_id)
  if not st or st.institution_id!=i or st.state!=StudentState.ACTIVE:raise ValueError('research_student_scope_mismatch')
  if not any(r.id==academic_registration_id and r.institution_id==i and r.state==RegistrationState.ENROLLED for r in self.students.registrations(student_id)):raise ValueError('research_active_registration_required')
  sup=self.campus.membership(i,supervisor_account_id)
  if not sup or sup.state!=MembershipState.ACTIVE or sup.role==CampusRole.STUDENT:raise ValueError('research_supervisor_invalid')
  title=title.strip()
  if len(title)<5 or len(title)>500:raise ValueError('research_title_invalid')
  n=self.now();x=ResearchProject(uuid4().hex,i,student_id,academic_registration_id,ResearchKind(kind),title,supervisor_account_id,ResearchState.PROPOSED,1,n,n);self.repo.create(x);self._audit(a,'research.created',x.id);return x
 def get(self,a,i,pid):
  x=self.repo.get(i,pid)
  if not x:raise ValueError('research_not_found')
  st=self.students.get(x.student_id)
  if a!=st.account_id and a!=x.supervisor_account_id:self._staff(a,i)
  return x
 def transition(self,a,i,pid,state,expected_version,reason):
  self._staff(a,i);x=self.get(a,i,pid)
  if not reason.strip():raise ValueError('research_reason_required')
  if x.version!=expected_version:raise ValueError('research_concurrent_modification')
  target=ResearchState(state)
  if target not in TRANS.get(x.state,set()):raise ValueError('research_invalid_transition')
  if target==ResearchState.READY_FOR_DEFENSE:
   rs=self.repo.revisions(pid)
   if not rs or rs[-1].state!=RevisionState.APPROVED:raise ValueError('research_approved_revision_required')
  y=replace(x,state=target,version=x.version+1,updated_at=self.now());self.repo.save(y,expected_version);self._audit(a,'research.transition.'+target.value,pid);return y
 def submit_revision(self,a,i,pid,document_ref,sha256_hex,student_note=''):
  x=self.get(a,i,pid);st=self.students.get(x.student_id)
  if a!=st.account_id:raise PermissionError('research_student_revision_only')
  if x.state not in {ResearchState.APPROVED,ResearchState.IN_PROGRESS}:raise ValueError('research_revision_state_invalid')
  if len(sha256_hex)!=64 or any(c not in '0123456789abcdefABCDEF' for c in sha256_hex):raise ValueError('research_sha256_invalid')
  rs=self.repo.revisions(pid)
  if rs and rs[-1].state==RevisionState.SUBMITTED:raise ValueError('research_revision_pending_review')
  r=ResearchRevision(uuid4().hex,pid,len(rs)+1,document_ref.strip(),sha256_hex.lower(),RevisionState.SUBMITTED,student_note.strip(),None,self.now(),None);self.repo.add_revision(r);self._audit(a,'research.revision.submitted',r.id);return r
 def review_revision(self,a,i,pid,revision_id,decision,note):
  x=self.get(a,i,pid)
  if a!=x.supervisor_account_id:self._staff(a,i)
  rs=self.repo.revisions(pid);r=next((z for z in rs if z.id==revision_id),None)
  if not r or r.state!=RevisionState.SUBMITTED:raise ValueError('research_revision_not_reviewable')
  state=RevisionState(decision)
  if state not in {RevisionState.APPROVED,RevisionState.CHANGES_REQUESTED}:raise ValueError('research_revision_decision_invalid')
  if state==RevisionState.CHANGES_REQUESTED and not note.strip():raise ValueError('research_review_note_required')
  q=replace(r,state=state,reviewer_note=note.strip() or None,reviewed_at=self.now());self.repo.review_revision(q);self._audit(a,'research.revision.'+state.value,r.id);return q
 def schedule_defense(self,a,i,pid,scheduled_at,room,chair_account_id,secretary_account_id):
  self._staff(a,i);x=self.get(a,i,pid)
  if x.state!=ResearchState.READY_FOR_DEFENSE:raise ValueError('research_not_ready_for_defense')
  if chair_account_id==secretary_account_id:raise ValueError('research_defense_separation_required')
  for who in (chair_account_id,secretary_account_id):
   m=self.campus.membership(i,who)
   if not m or m.state!=MembershipState.ACTIVE or m.role==CampusRole.STUDENT:raise ValueError('research_defense_member_invalid')
  if self.repo.get_defense(pid):raise ValueError('research_defense_already_scheduled')
  d=Defense(uuid4().hex,pid,scheduled_at,room.strip(),chair_account_id,secretary_account_id,'scheduled',None,None,None,self.now());self.repo.create_defense(d);self._audit(a,'research.defense.scheduled',d.id);return d
 def record_defense(self,a,i,pid,decision,score,minutes_text):
  self._staff(a,i);x=self.get(a,i,pid);d=self.repo.get_defense(pid)
  if not d or d.status!='scheduled':raise ValueError('research_defense_not_scheduled')
  if decision not in {'passed','failed','adjourned'}:raise ValueError('research_defense_decision_invalid')
  if score is not None and not 0<=score<=100:raise ValueError('research_defense_score_invalid')
  if not minutes_text.strip():raise ValueError('research_defense_minutes_required')
  h=sha256(minutes_text.encode()).hexdigest();q=replace(d,status='completed',decision=decision,score=score,minutes_sha256=h);self.repo.save_defense(q)
  if decision in {'passed','failed'}:
   y=replace(x,state=ResearchState.DEFENDED,version=x.version+1,updated_at=self.now());self.repo.save(y,x.version)
  self._audit(a,'research.defense.recorded',d.id);return q

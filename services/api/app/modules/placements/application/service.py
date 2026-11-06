from dataclasses import replace
from datetime import date
from uuid import uuid4
from app.modules.placements.domain.model import Placement,PlacementLog,PlacementState
from app.modules.campus.domain.model import CampusRole,MembershipState
from app.modules.student_records.domain.model import StudentState,RegistrationState

STAFF={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ACADEMIC_ADMIN}
TRANSITIONS={PlacementState.PROPOSED:{PlacementState.APPROVED,PlacementState.CANCELLED},PlacementState.APPROVED:{PlacementState.ACTIVE,PlacementState.CANCELLED},PlacementState.ACTIVE:{PlacementState.COMPLETED,PlacementState.CANCELLED}}
class PlacementService:
    def __init__(self,repo,campus,students,now,audit=None):self.repo=repo;self.campus=campus;self.students=students;self.now=now;self.audit=audit
    def _staff(self,actor,i):
        m=self.campus.membership(i,actor)
        if not m or m.state!=MembershipState.ACTIVE or m.role not in STAFF:raise PermissionError('placement_academic_officer_required')
    def _record(self,actor,action,target):
        if self.audit:self.audit.record(actor_id=actor,action=action,target_type='placement',target_id=target,metadata={})
    def create(self,actor,i,student_id,academic_registration_id,host_name,supervisor_account_id,start_date,end_date):
        self._staff(actor,i)
        student=self.students.get(student_id)
        if not student or student.institution_id!=i or student.state!=StudentState.ACTIVE:raise ValueError('placement_student_scope_mismatch')
        regs=self.students.registrations(student_id)
        if not any(r.id==academic_registration_id and r.institution_id==i and r.state==RegistrationState.ENROLLED for r in regs):raise ValueError('placement_active_registration_required')
        supervisor=self.campus.membership(i,supervisor_account_id)
        if not supervisor or supervisor.state!=MembershipState.ACTIVE or supervisor.role==CampusRole.STUDENT:raise ValueError('placement_supervisor_invalid')
        if not host_name.strip() or len(host_name)>200:raise ValueError('placement_host_invalid')
        try:a=date.fromisoformat(start_date);b=date.fromisoformat(end_date)
        except ValueError:raise ValueError('placement_dates_invalid')
        if a>b:raise ValueError('placement_dates_invalid')
        n=self.now();x=Placement(uuid4().hex,i,student_id,academic_registration_id,host_name.strip(),supervisor_account_id,start_date,end_date,PlacementState.PROPOSED,1,n,n)
        self.repo.create(x);self._record(actor,'placement.created',x.id);return x
    def get(self,actor,i,pid):
        p=self.repo.get(i,pid)
        if not p:raise ValueError('placement_not_found')
        if actor!=self.students.get(p.student_id).account_id:self._staff(actor,i)
        return p
    def transition(self,actor,i,pid,state,expected_version,reason):
        self._staff(actor,i);p=self.get(actor,i,pid)
        if not reason.strip():raise ValueError('placement_reason_required')
        if p.version!=expected_version:raise ValueError('placement_concurrent_modification')
        target=PlacementState(state)
        if target not in TRANSITIONS.get(p.state,set()):raise ValueError('placement_invalid_transition')
        q=replace(p,state=target,version=p.version+1,updated_at=self.now());self.repo.transition(q,expected_version);self._record(actor,'placement.transition.'+target.value,pid);return q
    def log(self,actor,i,pid,activity_date,description):
        p=self.get(actor,i,pid)
        if actor!=self.students.get(p.student_id).account_id:raise PermissionError('placement_student_log_only')
        if p.state!=PlacementState.ACTIVE:raise ValueError('placement_not_active')
        try:d=date.fromisoformat(activity_date)
        except ValueError:raise ValueError('placement_log_date_invalid')
        if not date.fromisoformat(p.start_date)<=d<=date.fromisoformat(p.end_date):raise ValueError('placement_log_outside_dates')
        if not description.strip() or len(description)>3000:raise ValueError('placement_log_invalid')
        x=PlacementLog(uuid4().hex,pid,p.student_id,activity_date,description.strip(),self.now());self.repo.add_log(x);self._record(actor,'placement.log.created',x.id);return x
    def logs(self,actor,i,pid):self.get(actor,i,pid);return self.repo.logs(pid)

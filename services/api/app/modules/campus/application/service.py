from __future__ import annotations
import re
from dataclasses import replace
from uuid import uuid4
from app.modules.campus.domain.model import *

WRITE_ROLES={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}
STRUCTURE_ROLES=WRITE_ROLES|{CampusRole.FACULTY_ADMIN}
READ_ROLES=set(CampusRole)

class CampusService:
    def __init__(self,repo,now,audit=None): self.repo=repo;self.now=now;self.audit=audit
    def _audit(self,actor,action,entity_type,entity_id,metadata=None):
        if self.audit:self.audit.write(actor_id=actor,action=action,entity_type=entity_type,entity_id=entity_id,metadata=metadata or {})
    def create_institution(self,actor_id,*,name,slug,legal_name='',country_code='CD',city=None,logo_url=None):
        slug=re.sub(r'[^a-z0-9-]+','-',slug.strip().lower()).strip('-')
        if len(name.strip())<2 or len(slug)<2:raise ValueError('campus_invalid_institution')
        if self.repo.institution_by_slug(slug):raise ValueError('campus_slug_exists')
        now=self.now();x=Institution(uuid4().hex,slug,name.strip(),legal_name.strip(),country_code.upper(),city,logo_url,InstitutionState.ACTIVE,1,actor_id,now,now)
        self.repo.save_institution(x);m=Membership(uuid4().hex,x.id,actor_id,CampusRole.OWNER,MembershipState.ACTIVE,None,actor_id,now,1,now,now);self.repo.save_membership(m)
        self._audit(actor_id,'campus.institution.created','campus_institution',x.id,{'slug':slug});return x
    def _ensure_writable(self,institution_id):
        x=self.repo.institution(institution_id)
        if not x: raise ValueError('campus_institution_not_found')
        if x.state!=InstitutionState.ACTIVE: raise PermissionError('campus_institution_not_writable')
        return x
    def _descendant_unit_ids(self,institution_id,root_id):
        units=self.repo.list_units(institution_id); children={}
        for u in units: children.setdefault(u.parent_id,[]).append(u.id)
        seen={root_id}; stack=[root_id]
        while stack:
            for child in children.get(stack.pop(),[]):
                if child not in seen: seen.add(child);stack.append(child)
        return seen
    def _assert_scope(self,actor,institution_id,unit_id):
        if actor.role!=CampusRole.FACULTY_ADMIN:return
        if not actor.unit_id:raise PermissionError('campus_scope_forbidden')
        if not unit_id or unit_id not in self._descendant_unit_ids(institution_id,actor.unit_id):raise PermissionError('campus_scope_forbidden')
    def _assert_can_assign_role(self,actor,target_role):
        if target_role==CampusRole.OWNER: raise PermissionError('campus_role_escalation_forbidden')
        if actor.role==CampusRole.OWNER:return
        if actor.role==CampusRole.RECTOR and target_role not in {CampusRole.RECTOR,CampusRole.OWNER}:return
        if actor.role in {CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN} and target_role in {CampusRole.FACULTY_ADMIN,CampusRole.TEACHER,CampusRole.STUDENT,CampusRole.AUDITOR}:return
        if actor.role==CampusRole.FACULTY_ADMIN and target_role in {CampusRole.TEACHER,CampusRole.STUDENT}:return
        raise PermissionError('campus_role_escalation_forbidden')
    def membership(self,actor_id,institution_id,roles=None):
        m=self.repo.membership(institution_id,actor_id)
        if not m or m.state!=MembershipState.ACTIVE:raise PermissionError('campus_membership_required')
        if roles and m.role not in roles:raise PermissionError('campus_role_forbidden')
        return m
    def institution(self,actor_id,institution_id):self.membership(actor_id,institution_id,READ_ROLES);return self.repo.institution(institution_id)
    def update_institution(self,actor_id,institution_id,expected_version,**changes):
        self.membership(actor_id,institution_id,WRITE_ROLES);x=self.repo.institution(institution_id)
        if not x:raise ValueError('campus_institution_not_found')
        if x.row_version!=expected_version:raise ValueError('campus_concurrent_modification')
        allowed={k:v for k,v in changes.items() if k in {'name','legal_name','city','logo_url','state'} and v is not None};now=self.now();y=replace(x,**allowed,row_version=x.row_version+1,updated_at=now);self.repo.save_institution(y,expected_version);self._audit(actor_id,'campus.institution.updated','campus_institution',x.id,{'version':y.row_version});return y
    def add_unit(self,actor_id,institution_id,*,kind,name,code,parent_id=None):
        actor=self.membership(actor_id,institution_id,STRUCTURE_ROLES);self._ensure_writable(institution_id)
        if actor.role==CampusRole.FACULTY_ADMIN:self._assert_scope(actor,institution_id,parent_id)
        if parent_id:
            p=self.repo.unit(institution_id,parent_id)
            if not p:raise ValueError('campus_parent_unit_not_found')
            valid={UnitKind.CAMPUS:{UnitKind.FACULTY},UnitKind.FACULTY:{UnitKind.DEPARTMENT,UnitKind.PROGRAM},UnitKind.DEPARTMENT:{UnitKind.PROGRAM},UnitKind.PROGRAM:set()}
            if kind not in valid[p.kind]:raise ValueError('campus_invalid_unit_hierarchy')
        elif kind not in {UnitKind.CAMPUS,UnitKind.FACULTY,UnitKind.PROGRAM}:raise ValueError('campus_parent_required')
        if self.repo.unit_by_code(institution_id,code):raise ValueError('campus_unit_code_exists')
        now=self.now();x=AcademicUnit(uuid4().hex,institution_id,kind,name.strip(),code.strip().upper(),parent_id,True,1,now,now);self.repo.save_unit(x);self._audit(actor_id,'campus.unit.created','campus_unit',x.id,{'institution_id':institution_id,'kind':kind.value});return x
    def add_period(self,actor_id,institution_id,*,kind,name,starts_on,ends_on,parent_id=None):
        actor=self.membership(actor_id,institution_id,STRUCTURE_ROLES);self._ensure_writable(institution_id)
        if starts_on>=ends_on:raise ValueError('campus_invalid_period_dates')
        if parent_id:
            p=self.repo.period(institution_id,parent_id)
            if not p:raise ValueError('campus_parent_period_not_found')
            valid={PeriodKind.ACADEMIC_YEAR:{PeriodKind.SEMESTER,PeriodKind.TERM},PeriodKind.SEMESTER:{PeriodKind.TERM},PeriodKind.TERM:set()}
            if kind not in valid[p.kind]:raise ValueError('campus_invalid_period_hierarchy')
            if starts_on<p.starts_on or ends_on>p.ends_on:raise ValueError('campus_period_outside_parent')
        elif kind!=PeriodKind.ACADEMIC_YEAR:raise ValueError('campus_period_parent_required')
        now=self.now();x=AcademicPeriod(uuid4().hex,institution_id,kind,name.strip(),starts_on,ends_on,parent_id,True,1,now);self.repo.save_period(x);self._audit(actor_id,'campus.period.created','campus_period',x.id);return x
    def invite_member(self,actor_id,institution_id,*,account_id,role,unit_id=None):
        actor=self.membership(actor_id,institution_id,WRITE_ROLES|{CampusRole.FACULTY_ADMIN});self._ensure_writable(institution_id);self._assert_can_assign_role(actor,role)
        if role==CampusRole.FACULTY_ADMIN and not unit_id:raise ValueError('campus_faculty_admin_scope_required')
        if unit_id and not self.repo.unit(institution_id,unit_id):raise ValueError('campus_unit_not_found')
        self._assert_scope(actor,institution_id,unit_id)
        old=self.repo.membership(institution_id,account_id)
        if old and old.state==MembershipState.ACTIVE:raise ValueError('campus_member_already_active')
        now=self.now();x=Membership(old.id if old else uuid4().hex,institution_id,account_id,role,MembershipState.INVITED,unit_id,actor_id,None,(old.row_version+1 if old else 1),old.created_at if old else now,now);self.repo.save_membership(x,old.row_version if old else None);self._audit(actor_id,'campus.member.invited','campus_membership',x.id,{'institution_id':institution_id,'role':role.value});return x
    def accept_invitation(self,actor_id,institution_id):
        x=self.repo.membership(institution_id,actor_id)
        if x and x.role==CampusRole.FACULTY_ADMIN and not x.unit_id:raise ValueError('campus_faculty_admin_scope_required')
        if not x or x.state!=MembershipState.INVITED:raise ValueError('campus_invitation_not_found')
        now=self.now();y=replace(x,state=MembershipState.ACTIVE,joined_at=now,row_version=x.row_version+1,updated_at=now);self.repo.save_membership(y,x.row_version);self._audit(actor_id,'campus.member.joined','campus_membership',y.id);return y
    def set_member_state(self,actor_id,institution_id,account_id,state,expected_version):
        self.membership(actor_id,institution_id,WRITE_ROLES);self._ensure_writable(institution_id);x=self.repo.membership(institution_id,account_id)
        if not x:raise ValueError('campus_member_not_found')
        if x.role==CampusRole.OWNER and state!=MembershipState.ACTIVE:raise ValueError('campus_owner_cannot_be_revoked')
        if x.row_version!=expected_version:raise ValueError('campus_concurrent_modification')
        y=replace(x,state=state,row_version=x.row_version+1,updated_at=self.now());self.repo.save_membership(y,x.row_version);self._audit(actor_id,'campus.member.state_changed','campus_membership',y.id,{'state':state.value});return y
    def set_member_role(self,actor_id,institution_id,account_id,role,expected_version):
        actor=self.membership(actor_id,institution_id,WRITE_ROLES);self._ensure_writable(institution_id);self._assert_can_assign_role(actor,role);x=self.repo.membership(institution_id,account_id)
        if not x:raise ValueError('campus_member_not_found')
        if x.role==CampusRole.OWNER:raise ValueError('campus_owner_role_immutable')
        if x.row_version!=expected_version:raise ValueError('campus_concurrent_modification')
        if role==CampusRole.FACULTY_ADMIN and not x.unit_id:raise ValueError('campus_faculty_admin_scope_required')
        y=replace(x,role=role,row_version=x.row_version+1,updated_at=self.now());self.repo.save_membership(y,x.row_version);self._audit(actor_id,'campus.member.role_changed','campus_membership',y.id,{'role':role.value});return y
    def list_members(self,actor_id,institution_id):
        actor=self.membership(actor_id,institution_id,READ_ROLES);members=self.repo.list_members(institution_id)
        if actor.role!=CampusRole.FACULTY_ADMIN:return members
        allowed=self._descendant_unit_ids(institution_id,actor.unit_id) if actor.unit_id else set()
        return tuple(m for m in members if m.account_id==actor_id or (m.unit_id and m.unit_id in allowed))
    def create_cohort(self,actor_id,institution_id,*,program_unit_id,academic_period_id,name,level):
        actor=self.membership(actor_id,institution_id,STRUCTURE_ROLES);self._ensure_writable(institution_id);self._assert_scope(actor,institution_id,program_unit_id);u=self.repo.unit(institution_id,program_unit_id);p=self.repo.period(institution_id,academic_period_id)
        if not u or u.kind!=UnitKind.PROGRAM:raise ValueError('campus_program_required')
        if not p:raise ValueError('campus_period_not_found')
        now=self.now();x=Cohort(uuid4().hex,institution_id,program_unit_id,academic_period_id,name.strip(),level.strip(),True,1,now,now);self.repo.save_cohort(x);self._audit(actor_id,'campus.cohort.created','campus_cohort',x.id);return x
    def enroll(self,actor_id,institution_id,*,cohort_id,student_account_id):
        actor=self.membership(actor_id,institution_id,STRUCTURE_ROLES);self._ensure_writable(institution_id);c=self.repo.cohort(institution_id,cohort_id);m=self.repo.membership(institution_id,student_account_id)
        if not c:raise ValueError('campus_cohort_not_found')
        if not m or m.state!=MembershipState.ACTIVE or m.role!=CampusRole.STUDENT:raise ValueError('campus_active_student_required')
        old=self.repo.enrollment(cohort_id,student_account_id)
        if old and old.active:return old
        x=Enrollment(old.id if old else uuid4().hex,institution_id,cohort_id,student_account_id,True,old.created_at if old else self.now());self.repo.save_enrollment(x);self._audit(actor_id,'campus.student.enrolled','campus_enrollment',x.id);return x
    def overview(self,actor_id,institution_id):
        self.membership(actor_id,institution_id,READ_ROLES);return self.repo.overview(institution_id)
    def my_institutions(self,actor_id):return self.repo.institutions_for_account(actor_id)

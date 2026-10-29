from dataclasses import replace
from hashlib import sha256
import json
from uuid import uuid4
from app.modules.jury.domain.model import JurySession,JuryOutcome,JuryState,JuryDecision,JuryMember,JuryMemberRole,JuryVote,JuryVoteChoice,JuryMinutes
from app.modules.campus.domain.model import CampusRole,MembershipState
from app.modules.student_records.domain.model import CourseRegistrationState,RegistrationState,StudentState

JURY_ROLES={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ACADEMIC_ADMIN}
class JuryService:
    def __init__(self,repo,campus,students,now,audit=None,academic=None):
        self.repo=repo;self.campus=campus;self.students=students;self.now=now;self.audit=audit;self.academic=academic
    def _staff(self,actor,institution):
        member=self.campus.membership(institution,actor)
        if not member or member.state!=MembershipState.ACTIVE or member.role not in JURY_ROLES:
            raise PermissionError('jury_authorized_academic_officer_required')
    def _audit(self,actor,action,target,metadata=None):
        if self.audit:self.audit.record(actor_id=actor,action=action,target_type='jury',target_id=target,metadata=metadata or {})
    def create(self,actor,institution,cohort_id,academic_year_id,curriculum_id,name,min_credits,quorum=1):
        self._staff(actor,institution)
        cohort=self.campus.cohort(institution,cohort_id)
        if not cohort:raise ValueError('jury_cohort_not_found')
        if not name.strip() or not 0<=min_credits<=600 or not 1<=quorum<=100:raise ValueError('jury_invalid_rule')
        if self.academic:
            binding=self.academic.binding_for_cohort(institution,cohort_id)
            curriculum=self.academic.curriculum(institution,curriculum_id)
            if not binding or binding.curriculum_id!=curriculum_id or not curriculum or curriculum.effective_academic_year_id!=academic_year_id or curriculum.program_unit_id!=cohort.program_unit_id or curriculum.state.value!='published':
                raise ValueError('jury_curriculum_scope_mismatch')
        n=self.now();x=JurySession(uuid4().hex,institution,cohort_id,curriculum_id,academic_year_id,name.strip(),float(min_credits),JuryState.DRAFT,1,actor,n,n,int(quorum))
        self.repo.create(x);self._audit(actor,'jury.session.created',x.id);return x
    def _get(self,institution,session_id):
        x=self.repo.get(institution,session_id)
        if not x:raise ValueError('jury_session_not_found')
        return x
    def get(self,actor,institution,session_id):
        self._staff(actor,institution);return self._get(institution,session_id)
    def evaluate(self,actor,institution,session_id,student_id,reason):
        self._staff(actor,institution);session=self._get(institution,session_id)
        if session.state!=JuryState.DRAFT:raise ValueError('jury_session_locked')
        if not reason.strip():raise ValueError('jury_decision_reason_required')
        existing=self.repo.outcome(session_id,student_id)
        if existing:return existing
        student=self.students.get(student_id)
        if not student or student.institution_id!=institution or student.cohort_id!=session.cohort_id or student.curriculum_id!=session.curriculum_id or student.state!=StudentState.ACTIVE:
            raise ValueError('jury_student_scope_mismatch')
        registrations=[r for r in self.students.registrations(student_id) if r.academic_year_id==session.academic_year_id and r.cohort_id==session.cohort_id and r.curriculum_id==session.curriculum_id and r.state in {RegistrationState.ENROLLED,RegistrationState.COMPLETED}]
        if not registrations:raise ValueError('jury_academic_registration_required')
        courses=[c for c in self.students.course_registrations(student_id) if c.registration_id in {r.id for r in registrations}]
        if not courses:raise ValueError('jury_course_results_missing')
        # Credits are awarded only from canonical validated ECUE, never from unpublished gradebook drafts.
        earned=round(sum(c.credits or 0 for c in courses if c.state in {CourseRegistrationState.VALIDATED,CourseRegistrationState.EXEMPTED}),4)
        unresolved=any(c.state==CourseRegistrationState.ENROLLED for c in courses)
        decision=JuryDecision.DEFERRED if unresolved else (JuryDecision.PASS if earned>=session.min_credits else JuryDecision.RETAKE)
        digest=self._evidence_hash(session,student_id)
        x=JuryOutcome(uuid4().hex,session.id,student_id,decision,earned,session.min_credits,digest,actor,reason.strip(),self.now())
        self.repo.save_outcome(x);self._audit(actor,'jury.outcome.recorded',x.id,{'student_id':student_id,'decision':decision.value,'evidence_hash':digest});return x
    def _evidence_hash(self,session,student_id):
        regs=[r for r in self.students.registrations(student_id) if r.academic_year_id==session.academic_year_id and r.cohort_id==session.cohort_id and r.curriculum_id==session.curriculum_id and r.state in {RegistrationState.ENROLLED,RegistrationState.COMPLETED}]
        courses=[c for c in self.students.course_registrations(student_id) if c.registration_id in {r.id for r in regs}]
        evidence=[{'id':c.id,'course':c.curriculum_course_id,'credits':c.credits,'state':c.state.value} for c in sorted(courses,key=lambda c:c.id)]
        return sha256(json.dumps({'curriculum':session.curriculum_id,'courses':evidence,'rule':session.min_credits},sort_keys=True,separators=(',',':')).encode()).hexdigest()

    def add_member(self,actor,institution,session_id,account_id,role='member',voting=True):
        self._staff(actor,institution); x=self._get(institution,session_id)
        if x.state!=JuryState.DRAFT: raise ValueError('jury_session_locked')
        member=self.campus.membership(institution,account_id)
        if not member or member.state!=MembershipState.ACTIVE: raise ValueError('jury_member_not_active')
        existing={m.account_id for m in self.repo.members(session_id)}
        if account_id in existing: raise ValueError('jury_member_duplicate')
        if role=='president' and any(m.role==JuryMemberRole.PRESIDENT for m in self.repo.members(session_id)): raise ValueError('jury_president_already_exists')
        m=JuryMember(uuid4().hex,session_id,account_id,JuryMemberRole(role),bool(voting),self.now()); self.repo.add_member(m); self._audit(actor,'jury.member.added',m.id,{'session_id':session_id,'account_id':account_id,'role':role}); return m
    def vote(self,actor,institution,session_id,student_id,choice,rationale):
        self._staff(actor,institution); x=self._get(institution,session_id)
        if x.state!=JuryState.DRAFT: raise ValueError('jury_session_locked')
        members={m.account_id:m for m in self.repo.members(session_id)}
        if actor not in members or not members[actor].voting: raise PermissionError('jury_voting_member_required')
        if not self.repo.outcome(session_id,student_id): raise ValueError('jury_outcome_required_before_vote')
        if any(v.account_id==actor for v in self.repo.votes(session_id,student_id)): raise ValueError('jury_vote_already_cast')
        if not rationale.strip(): raise ValueError('jury_vote_rationale_required')
        v=JuryVote(uuid4().hex,session_id,student_id,actor,JuryVoteChoice(choice),rationale.strip(),self.now()); self.repo.save_vote(v); self._audit(actor,'jury.vote.cast',v.id,{'student_id':student_id,'choice':choice}); return v
    def _quorum_ok(self,x):
        voting=[m for m in self.repo.members(x.id) if m.voting]
        if len(voting)<x.quorum or not any(m.role==JuryMemberRole.PRESIDENT for m in voting): return False
        for o in self.repo.outcomes(x.id):
            votes=self.repo.votes(x.id,o.student_id)
            voters={v.account_id for v in votes if v.choice!=JuryVoteChoice.ABSTAIN}
            approvals=sum(1 for v in votes if v.choice==JuryVoteChoice.APPROVE)
            rejections=sum(1 for v in votes if v.choice==JuryVoteChoice.REJECT)
            if len(voters)<x.quorum or approvals<=rejections: return False
        return True
    def generate_minutes(self,actor,institution,session_id):
        self._staff(actor,institution); x=self._get(institution,session_id)
        if x.state not in {JuryState.LOCKED,JuryState.PUBLISHED}: raise ValueError('jury_minutes_require_locked_session')
        old=self.repo.minutes(session_id)
        if old:return old
        outcomes=self.repo.outcomes(session_id)
        payload=[{'student':o.student_id,'decision':o.decision.value,'credits':o.credits_earned,'evidence':o.evidence_hash,'votes':[(v.account_id,v.choice.value) for v in self.repo.votes(session_id,o.student_id)]} for o in outcomes]
        digest=sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(); m=JuryMinutes(uuid4().hex,session_id,digest,len(outcomes),actor,self.now()); self.repo.save_minutes(m); self._audit(actor,'jury.minutes.generated',m.id,{'session_id':session_id,'hash':digest}); return m

    def lock(self,actor,institution,session_id,expected_version):
        self._staff(actor,institution);x=self._get(institution,session_id)
        if x.row_version!=expected_version:raise ValueError('jury_concurrent_modification')
        if x.state!=JuryState.DRAFT or not self.repo.outcomes(x.id):raise ValueError('jury_cannot_lock_empty_or_finalized')
        if not self._quorum_ok(x):raise ValueError('jury_quorum_not_reached')
        for outcome in self.repo.outcomes(x.id):
            if self._evidence_hash(x,outcome.student_id)!=outcome.evidence_hash:
                raise ValueError('jury_outcome_stale_academic_evidence')
        y=replace(x,state=JuryState.LOCKED,row_version=x.row_version+1,updated_at=self.now());self.repo.transition(y,x.row_version);self._audit(actor,'jury.session.locked',x.id);return y
    def publish(self,actor,institution,session_id,expected_version):
        self._staff(actor,institution);x=self._get(institution,session_id)
        if x.row_version!=expected_version:raise ValueError('jury_concurrent_modification')
        if x.state!=JuryState.LOCKED:raise ValueError('jury_session_must_be_locked')
        if not self.repo.minutes(x.id):raise ValueError('jury_minutes_required_before_publication')
        for outcome in self.repo.outcomes(x.id):
            if self._evidence_hash(x,outcome.student_id)!=outcome.evidence_hash:
                raise ValueError('jury_outcome_stale_academic_evidence')
        y=replace(x,state=JuryState.PUBLISHED,row_version=x.row_version+1,updated_at=self.now());self.repo.transition(y,x.row_version);self._audit(actor,'jury.session.published',x.id);return y
    def outcomes(self,actor,institution,session_id):
        self._staff(actor,institution);self._get(institution,session_id);return self.repo.outcomes(session_id)

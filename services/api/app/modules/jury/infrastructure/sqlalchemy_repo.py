from sqlalchemy import String, DateTime, Integer, Float, Boolean, UniqueConstraint, select, update
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base
from app.modules.jury.domain.model import JurySession, JuryOutcome, JuryState, JuryDecision, JuryMember, JuryMemberRole, JuryVote, JuryVoteChoice, JuryMinutes

class JurySessionRow(Base):
    __tablename__ = 'jury_sessions'
    __table_args__ = (UniqueConstraint('institution_id','cohort_id','academic_year_id','name',name='uq_jury_scope_name'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    cohort_id: Mapped[str] = mapped_column(String(64), index=True)
    curriculum_id: Mapped[str] = mapped_column(String(64))
    academic_year_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(160))
    min_credits: Mapped[float] = mapped_column(Float)
    state: Mapped[str] = mapped_column(String(24))
    row_version: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    quorum: Mapped[int] = mapped_column(Integer, default=1)

class JuryOutcomeRow(Base):
    __tablename__ = 'jury_outcomes'
    __table_args__ = (UniqueConstraint('session_id','student_id',name='uq_jury_outcome_student'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    student_id: Mapped[str] = mapped_column(String(64), index=True)
    decision: Mapped[str] = mapped_column(String(24))
    credits_earned: Mapped[float] = mapped_column(Float)
    credits_required: Mapped[float] = mapped_column(Float)
    evidence_hash: Mapped[str] = mapped_column(String(64))
    decided_by: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))

class JuryMemberRow(Base):
    __tablename__='jury_members'; __table_args__=(UniqueConstraint('session_id','account_id',name='uq_jury_member'),)
    id: Mapped[str]=mapped_column(String(64),primary_key=True); session_id: Mapped[str]=mapped_column(String(64),index=True); account_id: Mapped[str]=mapped_column(String(64)); role: Mapped[str]=mapped_column(String(24)); voting: Mapped[bool]=mapped_column(Boolean); created_at: Mapped[object]=mapped_column(DateTime(timezone=True))
class JuryVoteRow(Base):
    __tablename__='jury_votes'; __table_args__=(UniqueConstraint('session_id','student_id','account_id',name='uq_jury_vote'),)
    id: Mapped[str]=mapped_column(String(64),primary_key=True); session_id: Mapped[str]=mapped_column(String(64),index=True); student_id: Mapped[str]=mapped_column(String(64),index=True); account_id: Mapped[str]=mapped_column(String(64)); choice: Mapped[str]=mapped_column(String(24)); rationale: Mapped[str]=mapped_column(String(1000)); created_at: Mapped[object]=mapped_column(DateTime(timezone=True))
class JuryMinutesRow(Base):
    __tablename__='jury_minutes'
    id: Mapped[str]=mapped_column(String(64),primary_key=True); session_id: Mapped[str]=mapped_column(String(64),unique=True,index=True); content_hash: Mapped[str]=mapped_column(String(64)); outcome_count: Mapped[int]=mapped_column(Integer); generated_by: Mapped[str]=mapped_column(String(64)); generated_at: Mapped[object]=mapped_column(DateTime(timezone=True))

class SqlJuryRepository:
    def __init__(self, sf): self.sf = sf
    @staticmethod
    def _session(r):
        return JurySession(r.id,r.institution_id,r.cohort_id,r.curriculum_id,r.academic_year_id,r.name,r.min_credits,JuryState(r.state),r.row_version,r.created_by,r.created_at,r.updated_at,r.quorum)
    @staticmethod
    def _outcome(r):
        return JuryOutcome(r.id,r.session_id,r.student_id,JuryDecision(r.decision),r.credits_earned,r.credits_required,r.evidence_hash,r.decided_by,r.reason,r.created_at)
    def get(self, institution_id, session_id):
        with self.sf() as s:
            r=s.scalar(select(JurySessionRow).where(JurySessionRow.id==session_id,JurySessionRow.institution_id==institution_id))
            return self._session(r) if r else None
    def create(self, x):
        with self.sf() as s:
            s.add(JurySessionRow(**{**x.__dict__,'state':x.state.value}));s.commit()
    def transition(self, x, expected_version):
        with self.sf() as s:
            result=s.execute(update(JurySessionRow).where(JurySessionRow.id==x.id,JurySessionRow.institution_id==x.institution_id,JurySessionRow.row_version==expected_version).values(state=x.state.value,row_version=x.row_version,updated_at=x.updated_at))
            if result.rowcount!=1:s.rollback();raise ValueError('jury_concurrent_modification')
            s.commit()
    def outcome(self, session_id, student_id):
        with self.sf() as s:
            r=s.scalar(select(JuryOutcomeRow).where(JuryOutcomeRow.session_id==session_id,JuryOutcomeRow.student_id==student_id))
            return self._outcome(r) if r else None
    def save_outcome(self, x):
        with self.sf() as s:
            s.add(JuryOutcomeRow(**{**x.__dict__,'decision':x.decision.value}));s.commit()
    def outcomes(self, session_id):
        with self.sf() as s:
            return tuple(self._outcome(r) for r in s.scalars(select(JuryOutcomeRow).where(JuryOutcomeRow.session_id==session_id).order_by(JuryOutcomeRow.student_id)).all())

    def add_member(self,x):
        with self.sf() as s: s.add(JuryMemberRow(**{**x.__dict__,'role':x.role.value}));s.commit()
    def members(self,session_id):
        with self.sf() as s: return tuple(JuryMember(r.id,r.session_id,r.account_id,JuryMemberRole(r.role),r.voting,r.created_at) for r in s.scalars(select(JuryMemberRow).where(JuryMemberRow.session_id==session_id)).all())
    def save_vote(self,x):
        with self.sf() as s: s.add(JuryVoteRow(**{**x.__dict__,'choice':x.choice.value}));s.commit()
    def votes(self,session_id,student_id):
        with self.sf() as s: return tuple(JuryVote(r.id,r.session_id,r.student_id,r.account_id,JuryVoteChoice(r.choice),r.rationale,r.created_at) for r in s.scalars(select(JuryVoteRow).where(JuryVoteRow.session_id==session_id,JuryVoteRow.student_id==student_id)).all())
    def save_minutes(self,x):
        with self.sf() as s: s.add(JuryMinutesRow(**x.__dict__));s.commit()
    def minutes(self,session_id):
        with self.sf() as s:
            r=s.scalar(select(JuryMinutesRow).where(JuryMinutesRow.session_id==session_id)); return JuryMinutes(r.id,r.session_id,r.content_hash,r.outcome_count,r.generated_by,r.generated_at) if r else None

    def published_passes(self, institution_id, student_id):
        with self.sf() as s:
            rows=s.execute(select(JurySessionRow,JuryOutcomeRow).join(JuryOutcomeRow,JuryOutcomeRow.session_id==JurySessionRow.id).where(JurySessionRow.institution_id==institution_id,JurySessionRow.state==JuryState.PUBLISHED.value,JuryOutcomeRow.student_id==student_id,JuryOutcomeRow.decision==JuryDecision.PASS.value)).all()
            return tuple((self._session(a),self._outcome(b)) for a,b in rows)

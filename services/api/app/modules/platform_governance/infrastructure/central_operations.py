"""Central operations, isolated from private tenant/student data."""
from datetime import datetime, UTC
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime, select, func, update
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base
from app.modules.campus.infrastructure.sqlalchemy_repo import InstitutionRow, MembershipRow
from app.modules.identity.infrastructure.sqlalchemy_repo import AccountRow
from app.modules.platform_governance.infrastructure.sqlalchemy_repo import PlatformMembershipRow

class PlatformSupportTicketRow(Base):
    __tablename__ = 'platform_support_tickets'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(String(1500))
    state: Mapped[str] = mapped_column(String(24), index=True)
    priority: Mapped[str] = mapped_column(String(16))
    assigned_to: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by: Mapped[str] = mapped_column(String(64))
    updated_by: Mapped[str] = mapped_column(String(64))
    row_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class CentralOperationsRepository:
    def __init__(self, sf): self.sf=sf
    @staticmethod
    def ticket_out(x):
        return {k:getattr(x,k) for k in ('id','institution_id','title','description','state','priority','assigned_to','created_by','updated_by','row_version')} | {'created_at':x.created_at.isoformat(),'updated_at':x.updated_at.isoformat()}
    @staticmethod
    def member_out(x):
        return {k:getattr(x,k) for k in ('id','institution_id','account_id','role','state','invited_by','row_version')}
    def assignments(self, institution_id):
        with self.sf() as s:
            if s.get(InstitutionRow,institution_id) is None: raise ValueError('institution_not_found')
            rows=s.scalars(select(MembershipRow).where(MembershipRow.institution_id==institution_id,MembershipRow.role.in_(['admin','academic_admin','faculty_admin','rector'])).order_by(MembershipRow.account_id)).all()
            return [self.member_out(x) for x in rows]
    def assign(self,institution_id,account_id,role,actor,expected_version):
        if role not in ('admin','academic_admin','faculty_admin'): raise ValueError('invalid_admin_role')
        now=datetime.now(UTC)
        with self.sf() as s:
            inst=s.get(InstitutionRow,institution_id)
            if inst is None: raise ValueError('institution_not_found')
            if inst.state!='active': raise ValueError('institution_not_active')
            account=s.get(AccountRow,account_id)
            if account is None or account.state!='active': raise ValueError('account_not_active')
            member=s.scalar(select(MembershipRow).where(MembershipRow.institution_id==institution_id,MembershipRow.account_id==account_id))
            if member is None:
                if expected_version is not None: raise ValueError('assignment_concurrent_modification')
                member=MembershipRow(id=str(uuid4()),institution_id=institution_id,account_id=account_id,role=role,state='invited',unit_id=None,invited_by=actor,joined_at=None,row_version=1,created_at=now,updated_at=now)
                s.add(member)
            else:
                if expected_version is None or member.row_version!=expected_version: raise ValueError('assignment_concurrent_modification')
                if member.role in ('owner','rector') or member.role not in ('admin','academic_admin','faculty_admin'): raise ValueError('protected_membership')
                member.role=role;member.state='invited';member.joined_at=None;member.invited_by=actor;member.row_version+=1;member.updated_at=now
            s.commit();return self.member_out(member)
    def revoke(self,institution_id,account_id,actor,expected_version):
        with self.sf() as s:
            member=s.scalar(select(MembershipRow).where(MembershipRow.institution_id==institution_id,MembershipRow.account_id==account_id))
            if member is None: raise ValueError('assignment_not_found')
            if member.role not in ('admin','academic_admin','faculty_admin'): raise ValueError('protected_membership')
            if member.row_version!=expected_version: raise ValueError('assignment_concurrent_modification')
            result=s.execute(update(MembershipRow).where(MembershipRow.id==member.id,MembershipRow.row_version==expected_version).values(state='revoked',row_version=expected_version+1,updated_at=datetime.now(UTC)))
            if result.rowcount!=1: s.rollback();raise ValueError('assignment_concurrent_modification')
            s.commit();member=s.get(MembershipRow,member.id);return self.member_out(member)
    def tickets(self,limit=25,offset=0,state=None,institution_id=None):
        with self.sf() as s:
            conditions=[]
            if state:conditions.append(PlatformSupportTicketRow.state==state)
            if institution_id:conditions.append(PlatformSupportTicketRow.institution_id==institution_id)
            total=s.scalar(select(func.count()).select_from(PlatformSupportTicketRow).where(*conditions)) or 0
            rows=s.scalars(select(PlatformSupportTicketRow).where(*conditions).order_by(PlatformSupportTicketRow.created_at.desc(),PlatformSupportTicketRow.id).limit(limit).offset(offset)).all()
            return {'total':total,'limit':limit,'offset':offset,'items':[self.ticket_out(x) for x in rows]}
    def create_ticket(self,institution_id,title,description,priority,actor):
        if priority not in ('low','normal','high','critical'):raise ValueError('invalid_priority')
        now=datetime.now(UTC)
        with self.sf() as s:
            if s.get(InstitutionRow,institution_id) is None:raise ValueError('institution_not_found')
            x=PlatformSupportTicketRow(id=str(uuid4()),institution_id=institution_id,title=title,description=description,state='open',priority=priority,assigned_to=None,created_by=actor,updated_by=actor,row_version=1,created_at=now,updated_at=now)
            s.add(x);s.commit();return self.ticket_out(x)
    def update_ticket(self,ticket_id,state,assigned_to,actor,expected_version):
        if state not in ('open','in_progress','resolved','closed'):raise ValueError('invalid_ticket_state')
        with self.sf() as s:
            x=s.get(PlatformSupportTicketRow,ticket_id)
            if x is None:raise ValueError('ticket_not_found')
            if x.row_version!=expected_version:raise ValueError('ticket_concurrent_modification')
            if x.state=='closed' and state!='closed':raise ValueError('closed_ticket_immutable')
            if state=='closed' and x.state not in ('resolved','closed'):raise ValueError('ticket_must_be_resolved_before_closing')
            if assigned_to is not None:
                member=s.get(AccountRow,assigned_to)
                if member is None or member.state!='active':raise ValueError('assignee_not_active')
                operator=s.get(PlatformMembershipRow,assigned_to)
                if operator is None or not operator.active or operator.role not in ('owner','platform_admin','support_operator'):raise ValueError('assignee_not_support_operator')
            result=s.execute(update(PlatformSupportTicketRow).where(PlatformSupportTicketRow.id==ticket_id,PlatformSupportTicketRow.row_version==expected_version).values(state=state,assigned_to=assigned_to,updated_by=actor,row_version=expected_version+1,updated_at=datetime.now(UTC)))
            if result.rowcount!=1:s.rollback();raise ValueError('ticket_concurrent_modification')
            s.commit();return self.ticket_out(s.get(PlatformSupportTicketRow,ticket_id))

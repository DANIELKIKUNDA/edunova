from __future__ import annotations
from datetime import UTC
from sqlalchemy import String,Integer,DateTime,Boolean,select,update,func
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.platform_governance.domain.model import PlatformMembership,PlatformRole

def _utc(x): return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class PlatformMembershipRow(Base):
 __tablename__='platform_memberships'
 account_id:Mapped[str]=mapped_column(String(64),primary_key=True)
 role:Mapped[str]=mapped_column(String(40),index=True)
 active:Mapped[bool]=mapped_column(Boolean,index=True)
 row_version:Mapped[int]=mapped_column(Integer)
 granted_by:Mapped[str]=mapped_column(String(64),index=True)
 created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
 updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SqlPlatformGovernanceRepository:
 def __init__(self,sf): self.sf=sf
 def _m(self,r): return PlatformMembership(r.account_id,PlatformRole(r.role),r.active,r.row_version,r.granted_by,_utc(r.created_at),_utc(r.updated_at))
 def get(self,a):
  with self.sf() as s:
   r=s.get(PlatformMembershipRow,a); return self._m(r) if r else None
 def save(self,x,expected_version=None):
  d=dict(role=x.role.value,active=x.active,row_version=x.row_version,granted_by=x.granted_by,created_at=x.created_at,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(PlatformMembershipRow,x.account_id)
   if not old: s.add(PlatformMembershipRow(account_id=x.account_id,**d)); s.commit(); return
   q=update(PlatformMembershipRow).where(PlatformMembershipRow.account_id==x.account_id)
   if expected_version is not None:q=q.where(PlatformMembershipRow.row_version==expected_version)
   r=s.execute(q.values(**d))
   if r.rowcount!=1:s.rollback();raise ValueError('platform_concurrent_modification')
   s.commit()
 def list(self):
  with self.sf() as s:return tuple(self._m(r) for r in s.scalars(select(PlatformMembershipRow).order_by(PlatformMembershipRow.role,PlatformMembershipRow.account_id)).all())
 def count_by_role(self):
  with self.sf() as s:return {role:int(n) for role,n in s.execute(select(PlatformMembershipRow.role,func.count()).where(PlatformMembershipRow.active==True).group_by(PlatformMembershipRow.role)).all()}

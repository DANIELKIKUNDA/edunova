from __future__ import annotations
from datetime import UTC
from sqlalchemy import String,DateTime,Text,select
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.trust_governance.domain.model import *
class ConsentRow(Base):
 __tablename__='privacy_consents'; id:Mapped[str]=mapped_column(String(64),primary_key=True); account_id:Mapped[str]=mapped_column(String(64),index=True); purpose:Mapped[str]=mapped_column(String(128),index=True); policy_version:Mapped[str]=mapped_column(String(64)); state:Mapped[str]=mapped_column(String(32)); recorded_at:Mapped[object]=mapped_column(DateTime(timezone=True)); source:Mapped[str]=mapped_column(String(32))
class PrivacyRequestRow(Base):
 __tablename__='privacy_requests'; id:Mapped[str]=mapped_column(String(64),primary_key=True); account_id:Mapped[str]=mapped_column(String(64),index=True); kind:Mapped[str]=mapped_column(String(32)); state:Mapped[str]=mapped_column(String(32),index=True); requested_at:Mapped[object]=mapped_column(DateTime(timezone=True)); completed_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
class MfaCredentialRow(Base):
 __tablename__='account_mfa_credentials'; account_id:Mapped[str]=mapped_column(String(64),primary_key=True); encrypted_secret:Mapped[str]=mapped_column(Text); enabled:Mapped[bool]=mapped_column(default=False); created_at:Mapped[object]=mapped_column(DateTime(timezone=True)); verified_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
class RetentionPolicyRow(Base):
 __tablename__='institution_retention_policies'; id:Mapped[str]=mapped_column(String(64),primary_key=True); institution_id:Mapped[str]=mapped_column(String(64),index=True); data_class:Mapped[str]=mapped_column(String(64)); retention_days:Mapped[int]=mapped_column(); policy_version:Mapped[str]=mapped_column(String(64)); updated_at:Mapped[object]=mapped_column(DateTime(timezone=True)); updated_by:Mapped[str]=mapped_column(String(64))
class SecurityLedgerRow(Base):
 __tablename__='security_ledger'; id:Mapped[str]=mapped_column(String(64),primary_key=True); actor_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True); action:Mapped[str]=mapped_column(String(128),index=True); resource_type:Mapped[str]=mapped_column(String(64)); resource_id:Mapped[str]=mapped_column(String(128)); occurred_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True); previous_hash:Mapped[str]=mapped_column(String(64)); event_hash:Mapped[str]=mapped_column(String(64),unique=True); metadata_json:Mapped[str]=mapped_column(Text,default='{}')
def _utc(x): return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class SqlTrustGovernanceRepository:
 def __init__(self,sf): self.sf=sf
 def save_consent(self,x):
  with self.sf() as s: s.add(ConsentRow(id=x.id,account_id=x.account_id,purpose=x.purpose,policy_version=x.policy_version,state=x.state.value,recorded_at=x.recorded_at,source=x.source)); s.commit()
 def list_consents(self,a):
  with self.sf() as s: rows=s.scalars(select(ConsentRow).where(ConsentRow.account_id==a).order_by(ConsentRow.recorded_at)).all(); return [ConsentRecord(r.id,r.account_id,r.purpose,r.policy_version,ConsentState(r.state),_utc(r.recorded_at),r.source) for r in rows]
 def save_privacy_request(self,x):
  with self.sf() as s: s.add(PrivacyRequestRow(id=x.id,account_id=x.account_id,kind=x.kind.value,state=x.state.value,requested_at=x.requested_at,completed_at=x.completed_at)); s.commit()
 def get_mfa(self,account_id):
  with self.sf() as s:
   r=s.get(MfaCredentialRow,account_id); return MfaCredential(r.account_id,r.encrypted_secret,r.enabled,_utc(r.created_at),_utc(r.verified_at)) if r else None
 def save_mfa(self,x):
  with self.sf() as s: s.merge(MfaCredentialRow(**x.__dict__)); s.commit()
 def save_retention(self,x):
  with self.sf() as s: s.add(RetentionPolicyRow(**x.__dict__)); s.commit()
 def save_ledger(self,x):
  with self.sf() as s: s.add(SecurityLedgerRow(**x.__dict__)); s.commit()
 def last_ledger_hash(self):
  with self.sf() as s: r=s.scalar(select(SecurityLedgerRow).order_by(SecurityLedgerRow.occurred_at.desc(),SecurityLedgerRow.id.desc()).limit(1)); return r.event_hash if r else None
 def list_ledger(self):
  with self.sf() as s: rows=s.scalars(select(SecurityLedgerRow).order_by(SecurityLedgerRow.occurred_at,SecurityLedgerRow.id)).all(); return [SecurityLedgerEvent(r.id,r.actor_id,r.action,r.resource_type,r.resource_id,_utc(r.occurred_at),r.previous_hash,r.event_hash,r.metadata_json) for r in rows]

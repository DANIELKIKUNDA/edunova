from sqlalchemy import String,Integer,DateTime,Boolean,UniqueConstraint,select,func
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.payment_gateway.domain.model import *
class PaymentIntentRow(Base):
 __tablename__='payment_gateway_intents';__table_args__=(UniqueConstraint('institution_id','idempotency_key',name='uq_gateway_idempotency'),UniqueConstraint('merchant_reference',name='uq_gateway_merchant_ref'),UniqueConstraint('provider','provider_reference',name='uq_gateway_provider_ref'))
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);student_id:Mapped[str]=mapped_column(String(64),index=True);amount_minor:Mapped[int]=mapped_column(Integer);currency:Mapped[str]=mapped_column(String(8));provider:Mapped[str]=mapped_column(String(32),index=True);payer_msisdn:Mapped[str]=mapped_column(String(32));idempotency_key:Mapped[str]=mapped_column(String(160));merchant_reference:Mapped[str]=mapped_column(String(120));provider_reference:Mapped[str|None]=mapped_column(String(160),nullable=True);status:Mapped[str]=mapped_column(String(20),index=True);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True));expires_at:Mapped[object]=mapped_column(DateTime(timezone=True));failure_code:Mapped[str|None]=mapped_column(String(100),nullable=True);receipt_id:Mapped[str|None]=mapped_column(String(64),nullable=True)
class ProviderEventRow(Base):
 __tablename__='payment_gateway_events';__table_args__=(UniqueConstraint('provider','provider_event_id',name='uq_gateway_provider_event'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);provider:Mapped[str]=mapped_column(String(32),index=True);provider_event_id:Mapped[str]=mapped_column(String(160));payment_intent_id:Mapped[str]=mapped_column(String(64),index=True);provider_reference:Mapped[str|None]=mapped_column(String(160),nullable=True);status:Mapped[str]=mapped_column(String(30));payload_sha256:Mapped[str]=mapped_column(String(64));received_at:Mapped[object]=mapped_column(DateTime(timezone=True));processed:Mapped[bool]=mapped_column(Boolean)

class PaymentAttemptRow(Base):
 __tablename__='payment_gateway_attempts';__table_args__=(UniqueConstraint('payment_intent_id','attempt_no',name='uq_gateway_attempt_no'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);payment_intent_id:Mapped[str]=mapped_column(String(64),index=True);provider:Mapped[str]=mapped_column(String(32),index=True);kind:Mapped[str]=mapped_column(String(32));attempt_no:Mapped[int]=mapped_column(Integer);outcome:Mapped[str]=mapped_column(String(32));detail:Mapped[str|None]=mapped_column(String(500),nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class ReconciliationRecordRow(Base):
 __tablename__='payment_gateway_reconciliations'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);payment_intent_id:Mapped[str]=mapped_column(String(64),index=True);provider:Mapped[str]=mapped_column(String(32),index=True);provider_reference:Mapped[str|None]=mapped_column(String(160),nullable=True);provider_status:Mapped[str]=mapped_column(String(30));local_status:Mapped[str]=mapped_column(String(30));matched:Mapped[bool]=mapped_column(Boolean,index=True);note:Mapped[str|None]=mapped_column(String(500),nullable=True);checked_by:Mapped[str]=mapped_column(String(64));checked_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True)

class SqlPaymentGatewayRepository:
 def __init__(self,sf):self.sf=sf
 def _i(self,r):return PaymentIntent(r.id,r.institution_id,r.student_id,r.amount_minor,r.currency,r.provider,r.payer_msisdn,r.idempotency_key,r.merchant_reference,r.provider_reference,PaymentStatus(r.status),r.created_by,r.created_at,r.updated_at,r.expires_at,r.failure_code,r.receipt_id)
 def get(self,x):
  with self.sf() as s:r=s.get(PaymentIntentRow,x);return self._i(r) if r else None
 def by_idempotency(self,i,k):
  with self.sf() as s:r=s.scalar(select(PaymentIntentRow).where(PaymentIntentRow.institution_id==i,PaymentIntentRow.idempotency_key==k));return self._i(r) if r else None
 def save(self,x):
  with self.sf() as s:
   r=s.get(PaymentIntentRow,x.id);d=x.__dict__.copy();d['status']=x.status.value
   if not r:s.add(PaymentIntentRow(**d))
   else:
    for k,v in d.items():setattr(r,k,v)
   s.commit()
 def event(self,p,eid):
  with self.sf() as s:return s.scalar(select(ProviderEventRow).where(ProviderEventRow.provider==p,ProviderEventRow.provider_event_id==eid))
 def add_event(self,x):
  with self.sf() as s:s.add(ProviderEventRow(**x.__dict__));s.commit()
 def mark_event(self,p,eid):
  with self.sf() as s:r=s.scalar(select(ProviderEventRow).where(ProviderEventRow.provider==p,ProviderEventRow.provider_event_id==eid));r.processed=True;s.commit()

 def add_attempt(self,x):
  with self.sf() as s:s.add(PaymentAttemptRow(**x.__dict__));s.commit()
 def attempts(self,intent_id):
  with self.sf() as s:
   rs=s.scalars(select(PaymentAttemptRow).where(PaymentAttemptRow.payment_intent_id==intent_id).order_by(PaymentAttemptRow.attempt_no)).all();return tuple(PaymentAttempt(r.id,r.payment_intent_id,r.provider,r.kind,r.attempt_no,r.outcome,r.detail,r.created_at) for r in rs)
 def next_attempt_no(self,intent_id):
  with self.sf() as s:return int(s.scalar(select(func.count()).select_from(PaymentAttemptRow).where(PaymentAttemptRow.payment_intent_id==intent_id)) or 0)+1
 def add_reconciliation(self,x):
  with self.sf() as s:s.add(ReconciliationRecordRow(**x.__dict__));s.commit()
 def reconciliations(self,intent_id):
  with self.sf() as s:
   rs=s.scalars(select(ReconciliationRecordRow).where(ReconciliationRecordRow.payment_intent_id==intent_id).order_by(ReconciliationRecordRow.checked_at)).all();return tuple(ReconciliationRecord(r.id,r.payment_intent_id,r.provider,r.provider_reference,r.provider_status,r.local_status,r.matched,r.note,r.checked_by,r.checked_at) for r in rs)
 def pending(self,provider=None):
  with self.sf() as s:
   q=select(PaymentIntentRow).where(PaymentIntentRow.status==PaymentStatus.PENDING.value)
   if provider:q=q.where(PaymentIntentRow.provider==provider)
   return tuple(self._i(r) for r in s.scalars(q.order_by(PaymentIntentRow.created_at)).all())

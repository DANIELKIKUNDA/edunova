from dataclasses import replace
from uuid import uuid4
from app.modules.campus.domain.model import CampusRole,UnitKind
from app.modules.student_finance.domain.model import *
FINANCE_WRITE={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN}
FINANCE_READ=FINANCE_WRITE|{CampusRole.ACADEMIC_ADMIN,CampusRole.AUDITOR}
class StudentFinanceService:
 def __init__(self,repo,campus,campus_repo,student_repo,now,audit=None):self.repo=repo;self.campus=campus;self.campus_repo=campus_repo;self.student_repo=student_repo;self.now=now;self.audit=audit
 def _auth(self,a,i,write=True):return self.campus.membership(a,i,FINANCE_WRITE if write else FINANCE_READ)
 def _student(self,i,sid):
  x=self.student_repo.get(sid)
  if not x or x.institution_id!=i:raise ValueError('finance_student_not_found')
  return x
 def _audit(self,a,action,eid,meta=None):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type='student_finance',entity_id=eid,metadata=meta or {})
 def create_schedule(self,a,i,program_unit_id,academic_year_id,name,currency='CDF'):
  self._auth(a,i);u=self.campus_repo.unit(i,program_unit_id);y=self.campus_repo.period(i,academic_year_id)
  if not u or u.kind!=UnitKind.PROGRAM or not y or not y.active:raise ValueError('finance_program_year_required')
  if currency not in {'CDF','USD'}:raise ValueError('finance_currency_unsupported')
  x=FeeSchedule(uuid4().hex,i,program_unit_id,academic_year_id,name.strip(),currency,ScheduleState.DRAFT,1,a,self.now(),None);self.repo.save_schedule(x);return x
 def add_fee(self,a,i,schedule_id,code,label,amount_minor,due_on=None,mandatory=True,installment_no=1):
  self._auth(a,i);s=self.repo.schedule(schedule_id)
  if not s or s.institution_id!=i:raise ValueError('finance_schedule_not_found')
  if s.state!=ScheduleState.DRAFT:raise ValueError('finance_published_schedule_immutable')
  if amount_minor<=0 or installment_no<1:raise ValueError('finance_invalid_fee')
  x=FeeItem(uuid4().hex,s.id,code.strip().upper(),label.strip(),amount_minor,due_on,mandatory,installment_no);self.repo.add_item(x);return x
 def publish(self,a,i,sid):
  self._auth(a,i);s=self.repo.schedule(sid)
  if not s or s.institution_id!=i:raise ValueError('finance_schedule_not_found')
  if not self.repo.items(sid):raise ValueError('finance_schedule_items_required')
  if s.state==ScheduleState.PUBLISHED:return s
  if s.state!=ScheduleState.DRAFT:raise ValueError('finance_schedule_not_publishable')
  x=replace(s,state=ScheduleState.PUBLISHED,row_version=s.row_version+1,published_at=self.now());self.repo.save_schedule(x);self._audit(a,'finance.schedule.published',x.id);return x
 def assess(self,a,i,sid,student_id,registration_id):
  self._auth(a,i);s=self.repo.schedule(sid);student=self._student(i,student_id);reg=self.student_repo.registration(student_id,s.academic_year_id) if s else None
  if not s or s.institution_id!=i or s.state!=ScheduleState.PUBLISHED:raise ValueError('finance_published_schedule_required')
  if student.program_unit_id!=s.program_unit_id or not reg or reg.id!=registration_id:raise ValueError('finance_registration_schedule_mismatch')
  existing={c.fee_item_id:c for c in self.repo.charges(student_id) if c.registration_id==registration_id};out=[]
  for f in self.repo.items(s.id):
   if f.id in existing:out.append(existing[f.id]);continue
   c=StudentCharge(uuid4().hex,i,student_id,registration_id,f.id,f.code,f.label,f.amount_minor,0,s.currency,f.due_on,ChargeState.OPEN,self.now());self.repo.add_charge(c);self.repo.add_ledger(LedgerEntry(uuid4().hex,i,student_id,TxKind.CHARGE,f.amount_minor,s.currency,'CHG-'+c.id,c.id,a,f.label,self.now()));out.append(c)
  return tuple(out)
 def statement(self,a,i,student_id):
  st=self._student(i,student_id);m=self.campus_repo.membership(i,a)
  if a!=st.account_id:self._auth(a,i,False)
  charges=self.repo.charges(student_id);ledger=self.repo.ledger(student_id);currencies=sorted({x.currency for x in ledger});balances={};debits_by={};credits_by={}
  for cur in currencies:
   debits_by[cur]=sum(x.amount_minor for x in ledger if x.currency==cur and x.kind in {TxKind.CHARGE,TxKind.REFUND});credits_by[cur]=sum(x.amount_minor for x in ledger if x.currency==cur and x.kind in {TxKind.PAYMENT,TxKind.SCHOLARSHIP,TxKind.DISCOUNT,TxKind.SPONSOR,TxKind.REVERSAL});balances[cur]=debits_by[cur]-credits_by[cur]
  single=currencies[0] if len(currencies)==1 else None;return {'student':st,'charges':charges,'ledger':ledger,'debits_minor':debits_by.get(single,0) if single else None,'credits_minor':credits_by.get(single,0) if single else None,'balance_minor':balances.get(single,0) if single else None,'balances_by_currency':balances}
 def payment(self,a,i,student_id,amount_minor,currency,method,external_reference=None,note=None,internal=False):
  if not internal:self._auth(a,i)
  self._student(i,student_id)
  if amount_minor<=0:raise ValueError('finance_invalid_payment_amount')
  if method=='cash':
   cs=self.repo.open_cash_session(i,a)
   if not cs or cs.currency!=currency:raise ValueError('finance_cash_session_required')
  old=self.repo.receipt_by_external(i,external_reference) if external_reference else None
  if old:
   if old.reversed:
    raise ValueError('finance_external_reference_reversed')
   # An external provider reference must never acknowledge a different payment.
   if (old.student_id,old.amount_minor,old.currency,old.payment_method)!=(student_id,amount_minor,currency,method):
    raise ValueError('finance_external_reference_conflict')
   return old
  open_charges=[c for c in self.repo.charges(student_id) if c.currency==currency and c.state!=ChargeState.PAID]
  if not open_charges:raise ValueError('finance_no_open_charges')
  outstanding=sum(c.amount_minor-c.paid_minor for c in open_charges)
  if amount_minor>outstanding:raise ValueError('finance_overpayment_requires_explicit_credit_policy')
  now=self.now();rid=uuid4().hex;r=FinanceReceipt(rid,i,student_id,'RCT-'+rid[:12].upper(),amount_minor,currency,method,external_reference,a,now,False);self.repo.add_receipt(r);remaining=amount_minor
  for c in open_charges:
   if remaining<=0:break
   alloc=min(remaining,c.amount_minor-c.paid_minor);self.repo.update_charge_paid(c.id,c.paid_minor+alloc);self.repo.add_ledger(LedgerEntry(uuid4().hex,i,student_id,TxKind.PAYMENT,alloc,currency,r.reference,c.id,a,note,now));remaining-=alloc
  self._audit(a,'finance.payment.posted',r.id,{'amount_minor':amount_minor,'currency':currency});return r
 def credit(self,a,i,student_id,amount_minor,currency,kind,reference,note):
  self._auth(a,i);self._student(i,student_id);k=TxKind(kind)
  if k not in {TxKind.SCHOLARSHIP,TxKind.DISCOUNT,TxKind.SPONSOR} or amount_minor<=0 or not note or not note.strip():raise ValueError('finance_invalid_credit')
  st=self.statement(a,i,student_id);bal=st['balances_by_currency'].get(currency,0)
  if amount_minor>bal:raise ValueError('finance_credit_exceeds_balance')
  e=LedgerEntry(uuid4().hex,i,student_id,k,amount_minor,currency,reference,None,a,note,self.now());self.repo.add_ledger(e);self._audit(a,'finance.credit.posted',e.id,{'kind':k.value});return e
 def refund(self,a,i,receipt_id,reason):
  self._auth(a,i);r=self.repo.receipt(receipt_id)
  if not r or r.institution_id!=i:raise ValueError('finance_receipt_not_found')
  if r.reversed:raise ValueError('finance_receipt_already_reversed')
  if not reason or not reason.strip():raise ValueError('finance_refund_reason_required')
  # Refund is append-only: original payment remains; offset entries reopen allocated charges.
  payments=[e for e in self.repo.ledger(r.student_id) if e.reference==r.reference and e.kind==TxKind.PAYMENT]
  for e in payments:
   c=next(x for x in self.repo.charges(r.student_id) if x.id==e.charge_id);self.repo.update_charge_paid(c.id,max(0,c.paid_minor-e.amount_minor));self.repo.add_ledger(LedgerEntry(uuid4().hex,i,r.student_id,TxKind.REFUND,e.amount_minor,r.currency,'RFND-'+r.reference,e.charge_id,a,reason,self.now()))
  self.repo.reverse_receipt(r.id);self._audit(a,'finance.refund.posted',r.id,{'reason':reason});return self.repo.receipt(r.id)

 # Phase 6 maximum-depth controls
 def open_cash(self,a,i,currency='CDF',opening_float_minor=0):
  self._auth(a,i)
  if currency not in {'CDF','USD'} or opening_float_minor<0:raise ValueError('finance_invalid_cash_opening')
  old=self.repo.open_cash_session(i,a)
  if old:raise ValueError('finance_cash_session_already_open')
  x=CashSession(uuid4().hex,i,a,currency,opening_float_minor,CashState.OPEN,self.now(),None,None,None,None,None);self.repo.add_cash_session(x);self._audit(a,'finance.cash.opened',x.id);return x
 def close_cash(self,a,i,counted_minor,note=None):
  self._auth(a,i);x=self.repo.open_cash_session(i,a)
  if not x:raise ValueError('finance_cash_session_not_open')
  if counted_minor<0:raise ValueError('finance_invalid_cash_count')
  now=self.now();cash=sum(r.amount_minor for r in self.repo.cash_receipts(i,a,x.opened_at,now));expected=x.opening_float_minor+cash;variance=counted_minor-expected
  if variance and (not note or not note.strip()):raise ValueError('finance_cash_variance_reason_required')
  y=replace(x,state=CashState.CLOSED,closed_at=now,expected_minor=expected,counted_minor=counted_minor,variance_minor=variance,close_note=note);self.repo.save_cash_session(y);self._audit(a,'finance.cash.closed',y.id,{'variance_minor':variance});return y
 def create_sponsor(self,a,i,name,reference,currency,ceiling_minor,valid_from,valid_until):
  self._auth(a,i)
  if ceiling_minor<=0 or valid_until<valid_from or currency not in {'CDF','USD'}:raise ValueError('finance_invalid_sponsor_agreement')
  x=SponsorAgreement(uuid4().hex,i,name.strip(),reference.strip(),currency,ceiling_minor,0,valid_from,valid_until,SponsorState.ACTIVE,a,self.now());self.repo.add_sponsor(x);self._audit(a,'finance.sponsor.created',x.id);return x
 def sponsor_student(self,a,i,agreement_id,student_id,amount_minor,note):
  self._auth(a,i);self._student(i,student_id);x=self.repo.sponsor(agreement_id);today=self.now().date()
  if not x or x.institution_id!=i or x.state!=SponsorState.ACTIVE:raise ValueError('finance_sponsor_not_active')
  if today<x.valid_from or today>x.valid_until:raise ValueError('finance_sponsor_outside_validity')
  if amount_minor<=0 or x.used_minor+amount_minor>x.ceiling_minor:raise ValueError('finance_sponsor_ceiling_exceeded')
  if not note or not note.strip():raise ValueError('finance_sponsor_reason_required')
  st=self.statement(a,i,student_id);bal=st['balances_by_currency'].get(x.currency,0)
  if amount_minor>bal:raise ValueError('finance_credit_exceeds_balance')
  e=LedgerEntry(uuid4().hex,i,student_id,TxKind.SPONSOR,amount_minor,x.currency,x.reference,None,a,note,self.now());self.repo.add_ledger(e);self.repo.save_sponsor(replace(x,used_minor=x.used_minor+amount_minor));self._audit(a,'finance.sponsor.applied',e.id);return e
 def create_payment_plan(self,a,i,student_id,registration_id,name,reason,lines):
  self._auth(a,i);self._student(i,student_id);reg=self.student_repo.registration(student_id,None) if False else None
  if self.repo.plan_for_registration(registration_id):raise ValueError('finance_payment_plan_exists')
  if not reason or not reason.strip() or not lines:raise ValueError('finance_payment_plan_invalid')
  charges=[c for c in self.repo.charges(student_id) if c.registration_id==registration_id and c.state!=ChargeState.PAID];outstanding=sum(c.amount_minor-c.paid_minor for c in charges)
  normalized=[];seen=set();total=0;last=None
  for n,amt,due in lines:
   if n<1 or n in seen or amt<=0 or (last and due<last):raise ValueError('finance_payment_plan_invalid')
   seen.add(n);last=due;total+=amt;normalized.append(PaymentPlanLine(uuid4().hex,'',n,amt,due))
  if total!=outstanding:raise ValueError('finance_payment_plan_total_mismatch')
  p=PaymentPlan(uuid4().hex,i,student_id,registration_id,name.strip(),a,reason.strip(),self.now());normalized=[replace(x,plan_id=p.id) for x in normalized];self.repo.add_plan(p,normalized);self._audit(a,'finance.payment_plan.created',p.id);return p,tuple(normalized)
 def aging(self,a,i,student_id):
  self._auth(a,i,False);self._student(i,student_id);today=self.now().date();b={'current':0,'1_30':0,'31_60':0,'61_90':0,'90_plus':0}
  for c in self.repo.charges(student_id):
   rem=c.amount_minor-c.paid_minor
   if rem<=0:continue
   days=(today-c.due_on).days if c.due_on else 0
   k='current' if days<=0 else '1_30' if days<=30 else '31_60' if days<=60 else '61_90' if days<=90 else '90_plus';b[k]+=rem
  return b

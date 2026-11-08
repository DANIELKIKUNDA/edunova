from sqlalchemy import String,Integer,DateTime,Date,Boolean,UniqueConstraint,select,func
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.student_finance.domain.model import *
class FeeScheduleRow(Base):
 __tablename__='student_fee_schedules';__table_args__=(UniqueConstraint('institution_id','program_unit_id','academic_year_id','name',name='uq_fee_schedule_scope'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);program_unit_id:Mapped[str]=mapped_column(String(64),index=True);academic_year_id:Mapped[str]=mapped_column(String(64),index=True);name:Mapped[str]=mapped_column(String(160));currency:Mapped[str]=mapped_column(String(8));state:Mapped[str]=mapped_column(String(20),index=True);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));published_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
class FeeItemRow(Base):
 __tablename__='student_fee_items';__table_args__=(UniqueConstraint('schedule_id','code',name='uq_fee_item_code'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);schedule_id:Mapped[str]=mapped_column(String(64),index=True);code:Mapped[str]=mapped_column(String(64));label:Mapped[str]=mapped_column(String(240));amount_minor:Mapped[int]=mapped_column(Integer);due_on:Mapped[object|None]=mapped_column(Date,nullable=True);mandatory:Mapped[bool]=mapped_column(Boolean);installment_no:Mapped[int]=mapped_column(Integer)
class StudentChargeRow(Base):
 __tablename__='student_finance_charges';__table_args__=(UniqueConstraint('registration_id','fee_item_id',name='uq_registration_fee_charge'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);student_id:Mapped[str]=mapped_column(String(64),index=True);registration_id:Mapped[str]=mapped_column(String(64),index=True);fee_item_id:Mapped[str]=mapped_column(String(64));code:Mapped[str]=mapped_column(String(64));label:Mapped[str]=mapped_column(String(240));amount_minor:Mapped[int]=mapped_column(Integer);paid_minor:Mapped[int]=mapped_column(Integer);currency:Mapped[str]=mapped_column(String(8));due_on:Mapped[object|None]=mapped_column(Date,nullable=True);state:Mapped[str]=mapped_column(String(20),index=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class FinanceLedgerRow(Base):
 __tablename__='student_finance_ledger';__table_args__=(UniqueConstraint('institution_id','reference','charge_id','kind',name='uq_finance_reference'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);student_id:Mapped[str]=mapped_column(String(64),index=True);kind:Mapped[str]=mapped_column(String(20),index=True);amount_minor:Mapped[int]=mapped_column(Integer);currency:Mapped[str]=mapped_column(String(8));reference:Mapped[str]=mapped_column(String(120));charge_id:Mapped[str|None]=mapped_column(String(64),nullable=True);actor_id:Mapped[str]=mapped_column(String(64));note:Mapped[str|None]=mapped_column(String(1000),nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class FinanceReceiptRow(Base):
 __tablename__='student_finance_receipts';__table_args__=(UniqueConstraint('institution_id','reference',name='uq_finance_receipt_ref'),UniqueConstraint('institution_id','external_reference',name='uq_finance_external_ref'))
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);student_id:Mapped[str]=mapped_column(String(64),index=True);reference:Mapped[str]=mapped_column(String(120));amount_minor:Mapped[int]=mapped_column(Integer);currency:Mapped[str]=mapped_column(String(8));payment_method:Mapped[str]=mapped_column(String(32));external_reference:Mapped[str|None]=mapped_column(String(160),nullable=True);issued_by:Mapped[str]=mapped_column(String(64));issued_at:Mapped[object]=mapped_column(DateTime(timezone=True));reversed:Mapped[bool]=mapped_column(Boolean,default=False)
class SqlStudentFinanceRepository:
 def __init__(self,sf):self.sf=sf
 def schedule(self,x):
  with self.sf() as s:r=s.get(FeeScheduleRow,x);return FeeSchedule(r.id,r.institution_id,r.program_unit_id,r.academic_year_id,r.name,r.currency,ScheduleState(r.state),r.row_version,r.created_by,r.created_at,r.published_at) if r else None
 def save_schedule(self,x):
  with self.sf() as s:
   r=s.get(FeeScheduleRow,x.id);d=x.__dict__.copy();d['state']=x.state.value
   if not r:s.add(FeeScheduleRow(**d))
   else:
    for k,v in d.items():setattr(r,k,v)
   s.commit()
 def items(self,sid):
  with self.sf() as s:return tuple(FeeItem(r.id,r.schedule_id,r.code,r.label,r.amount_minor,r.due_on,r.mandatory,r.installment_no) for r in s.scalars(select(FeeItemRow).where(FeeItemRow.schedule_id==sid).order_by(FeeItemRow.installment_no,FeeItemRow.code)).all())
 def add_item(self,x):
  with self.sf() as s:s.add(FeeItemRow(**x.__dict__));s.commit()
 def charges(self,student_id):
  with self.sf() as s:return tuple(StudentCharge(r.id,r.institution_id,r.student_id,r.registration_id,r.fee_item_id,r.code,r.label,r.amount_minor,r.paid_minor,r.currency,r.due_on,ChargeState(r.state),r.created_at) for r in s.scalars(select(StudentChargeRow).where(StudentChargeRow.student_id==student_id).order_by(StudentChargeRow.due_on,StudentChargeRow.created_at)).all())
 def add_charge(self,x):
  with self.sf() as s:s.add(StudentChargeRow(**{**x.__dict__,'state':x.state.value}));s.commit()
 def update_charge_paid(self,cid,paid):
  with self.sf() as s:r=s.get(StudentChargeRow,cid);r.paid_minor=paid;r.state=(ChargeState.PAID if paid>=r.amount_minor else ChargeState.PARTIAL if paid else ChargeState.OPEN).value;s.commit()
 def ledger(self,student_id):
  with self.sf() as s:return tuple(LedgerEntry(r.id,r.institution_id,r.student_id,TxKind(r.kind),r.amount_minor,r.currency,r.reference,r.charge_id,r.actor_id,r.note,r.created_at) for r in s.scalars(select(FinanceLedgerRow).where(FinanceLedgerRow.student_id==student_id).order_by(FinanceLedgerRow.created_at,FinanceLedgerRow.id)).all())
 def add_ledger(self,x):
  with self.sf() as s:s.add(FinanceLedgerRow(**{**x.__dict__,'kind':x.kind.value}));s.commit()
 def receipt_by_external(self,i,ref):
  if not ref:return None
  with self.sf() as s:r=s.scalar(select(FinanceReceiptRow).where(FinanceReceiptRow.institution_id==i,FinanceReceiptRow.external_reference==ref));return self._receipt(r) if r else None
 def receipt(self,rid):
  with self.sf() as s:r=s.get(FinanceReceiptRow,rid);return self._receipt(r) if r else None
 def _receipt(self,r):return FinanceReceipt(r.id,r.institution_id,r.student_id,r.reference,r.amount_minor,r.currency,r.payment_method,r.external_reference,r.issued_by,r.issued_at,r.reversed)
 def add_receipt(self,x):
  with self.sf() as s:s.add(FinanceReceiptRow(**x.__dict__));s.commit()
 def reverse_receipt(self,rid):
  with self.sf() as s:r=s.get(FinanceReceiptRow,rid);r.reversed=True;s.commit()
class CashSessionRow(Base):
 __tablename__='student_finance_cash_sessions'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);cashier_id:Mapped[str]=mapped_column(String(64),index=True);currency:Mapped[str]=mapped_column(String(8));opening_float_minor:Mapped[int]=mapped_column(Integer);state:Mapped[str]=mapped_column(String(20),index=True);opened_at:Mapped[object]=mapped_column(DateTime(timezone=True));closed_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True);expected_minor:Mapped[int|None]=mapped_column(Integer,nullable=True);counted_minor:Mapped[int|None]=mapped_column(Integer,nullable=True);variance_minor:Mapped[int|None]=mapped_column(Integer,nullable=True);close_note:Mapped[str|None]=mapped_column(String(1000),nullable=True)
class SponsorAgreementRow(Base):
 __tablename__='student_finance_sponsor_agreements';__table_args__=(UniqueConstraint('institution_id','reference',name='uq_sponsor_agreement_ref'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);name:Mapped[str]=mapped_column(String(200));reference:Mapped[str]=mapped_column(String(100));currency:Mapped[str]=mapped_column(String(8));ceiling_minor:Mapped[int]=mapped_column(Integer);used_minor:Mapped[int]=mapped_column(Integer);valid_from:Mapped[object]=mapped_column(Date);valid_until:Mapped[object]=mapped_column(Date);state:Mapped[str]=mapped_column(String(20),index=True);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class PaymentPlanRow(Base):
 __tablename__='student_finance_payment_plans';__table_args__=(UniqueConstraint('registration_id',name='uq_registration_payment_plan'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);student_id:Mapped[str]=mapped_column(String(64),index=True);registration_id:Mapped[str]=mapped_column(String(64),index=True);name:Mapped[str]=mapped_column(String(160));approved_by:Mapped[str]=mapped_column(String(64));reason:Mapped[str]=mapped_column(String(1000));created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class PaymentPlanLineRow(Base):
 __tablename__='student_finance_payment_plan_lines';__table_args__=(UniqueConstraint('plan_id','sequence_no',name='uq_payment_plan_line'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);plan_id:Mapped[str]=mapped_column(String(64),index=True);sequence_no:Mapped[int]=mapped_column(Integer);amount_minor:Mapped[int]=mapped_column(Integer);due_on:Mapped[object]=mapped_column(Date)

def _cash(r): return CashSession(r.id,r.institution_id,r.cashier_id,r.currency,r.opening_float_minor,CashState(r.state),r.opened_at,r.closed_at,r.expected_minor,r.counted_minor,r.variance_minor,r.close_note)
def _sponsor(r): return SponsorAgreement(r.id,r.institution_id,r.name,r.reference,r.currency,r.ceiling_minor,r.used_minor,r.valid_from,r.valid_until,SponsorState(r.state),r.created_by,r.created_at)
def _plan(r): return PaymentPlan(r.id,r.institution_id,r.student_id,r.registration_id,r.name,r.approved_by,r.reason,r.created_at)
def _line(r): return PaymentPlanLine(r.id,r.plan_id,r.sequence_no,r.amount_minor,r.due_on)
SqlStudentFinanceRepository.open_cash_session=lambda self,i,a: (lambda r:_cash(r) if r else None)(self._scalar(select(CashSessionRow).where(CashSessionRow.institution_id==i,CashSessionRow.cashier_id==a,CashSessionRow.state==CashState.OPEN.value)))
def _scalar(self,q):
 with self.sf() as s:return s.scalar(q)
SqlStudentFinanceRepository._scalar=_scalar
def _add_cash(self,x):
 with self.sf() as s:s.add(CashSessionRow(**{**x.__dict__,'state':x.state.value}));s.commit()
SqlStudentFinanceRepository.add_cash_session=_add_cash
def _close_cash(self,x):
 with self.sf() as s:r=s.get(CashSessionRow,x.id);[setattr(r,k,(v.value if hasattr(v,'value') else v)) for k,v in x.__dict__.items()];s.commit()
SqlStudentFinanceRepository.save_cash_session=_close_cash
def _cash_receipts(self,i,a,start,end):
 with self.sf() as s:return tuple(self._receipt(r) for r in s.scalars(select(FinanceReceiptRow).where(FinanceReceiptRow.institution_id==i,FinanceReceiptRow.issued_by==a,FinanceReceiptRow.issued_at>=start,FinanceReceiptRow.issued_at<=end,FinanceReceiptRow.payment_method=='cash',FinanceReceiptRow.reversed==False)).all())
SqlStudentFinanceRepository.cash_receipts=_cash_receipts
def _add_sponsor(self,x):
 with self.sf() as s:s.add(SponsorAgreementRow(**{**x.__dict__,'state':x.state.value}));s.commit()
SqlStudentFinanceRepository.add_sponsor=_add_sponsor
def _sponsor_get(self,x):
 with self.sf() as s:r=s.get(SponsorAgreementRow,x);return _sponsor(r) if r else None
SqlStudentFinanceRepository.sponsor=_sponsor_get
def _save_sponsor(self,x):
 with self.sf() as s:r=s.get(SponsorAgreementRow,x.id);[setattr(r,k,(v.value if hasattr(v,'value') else v)) for k,v in x.__dict__.items()];s.commit()
SqlStudentFinanceRepository.save_sponsor=_save_sponsor
def _add_plan(self,p,lines):
 with self.sf() as s:s.add(PaymentPlanRow(**p.__dict__));[s.add(PaymentPlanLineRow(**x.__dict__)) for x in lines];s.commit()
SqlStudentFinanceRepository.add_plan=_add_plan
def _plan_for_reg(self,rid):
 with self.sf() as s:r=s.scalar(select(PaymentPlanRow).where(PaymentPlanRow.registration_id==rid));return _plan(r) if r else None
SqlStudentFinanceRepository.plan_for_registration=_plan_for_reg
def _plan_lines(self,pid):
 with self.sf() as s:return tuple(_line(r) for r in s.scalars(select(PaymentPlanLineRow).where(PaymentPlanLineRow.plan_id==pid).order_by(PaymentPlanLineRow.sequence_no)).all())
SqlStudentFinanceRepository.plan_lines=_plan_lines


def _post_payment_atomic(self, receipt, note, session=None):
    """Post receipt, charge allocations and ledger in one database transaction.

    PostgreSQL row locks serialize payments for the same student's charges.
    The receipt unique constraint resolves concurrent external-reference claims.
    """
    from uuid import uuid4
    from contextlib import nullcontext
    session_context = nullcontext(session) if session is not None else self.sf()
    with session_context as s:
        transaction_context = nullcontext() if session is not None else s.begin()
        with transaction_context:
            # Serialize against other payments for this student, even if they use
            # distinct provider references. Lock all charges in stable ID order.
            charges = s.scalars(
                select(StudentChargeRow)
                .where(
                    StudentChargeRow.institution_id == receipt.institution_id,
                    StudentChargeRow.student_id == receipt.student_id,
                    StudentChargeRow.currency == receipt.currency,
                )
                .order_by(StudentChargeRow.id)
                .with_for_update()
            ).all()
            if receipt.external_reference:
                existing = s.scalar(
                    select(FinanceReceiptRow).where(
                        FinanceReceiptRow.institution_id == receipt.institution_id,
                        FinanceReceiptRow.external_reference == receipt.external_reference,
                    )
                )
                if existing:
                    if existing.reversed:
                        raise ValueError("finance_external_reference_reversed")
                    if (
                        existing.student_id,
                        existing.amount_minor,
                        existing.currency,
                        existing.payment_method,
                    ) != (
                        receipt.student_id,
                        receipt.amount_minor,
                        receipt.currency,
                        receipt.payment_method,
                    ):
                        raise ValueError("finance_external_reference_conflict")
                    return self._receipt(existing)
            open_charges = [
                c for c in charges
                if c.state in {ChargeState.OPEN.value, ChargeState.PARTIAL.value}
                and c.amount_minor > c.paid_minor
            ]
            # Lock in stable ID order, then allocate by financial due date.
            # UUID order must not decide which installment gets paid first.
            from datetime import date
            open_charges.sort(key=lambda c: (
                c.due_on is None, c.due_on or date.max, c.created_at, c.id,
            ))
            outstanding = sum(c.amount_minor - c.paid_minor for c in open_charges)
            if not open_charges:
                raise ValueError("finance_no_open_charges")
            if receipt.amount_minor > outstanding:
                raise ValueError("finance_overpayment_requires_explicit_credit_policy")
            s.add(FinanceReceiptRow(**receipt.__dict__))
            remaining = receipt.amount_minor
            for charge in open_charges:
                if remaining <= 0:
                    break
                allocation = min(remaining, charge.amount_minor - charge.paid_minor)
                charge.paid_minor += allocation
                charge.state = (
                    ChargeState.PAID.value
                    if charge.paid_minor >= charge.amount_minor
                    else ChargeState.PARTIAL.value
                )
                s.add(FinanceLedgerRow(
                    id=uuid4().hex,
                    institution_id=receipt.institution_id,
                    student_id=receipt.student_id,
                    kind=TxKind.PAYMENT.value,
                    amount_minor=allocation,
                    currency=receipt.currency,
                    reference=receipt.reference,
                    charge_id=charge.id,
                    actor_id=receipt.issued_by,
                    note=note,
                    created_at=receipt.issued_at,
                ))
                remaining -= allocation
            if remaining:
                raise ValueError("finance_allocation_incomplete")
    return receipt


SqlStudentFinanceRepository.post_payment_atomic = _post_payment_atomic

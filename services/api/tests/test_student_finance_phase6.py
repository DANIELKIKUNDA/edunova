import pytest
from datetime import date
from app.runtime import runtime
from test_student_records_phase5 import admitted_student

def finance_student(seed='fin'):
 admin,inst,app,r,co,student=admitted_student(seed);reg=runtime.student_record_repo.registrations(student.id)[0]
 sched=runtime.student_finance.create_schedule(admin,inst.id,student.program_unit_id,reg.academic_year_id,'Barème '+seed,'CDF')
 runtime.student_finance.add_fee(admin,inst.id,sched.id,'INS','Frais inscription',100000,due_on=date(2027,9,15),installment_no=1)
 runtime.student_finance.add_fee(admin,inst.id,sched.id,'MIN1','Minerval tranche 1',200000,due_on=date(2027,10,15),installment_no=2)
 sched=runtime.student_finance.publish(admin,inst.id,sched.id);charges=runtime.student_finance.assess(admin,inst.id,sched.id,student.id,reg.id)
 return admin,inst,app,student,reg,sched,charges

def test_fee_schedule_is_immutable_and_assessment_idempotent():
 a,i,app,s,r,sch,charges=finance_student('schedule');assert len(charges)==2 and sum(x.amount_minor for x in charges)==300000
 assert len(runtime.student_finance.assess(a,i.id,sch.id,s.id,r.id))==2
 with pytest.raises(ValueError,match='immutable'):runtime.student_finance.add_fee(a,i.id,sch.id,'X','Late',1)

def test_cash_payment_allocates_oldest_charge_and_receipt_is_idempotent():
 a,i,app,s,r,sch,c=finance_student('pay');runtime.student_finance.open_cash(a,i.id,'CDF',0);receipt=runtime.student_finance.payment(a,i.id,s.id,150000,'CDF','cash','CASH-001','Guichet central')
 same=runtime.student_finance.payment(a,i.id,s.id,150000,'CDF','cash','CASH-001','retry');assert same.id==receipt.id
 st=runtime.student_finance.statement(a,i.id,s.id);assert st['balance_minor']==150000
 cc=runtime.student_finance_repo.charges(s.id);assert cc[0].state.value=='paid' and cc[1].paid_minor==50000

def test_student_can_read_own_statement_but_other_student_cannot():
 a,i,app,s,r,sch,c=finance_student('privacyfin');assert runtime.student_finance.statement(app.account_id,i.id,s.id)['balance_minor']==300000
 _,i2,app2,s2,*_=finance_student('privacyfin2')
 with pytest.raises((ValueError,PermissionError)):runtime.student_finance.statement(app.account_id,i2.id,s2.id)

def test_scholarship_requires_reason_and_cannot_exceed_debt():
 a,i,app,s,r,sch,c=finance_student('scholar');e=runtime.student_finance.credit(a,i.id,s.id,50000,'CDF','scholarship','SCH-2027-1','Bourse mérite');assert e.kind.value=='scholarship';assert runtime.student_finance.statement(a,i.id,s.id)['balance_minor']==250000
 with pytest.raises(ValueError):runtime.student_finance.credit(a,i.id,s.id,300000,'CDF','discount','BAD','x')

def test_refund_is_append_only_and_reopens_receivable():
 a,i,app,s,r,sch,c=finance_student('refund');runtime.student_finance.open_cash(a,i.id,'CDF',0);receipt=runtime.student_finance.payment(a,i.id,s.id,100000,'CDF','cash','CASH-R','paid');assert runtime.student_finance.statement(a,i.id,s.id)['balance_minor']==200000
 rr=runtime.student_finance.refund(a,i.id,receipt.id,'Payment entered on wrong account');assert rr.reversed
 assert runtime.student_finance.statement(a,i.id,s.id)['balance_minor']==300000
 with pytest.raises(ValueError,match='already_reversed'):runtime.student_finance.refund(a,i.id,receipt.id,'again')

def test_no_overpayment_without_explicit_credit_policy():
 a,i,app,s,r,sch,c=finance_student('overpay');runtime.student_finance.open_cash(a,i.id,'CDF',0)
 with pytest.raises(ValueError,match='overpayment'):runtime.student_finance.payment(a,i.id,s.id,300001,'CDF','cash','OVER')

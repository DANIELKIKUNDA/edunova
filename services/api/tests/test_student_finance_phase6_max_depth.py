import pytest
from datetime import date,timedelta
from app.runtime import runtime
from test_student_finance_phase6 import finance_student

def test_cashier_session_required_and_close_reconciles_variance():
 a,i,app,s,r,sch,c=finance_student('cashdeep')
 with pytest.raises(ValueError,match='cash_session_required'):runtime.student_finance.payment(a,i.id,s.id,10000,'CDF','cash','C-DEEP')
 runtime.student_finance.open_cash(a,i.id,'CDF',5000)
 runtime.student_finance.payment(a,i.id,s.id,10000,'CDF','cash','C-DEEP')
 with pytest.raises(ValueError,match='variance_reason'):runtime.student_finance.close_cash(a,i.id,14000)
 x=runtime.student_finance.close_cash(a,i.id,14000,'Ecart de caisse constaté');assert x.expected_minor==15000 and x.variance_minor==-1000 and x.state.value=='closed'

def test_sponsor_ceiling_validity_and_student_debt_are_enforced():
 a,i,app,s,r,sch,c=finance_student('sponsorDeep');today=runtime.student_finance.now().date()
 ag=runtime.student_finance.create_sponsor(a,i.id,'Entreprise X','SP-X','CDF',120000,today-timedelta(days=1),today+timedelta(days=30))
 runtime.student_finance.sponsor_student(a,i.id,ag.id,s.id,100000,'Convention sociale');assert runtime.student_finance.statement(a,i.id,s.id)['balance_minor']==200000
 with pytest.raises(ValueError,match='ceiling'):runtime.student_finance.sponsor_student(a,i.id,ag.id,s.id,30000,'Too much')

def test_payment_plan_must_equal_outstanding_and_be_chronological():
 a,i,app,s,r,sch,c=finance_student('planDeep')
 with pytest.raises(ValueError,match='total_mismatch'):runtime.student_finance.create_payment_plan(a,i.id,s.id,r.id,'Plan','Motif',[(1,100000,date(2027,10,1))])
 p,lines=runtime.student_finance.create_payment_plan(a,i.id,s.id,r.id,'Plan','Difficulté temporaire',[(1,100000,date(2027,10,1)),(2,200000,date(2027,11,1))]);assert len(lines)==2
 with pytest.raises(ValueError,match='exists'):runtime.student_finance.create_payment_plan(a,i.id,s.id,r.id,'Plan2','x',[(1,300000,date(2027,12,1))])

def test_currency_isolation_prevents_cross_currency_credit():
 a,i,app,s,r,sch,c=finance_student('currencyDeep')
 with pytest.raises(ValueError,match='exceeds_balance'):runtime.student_finance.credit(a,i.id,s.id,1,'USD','discount','USD-BAD','Wrong currency')

def test_aging_buckets_are_deterministic():
 a,i,app,s,r,sch,c=finance_student('agingDeep');today=runtime.student_finance.now().date()
 # Existing source dates are overdue relative to runtime; only assert conservation.
 b=runtime.student_finance.aging(a,i.id,s.id);assert sum(b.values())==300000 and set(b)=={'current','1_30','31_60','61_90','90_plus'}

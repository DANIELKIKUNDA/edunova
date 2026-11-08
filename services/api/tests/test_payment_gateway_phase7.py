import pytest
from app.runtime import runtime
from test_student_finance_phase6 import finance_student

def setup(seed):
 a,i,app,s,r,sch,c=finance_student(seed);return a,i,app,s

def cb(intent,status='succeeded',event='evt1',ref='provider-1'):
 payload={'status':status,'provider_reference':ref};envelope={'event_id':event,'intent_id':intent.id,'status':status,'provider_reference':ref,'payload':payload};sig=runtime.payment_gateway.sign_sandbox(__import__('json').dumps(envelope,sort_keys=True,separators=(',',':')).encode())
 return runtime.payment_gateway.callback('sandbox',event,intent.id,status,ref,payload,sig)

def test_intent_idempotency_and_conflict():
 a,i,app,s=setup('pg-idem');x=runtime.payment_gateway.initiate(app.account_id,i.id,s.id,100000,'CDF','sandbox','+243990000001','key1');y=runtime.payment_gateway.initiate(app.account_id,i.id,s.id,100000,'CDF','sandbox','+243990000001','key1');assert x.id==y.id
 with pytest.raises(ValueError,match='conflict'):runtime.payment_gateway.initiate(app.account_id,i.id,s.id,50000,'CDF','sandbox','+243990000001','key1')

def test_pending_does_not_credit_success_credits_once():
 a,i,app,s=setup('pg-success');x=runtime.payment_gateway.initiate(app.account_id,i.id,s.id,100000,'CDF','sandbox','+243990000002','k2');assert runtime.student_finance.statement(app.account_id,i.id,s.id)['balance_minor']==300000
 y=cb(x);assert y.status.value=='succeeded' and y.receipt_id;assert runtime.student_finance.statement(app.account_id,i.id,s.id)['balance_minor']==200000
 z=cb(x,event='evt2');assert z.receipt_id==y.receipt_id;assert runtime.student_finance.statement(app.account_id,i.id,s.id)['balance_minor']==200000

def test_invalid_signature_and_terminal_conflict():
 a,i,app,s=setup('pg-sec');x=runtime.payment_gateway.initiate(app.account_id,i.id,s.id,100000,'CDF','sandbox','+243990000003','k3')
 with pytest.raises(PermissionError):runtime.payment_gateway.callback('sandbox','bad',x.id,'succeeded','r',{'x':1},'bad')
 y=cb(x,'failed','fail','r2');assert y.status.value=='failed'
 with pytest.raises(ValueError,match='terminal'):cb(x,'succeeded','late','r3')

def test_expiration_never_credits():
 a,i,app,s=setup('pg-exp');x=runtime.payment_gateway.initiate(app.account_id,i.id,s.id,50000,'CDF','sandbox','+243990000004','k4');from dataclasses import replace;from datetime import timedelta
 runtime.payment_gateway_repo.save(replace(x,expires_at=runtime.payment_gateway.now()-timedelta(seconds=1)));y=runtime.payment_gateway.expire(x.id);assert y.status.value=='expired';assert runtime.student_finance.statement(app.account_id,i.id,s.id)['balance_minor']==300000

def test_provider_event_replay_payload_conflict_is_rejected():
 a,i,app,s=setup('pg-replay');x=runtime.payment_gateway.initiate(app.account_id,i.id,s.id,50000,'CDF','sandbox','+243990000005','k5');cb(x,'failed','same-event','r5')
 payload={'status':'failed','provider_reference':'tampered','x':1};envelope={'event_id':'same-event','intent_id':x.id,'status':'failed','provider_reference':'tampered','payload':payload};sig=runtime.payment_gateway.sign_sandbox(__import__('json').dumps(envelope,sort_keys=True,separators=(',',':')).encode())
 with pytest.raises(PermissionError,match='replay_conflict'):runtime.payment_gateway.callback('sandbox','same-event',x.id,'failed','tampered',payload,sig)

def test_poll_evidence_never_credits_without_authenticated_callback():
 a,i,app,s=setup('pg-poll');x=runtime.payment_gateway.initiate(app.account_id,i.id,s.id,50000,'CDF','sandbox','+243990000006','k6');at=runtime.payment_gateway.record_poll(a,i.id,x.id,'succeeded','p6','provider query says paid');assert at.outcome=='succeeded';assert runtime.payment_gateway_repo.get(x.id).status.value=='pending';assert runtime.student_finance.statement(app.account_id,i.id,s.id)['balance_minor']==300000

def test_reconciliation_detects_mismatch_and_match():
 a,i,app,s=setup('pg-rec');x=runtime.payment_gateway.initiate(app.account_id,i.id,s.id,50000,'CDF','sandbox','+243990000007','k7');r=runtime.payment_gateway.reconcile(a,i.id,x.id,'succeeded','p7','daily reconciliation');assert r.matched is False;cb(x,'succeeded','rec-success','p7');r2=runtime.payment_gateway.reconcile(a,i.id,x.id,'succeeded','p7');assert r2.matched is True

def test_pending_cancellation_is_audited_and_never_credits():
 a,i,app,s=setup('pg-cancel');x=runtime.payment_gateway.initiate(app.account_id,i.id,s.id,50000,'CDF','sandbox','+243990000008','k8');y=runtime.payment_gateway.cancel(app.account_id,i.id,x.id,'candidate abandoned checkout');assert y.status.value=='cancelled';assert runtime.student_finance.statement(app.account_id,i.id,s.id)['balance_minor']==300000
 with pytest.raises(ValueError,match='pending'):runtime.payment_gateway.cancel(app.account_id,i.id,x.id,'again')

from dataclasses import replace
from datetime import timedelta,UTC
from hashlib import sha256
from hmac import compare_digest,new as hmac_new
from json import dumps
from uuid import uuid4
from app.modules.payment_gateway.domain.model import *
class PaymentGatewayService:
 def __init__(self,repo,finance,student_repo,campus,now,audit=None,secrets=None):self.repo=repo;self.finance=finance;self.student_repo=student_repo;self.campus=campus;self.now=now;self.audit=audit;self.secrets=secrets or {'sandbox':'edunova-sandbox-secret'}
 def _audit(self,a,action,eid,meta=None):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type='payment_gateway',entity_id=eid,metadata=meta or {})
 def initiate(self,a,i,student_id,amount_minor,currency,provider,payer_msisdn,idempotency_key):
  st=self.student_repo.get(student_id)
  if not st or st.institution_id!=i:raise ValueError('payment_student_not_found')
  if a!=st.account_id:self.finance._auth(a,i)
  if amount_minor<=0 or currency not in {'CDF','USD'} or provider not in {'sandbox','orange_money','airtel_money'}:raise ValueError('payment_invalid_request')
  if not idempotency_key.strip() or not payer_msisdn.strip():raise ValueError('payment_idempotency_and_msisdn_required')
  old=self.repo.by_idempotency(i,idempotency_key)
  if old:
   if (old.student_id,old.amount_minor,old.currency,old.provider,old.payer_msisdn)!=(student_id,amount_minor,currency,provider,payer_msisdn):raise ValueError('payment_idempotency_conflict')
   return old
  balance=self.finance.statement(a,i,student_id)['balances_by_currency'].get(currency,0)
  if amount_minor>balance:raise ValueError('payment_exceeds_student_balance')
  now=self.now();pid=uuid4().hex;x=PaymentIntent(pid,i,student_id,amount_minor,currency,provider,payer_msisdn,idempotency_key,'PAY-'+pid[:16].upper(),None,PaymentStatus.PENDING,a,now,now,now+timedelta(minutes=30),None,None);self.repo.save(x);self._audit(a,'payment.initiated',x.id,{'provider':provider});return x
 def sign_sandbox(self,payload:bytes):return hmac_new(self.secrets['sandbox'].encode(),payload,'sha256').hexdigest()
 def callback(self,provider,event_id,intent_id,status,provider_reference,payload,signature):
  if provider not in self.secrets:raise PermissionError('payment_provider_not_configured')
  envelope={'event_id':event_id,'intent_id':intent_id,'status':status,'provider_reference':provider_reference,'payload':payload};raw=dumps(envelope,sort_keys=True,separators=(',',':')).encode();expected=hmac_new(self.secrets[provider].encode(),raw,'sha256').hexdigest()
  if not compare_digest(expected,signature):raise PermissionError('payment_callback_signature_invalid')
  old_event=self.repo.event(provider,event_id)
  if old_event:
   if old_event.payment_intent_id!=intent_id or old_event.payload_sha256!=sha256(raw).hexdigest():raise PermissionError('payment_provider_event_replay_conflict')
   return self.repo.get(intent_id)
  x=self.repo.get(intent_id)
  if not x or x.provider!=provider:raise ValueError('payment_intent_not_found')
  self.repo.add_event(ProviderEvent(uuid4().hex,provider,event_id,intent_id,provider_reference,status,sha256(raw).hexdigest(),self.now(),False))
  if x.status==PaymentStatus.SUCCEEDED:
   if status!='succeeded':raise ValueError('payment_terminal_status_conflict')
   self.repo.mark_event(provider,event_id);return x
  if x.status in {PaymentStatus.FAILED,PaymentStatus.EXPIRED,PaymentStatus.CANCELLED}:raise ValueError('payment_terminal_status_conflict')
  now=self.now();self.repo.add_attempt(PaymentAttempt(uuid4().hex,x.id,provider,'callback',self.repo.next_attempt_no(x.id),status,str(provider_reference or ''),now))
  if status=='succeeded':
   # Provider success is the only event allowed to create a finance receipt.
   receipt=self.finance.payment('provider:'+provider,x.institution_id,x.student_id,x.amount_minor,x.currency,'mobile_money',provider_reference or x.merchant_reference,'provider:'+provider,internal=True)
   x=replace(x,status=PaymentStatus.SUCCEEDED,provider_reference=provider_reference,receipt_id=receipt.id,updated_at=now)
  elif status=='failed':x=replace(x,status=PaymentStatus.FAILED,provider_reference=provider_reference,failure_code=str(payload.get('failure_code') or 'provider_failed'),updated_at=now)
  else:raise ValueError('payment_callback_status_invalid')
  self.repo.save(x);self.repo.mark_event(provider,event_id);self._audit('provider:'+provider,'payment.'+x.status.value,x.id);return x
 def expire(self,intent_id):
  x=self.repo.get(intent_id)
  if not x:raise ValueError('payment_intent_not_found')
  exp=x.expires_at if x.expires_at.tzinfo else x.expires_at.replace(tzinfo=UTC)
  if x.status==PaymentStatus.PENDING and self.now()>=exp:x=replace(x,status=PaymentStatus.EXPIRED,updated_at=self.now(),failure_code='expired');self.repo.save(x)
  return x

 def cancel(self,a,i,intent_id,reason):
  x=self.repo.get(intent_id)
  if x and a!=x.created_by:self.finance._auth(a,i)
  if not x or x.institution_id!=i:raise ValueError('payment_intent_not_found')
  if x.status!=PaymentStatus.PENDING:raise ValueError('payment_only_pending_cancellable')
  if not reason or not reason.strip():raise ValueError('payment_cancel_reason_required')
  y=replace(x,status=PaymentStatus.CANCELLED,updated_at=self.now(),failure_code='cancelled:'+reason.strip()[:80]);self.repo.save(y);self.repo.add_attempt(PaymentAttempt(uuid4().hex,x.id,x.provider,'cancel',self.repo.next_attempt_no(x.id),'cancelled',reason.strip()[:500],self.now()));self._audit(a,'payment.cancelled',x.id,{'reason':reason});return y
 def record_poll(self,a,i,intent_id,provider_status,provider_reference=None,detail=None):
  self.finance._auth(a,i);x=self.repo.get(intent_id)
  if not x or x.institution_id!=i:raise ValueError('payment_intent_not_found')
  if x.status!=PaymentStatus.PENDING:raise ValueError('payment_poll_terminal_intent')
  if provider_status not in {'pending','succeeded','failed','not_found'}:raise ValueError('payment_provider_status_invalid')
  at=PaymentAttempt(uuid4().hex,x.id,x.provider,'poll',self.repo.next_attempt_no(x.id),provider_status,(detail or '')[:500] or None,self.now());self.repo.add_attempt(at);self._audit(a,'payment.provider_polled',x.id,{'provider_status':provider_status})
  # A poll is evidence, not settlement authority. Success still requires authenticated provider callback.
  return at
 def reconcile(self,a,i,intent_id,provider_status,provider_reference=None,note=None):
  self.finance._auth(a,i);x=self.repo.get(intent_id)
  if not x or x.institution_id!=i:raise ValueError('payment_intent_not_found')
  if provider_status not in {'pending','succeeded','failed','expired','cancelled','not_found'}:raise ValueError('payment_provider_status_invalid')
  matched=(provider_status==x.status.value) or (provider_status=='not_found' and x.status in {PaymentStatus.FAILED,PaymentStatus.EXPIRED,PaymentStatus.CANCELLED})
  r=ReconciliationRecord(uuid4().hex,x.id,x.provider,provider_reference or x.provider_reference,provider_status,x.status.value,matched,(note or '')[:500] or None,a,self.now());self.repo.add_reconciliation(r);self._audit(a,'payment.reconciled',x.id,{'matched':matched,'provider_status':provider_status,'local_status':x.status.value});return r
 def operations(self,a,i,provider=None):
  self.finance._auth(a,i,False);xs=[x for x in self.repo.pending(provider) if x.institution_id==i];return tuple({'intent':x,'attempts':self.repo.attempts(x.id),'reconciliations':self.repo.reconciliations(x.id)} for x in xs)

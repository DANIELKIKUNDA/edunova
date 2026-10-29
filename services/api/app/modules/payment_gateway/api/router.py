from fastapi import APIRouter,Depends,HTTPException,Header
from pydantic import BaseModel
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
def w(f):
 try:return f()
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(422,str(e))
def obj(x):
 d=x.__dict__.copy()
 for k,v in list(d.items()):
  if hasattr(v,'value'):d[k]=v.value
  elif hasattr(v,'isoformat'):d[k]=v.isoformat()
 return d
class InitIn(BaseModel):student_id:str;amount_minor:int;currency:str='CDF';provider:str;payer_msisdn:str
@router.post('/institutions/{iid}/intents')
def initiate(iid:str,q:InitIn,idempotency_key:str=Header(alias='Idempotency-Key'),a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.payment_gateway.initiate(a.account_id,iid,**q.model_dump(),idempotency_key=idempotency_key)))
class CallbackIn(BaseModel):event_id:str;intent_id:str;status:str;provider_reference:str|None=None;payload:dict
@router.post('/callbacks/{provider}')
def callback(provider:str,q:CallbackIn,x_signature:str=Header(alias='X-EduNova-Payment-Signature')):return obj(w(lambda:runtime.payment_gateway.callback(provider,q.event_id,q.intent_id,q.status,q.provider_reference,q.payload,x_signature)))
class CancelIn(BaseModel):reason:str
@router.post('/institutions/{iid}/intents/{intent_id}/cancel')
def cancel(iid:str,intent_id:str,q:CancelIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.payment_gateway.cancel(a.account_id,iid,intent_id,q.reason)))
class PollIn(BaseModel):provider_status:str;provider_reference:str|None=None;detail:str|None=None
@router.post('/institutions/{iid}/intents/{intent_id}/provider-observation')
def provider_observation(iid:str,intent_id:str,q:PollIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.payment_gateway.record_poll(a.account_id,iid,intent_id,**q.model_dump())))
class ReconcileIn(BaseModel):provider_status:str;provider_reference:str|None=None;note:str|None=None
@router.post('/institutions/{iid}/intents/{intent_id}/reconcile')
def reconcile(iid:str,intent_id:str,q:ReconcileIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.payment_gateway.reconcile(a.account_id,iid,intent_id,**q.model_dump())))
@router.get('/institutions/{iid}/operations')
def operations(iid:str,provider:str|None=None,a:AuthContext=Depends(current_auth)):
 rows=w(lambda:runtime.payment_gateway.operations(a.account_id,iid,provider));return [{'intent':obj(x['intent']),'attempts':[obj(v) for v in x['attempts']],'reconciliations':[obj(v) for v in x['reconciliations']]} for x in rows]

from datetime import date
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
def w(f):
 try:return f()
 except (ValueError,PermissionError) as e:raise HTTPException(422 if isinstance(e,ValueError) else 403,str(e)) from e
def obj(x):
 d=x.__dict__.copy()
 for k,v in list(d.items()):
  if hasattr(v,'value'):d[k]=v.value
  elif hasattr(v,'isoformat'):d[k]=v.isoformat()
 return d
class ScheduleIn(BaseModel):program_unit_id:str;academic_year_id:str;name:str;currency:str='CDF'
class FeeIn(BaseModel):code:str;label:str;amount_minor:int;due_on:date|None=None;mandatory:bool=True;installment_no:int=1
class AssessIn(BaseModel):student_id:str;registration_id:str
class PaymentIn(BaseModel):student_id:str;amount_minor:int;currency:str='CDF';method:str='cash';external_reference:str|None=None;note:str|None=None
class CreditIn(BaseModel):student_id:str;amount_minor:int;currency:str='CDF';kind:str;reference:str;note:str
class RefundIn(BaseModel):reason:str
@router.post('/institutions/{iid}/schedules')
def create(iid:str,q:ScheduleIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.create_schedule(a.account_id,iid,**q.model_dump())))
@router.post('/institutions/{iid}/schedules/{sid}/items')
def fee(iid:str,sid:str,q:FeeIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.add_fee(a.account_id,iid,sid,**q.model_dump())))
@router.post('/institutions/{iid}/schedules/{sid}/publish')
def publish(iid:str,sid:str,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.publish(a.account_id,iid,sid)))
@router.post('/institutions/{iid}/schedules/{sid}/assess')
def assess(iid:str,sid:str,q:AssessIn,a:AuthContext=Depends(current_auth)):return [obj(x) for x in w(lambda:runtime.student_finance.assess(a.account_id,iid,sid,q.student_id,q.registration_id))]
@router.get('/institutions/{iid}/students/{student_id}/statement')
def statement(iid:str,student_id:str,a:AuthContext=Depends(current_auth)):
 d=w(lambda:runtime.student_finance.statement(a.account_id,iid,student_id));return {**d,'student':obj(d['student']),'charges':[obj(x) for x in d['charges']],'ledger':[obj(x) for x in d['ledger']]}
@router.post('/institutions/{iid}/payments')
def payment(iid:str,q:PaymentIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.payment(a.account_id,iid,**q.model_dump())))
@router.post('/institutions/{iid}/credits')
def credit(iid:str,q:CreditIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.credit(a.account_id,iid,**q.model_dump())))
@router.post('/institutions/{iid}/receipts/{rid}/refund')
def refund(iid:str,rid:str,q:RefundIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.refund(a.account_id,iid,rid,q.reason)))
class CashOpenIn(BaseModel):currency:str='CDF';opening_float_minor:int=0
class CashCloseIn(BaseModel):counted_minor:int;note:str|None=None
class SponsorIn(BaseModel):name:str;reference:str;currency:str='CDF';ceiling_minor:int;valid_from:date;valid_until:date
class SponsorApplyIn(BaseModel):student_id:str;amount_minor:int;note:str
class PlanLineIn(BaseModel):sequence_no:int;amount_minor:int;due_on:date
class PlanIn(BaseModel):student_id:str;registration_id:str;name:str;reason:str;lines:list[PlanLineIn]
@router.post('/institutions/{iid}/cash-sessions/open')
def cash_open(iid:str,q:CashOpenIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.open_cash(a.account_id,iid,q.currency,q.opening_float_minor)))
@router.post('/institutions/{iid}/cash-sessions/close')
def cash_close(iid:str,q:CashCloseIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.close_cash(a.account_id,iid,q.counted_minor,q.note)))
@router.post('/institutions/{iid}/sponsors')
def sponsor_create(iid:str,q:SponsorIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.create_sponsor(a.account_id,iid,**q.model_dump())))
@router.post('/institutions/{iid}/sponsors/{sid}/apply')
def sponsor_apply(iid:str,sid:str,q:SponsorApplyIn,a:AuthContext=Depends(current_auth)):return obj(w(lambda:runtime.student_finance.sponsor_student(a.account_id,iid,sid,**q.model_dump())))
@router.post('/institutions/{iid}/payment-plans')
def plan(iid:str,q:PlanIn,a:AuthContext=Depends(current_auth)):
 p,lines=w(lambda:runtime.student_finance.create_payment_plan(a.account_id,iid,q.student_id,q.registration_id,q.name,q.reason,[(x.sequence_no,x.amount_minor,x.due_on) for x in q.lines]));return {'plan':obj(p),'lines':[obj(x) for x in lines]}
@router.get('/institutions/{iid}/students/{student_id}/aging')
def aging(iid:str,student_id:str,a:AuthContext=Depends(current_auth)):return w(lambda:runtime.student_finance.aging(a.account_id,iid,student_id))

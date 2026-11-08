from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
router=APIRouter()
def w(f):
 try:return f()
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(409 if 'concurrent' in str(e) or 'already' in str(e) else 400,str(e))
def ser(x):
 d={k:getattr(x,k) for k in x.__dataclass_fields__}
 for k,v in list(d.items()):
  if hasattr(v,'value'):d[k]=v.value
  elif isinstance(v,datetime):d[k]=v.isoformat()
 return d
class CreateIn(BaseModel):teaching_session_id:str;opens_at:datetime|None=None;closes_at:datetime|None=None
class VersionIn(BaseModel):expected_version:int
class DeviceIn(BaseModel):device_id:str
class ScanIn(BaseModel):token:str;device_id:str|None=None;latitude:float|None=None;longitude:float|None=None;accuracy_m:float|None=None;network_proof:bool=False;proximity_token:str|None=None
class ReviewIn(BaseModel):student_account_id:str;status:str;decision:str;reason:str;expected_version:int
@router.post('/institutions/{iid}/attendance')
def create(iid:str,q:CreateIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.create_attendance(a.account_id,iid,**q.model_dump())))
@router.post('/institutions/{iid}/attendance/{sid}/open')
def open_(iid:str,sid:str,q:VersionIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.open(a.account_id,iid,sid,q.expected_version)))
@router.get('/institutions/{iid}/attendance/{sid}/qr')
def qr(iid:str,sid:str,a:AuthContext=Depends(current_auth)):return {'token':w(lambda:runtime.campus_operations.qr_token(a.account_id,iid,sid))}
@router.get('/institutions/{iid}/attendance/{sid}/proximity-token')
def proximity(iid:str,sid:str,a:AuthContext=Depends(current_auth)):return {'token':w(lambda:runtime.campus_operations.proximity_token(a.account_id,iid,sid))}
@router.post('/institutions/{iid}/attendance/devices/bind')
def bind(iid:str,q:DeviceIn,a:AuthContext=Depends(current_auth)):return w(lambda:runtime.campus_operations.bind_device(a.account_id,iid,q.device_id))
@router.post('/institutions/{iid}/attendance/{sid}/scan')
def scan(iid:str,sid:str,q:ScanIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.scan(a.account_id,iid,sid,**q.model_dump())))
@router.post('/institutions/{iid}/attendance/{sid}/close')
def close(iid:str,sid:str,q:VersionIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.close(a.account_id,iid,sid,q.expected_version)))
@router.post('/institutions/{iid}/attendance/{sid}/review')
def review(iid:str,sid:str,q:ReviewIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.review(a.account_id,iid,sid,**q.model_dump())))
@router.get('/institutions/{iid}/attendance/{sid}/roster')
def roster(iid:str,sid:str,a:AuthContext=Depends(current_auth)):return [ser(x) for x in w(lambda:runtime.campus_operations.roster(a.account_id,iid,sid))]
class AnnouncementIn(BaseModel):title:str;body:str;audience:str='institution';offering_id:str|None=None;publish_at:datetime|None=None
class RetractIn(BaseModel):reason:str;expected_version:int
class AbsenceIn(BaseModel):attendance_session_id:str;reason:str;evidence_uri:str|None=None
class AbsenceDecisionIn(BaseModel):decision:str;reason:str;expected_version:int
class EventIn(BaseModel):kind:str;title:str;starts_at:datetime;ends_at:datetime;details:str='';location:str|None=None;offering_id:str|None=None;cohort_id:str|None=None;source_ref:str|None=None
class EventStateIn(BaseModel):state:str;reason:str;expected_version:int
@router.post('/institutions/{iid}/announcements')
def create_announcement(iid:str,q:AnnouncementIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.create_announcement(a.account_id,iid,**q.model_dump())))
@router.get('/institutions/{iid}/announcements')
def announcements(iid:str,a:AuthContext=Depends(current_auth)):return [ser(x) for x in w(lambda:runtime.campus_operations.announcements(a.account_id,iid))]
@router.post('/institutions/{iid}/announcements/{id}/retract')
def retract_announcement(iid:str,id:str,q:RetractIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.retract_announcement(a.account_id,iid,id,q.reason,q.expected_version)))
@router.post('/institutions/{iid}/absence-requests')
def submit_absence(iid:str,q:AbsenceIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.submit_absence(a.account_id,iid,q.attendance_session_id,q.reason,q.evidence_uri)))
@router.get('/institutions/{iid}/absence-requests')
def absence_requests(iid:str,a:AuthContext=Depends(current_auth)):return [ser(x) for x in w(lambda:runtime.campus_operations.absence_requests(a.account_id,iid))]
@router.post('/institutions/{iid}/absence-requests/{id}/decision')
def decide_absence(iid:str,id:str,q:AbsenceDecisionIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.decide_absence(a.account_id,iid,id,q.decision,q.reason,q.expected_version)))
@router.post('/institutions/{iid}/calendar')
def create_event(iid:str,q:EventIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.create_event(a.account_id,iid,**q.model_dump())))
@router.get('/institutions/{iid}/calendar')
def calendar(iid:str,a:AuthContext=Depends(current_auth)):return [ser(x) for x in w(lambda:runtime.campus_operations.calendar(a.account_id,iid))]
@router.post('/institutions/{iid}/calendar/{id}/state')
def event_state(iid:str,id:str,q:EventStateIn,a:AuthContext=Depends(current_auth)):return ser(w(lambda:runtime.campus_operations.update_event_state(a.account_id,iid,id,q.state,q.reason,q.expected_version)))
@router.get('/institutions/{iid}/operations-dashboard')
def dashboard(iid:str,a:AuthContext=Depends(current_auth)):return w(lambda:runtime.campus_operations.operations_dashboard(a.account_id,iid))

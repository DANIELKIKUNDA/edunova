from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.teaching.domain.model import TeacherRole
router=APIRouter()
def wrap(f):
 try:return f()
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(409 if 'concurrent' in str(e) else 400,str(e))
def ser(x):
 d={k:getattr(x,k) for k in x.__dataclass_fields__}
 for k,v in list(d.items()):
  if hasattr(v,'value'):d[k]=v.value
  elif isinstance(v,datetime):d[k]=v.isoformat()
 return d
class CourseIn(BaseModel):code:str;title:str;description:str='';credits:int|None=None
class OfferingIn(BaseModel):course_id:str;cohort_id:str;academic_period_id:str;label:str
class AssignIn(BaseModel):teacher_account_id:str;role:TeacherRole=TeacherRole.LEAD
class PublishIn(BaseModel):expected_version:int
class SessionIn(BaseModel):title:str;starts_at:datetime;ends_at:datetime
class CompleteIn(BaseModel):summary:str;next_topic:str='';expected_version:int
class ResourceIn(BaseModel):title:str;resource_type:str;uri:str;source_revision:str|None=None
class SyllabusIn(BaseModel):title:str;overview:str='';learning_outcomes:list[str]=[]
class TopicIn(BaseModel):title:str;description:str='';learning_objectives:list[str]=[];concept_refs:list[str]=[];planned_minutes:int=0
class TopicProgressIn(BaseModel):state:str;expected_version:int
class ResourceRevisionIn(BaseModel):title:str;uri:str;source_revision:str|None=None;change_note:str='';expected_version:int
@router.post('/institutions/{iid}/courses')
def course(iid:str,q:CourseIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.create_course(auth.account_id,iid,**q.model_dump())))
@router.post('/institutions/{iid}/offerings')
def offering(iid:str,q:OfferingIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.create_offering(auth.account_id,iid,**q.model_dump())))
@router.post('/institutions/{iid}/offerings/{oid}/teachers')
def assign(iid:str,oid:str,q:AssignIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.assign_teacher(auth.account_id,iid,oid,**q.model_dump())))
@router.post('/institutions/{iid}/offerings/{oid}/publish')
def publish(iid:str,oid:str,q:PublishIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.publish_offering(auth.account_id,iid,oid,q.expected_version)))
@router.post('/institutions/{iid}/offerings/{oid}/sessions')
def session(iid:str,oid:str,q:SessionIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.add_session(auth.account_id,iid,oid,**q.model_dump())))
@router.post('/institutions/{iid}/sessions/{sid}/complete')
def complete(iid:str,sid:str,q:CompleteIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.complete_session(auth.account_id,iid,sid,**q.model_dump())))
@router.post('/institutions/{iid}/offerings/{oid}/resources')
def resource(iid:str,oid:str,q:ResourceIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.add_resource(auth.account_id,iid,oid,**q.model_dump())))
@router.post('/institutions/{iid}/resources/{rid}/publish')
def publish_resource(iid:str,rid:str,q:PublishIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.publish_resource(auth.account_id,iid,rid,q.expected_version)))
@router.get('/institutions/{iid}/me/offerings')
def mine(iid:str,auth:AuthContext=Depends(current_auth)):return [ser(x) for x in wrap(lambda:runtime.teaching.my_offerings(auth.account_id,iid))]
@router.get('/institutions/{iid}/offerings/{oid}')
def detail(iid:str,oid:str,auth:AuthContext=Depends(current_auth)):
 d=wrap(lambda:runtime.teaching.offering_detail(auth.account_id,iid,oid));return {k:(ser(v) if hasattr(v,'__dataclass_fields__') else [ser(x) for x in v]) for k,v in d.items()}

@router.post('/institutions/{iid}/offerings/{oid}/syllabi')
def syllabus(iid:str,oid:str,q:SyllabusIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.create_syllabus(auth.account_id,iid,oid,**q.model_dump())))
@router.post('/institutions/{iid}/syllabi/{sid}/topics')
def topic(iid:str,sid:str,q:TopicIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.add_syllabus_topic(auth.account_id,iid,sid,**q.model_dump())))
@router.post('/institutions/{iid}/syllabi/{sid}/approve')
def approve_syllabus(iid:str,sid:str,q:PublishIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.approve_syllabus(auth.account_id,iid,sid,q.expected_version)))
@router.post('/institutions/{iid}/topics/{tid}/progress')
def topic_progress(iid:str,tid:str,q:TopicProgressIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.update_topic_progress(auth.account_id,iid,tid,**q.model_dump())))
@router.post('/institutions/{iid}/resources/{rid}/revisions')
def revise_resource(iid:str,rid:str,q:ResourceRevisionIn,auth:AuthContext=Depends(current_auth)):return ser(wrap(lambda:runtime.teaching.revise_resource(auth.account_id,iid,rid,**q.model_dump())))
@router.get('/institutions/{iid}/offerings/{oid}/progress')
def progress(iid:str,oid:str,auth:AuthContext=Depends(current_auth)):return wrap(lambda:runtime.teaching.teaching_progress(auth.account_id,iid,oid))

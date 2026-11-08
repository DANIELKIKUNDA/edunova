from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
class CurriculumIn(BaseModel):
 program_unit_id:str;effective_academic_year_id:str;code:str;title:str;version:int=1;source_catalog_id:str|None=None
class PrereqIn(BaseModel):course_id:str;required_course_id:str;minimum_status:str='passed'
def wrap(fn):
 try:return fn()
 except PermissionError as e:raise HTTPException(403,str(e)) from e
 except ValueError as e:raise HTTPException(422,str(e)) from e
def ver(x):return {'id':x.id,'program_unit_id':x.program_unit_id,'code':x.code,'title':x.title,'version':x.version,'state':x.state.value,'effective_academic_year_id':x.effective_academic_year_id,'source_catalog_id':x.source_catalog_id,'row_version':x.row_version,'published_at':x.published_at.isoformat() if x.published_at else None,'retired_at':x.retired_at.isoformat() if x.retired_at else None}
@router.post('/institutions/{iid}/curricula')
def create(iid:str,req:CurriculumIn,auth:AuthContext=Depends(current_auth)):return ver(wrap(lambda:runtime.academic_catalog.create(auth.account_id,iid,**req.model_dump())))
@router.post('/institutions/{iid}/curricula/{cid}/imports/medicine')
def med(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):return {'imported':len(wrap(lambda:runtime.academic_catalog.import_medicine(auth.account_id,iid,cid)))}
@router.post('/institutions/{iid}/curricula/{cid}/prerequisites')
def prerequisite(iid:str,cid:str,req:PrereqIn,auth:AuthContext=Depends(current_auth)):
 p=wrap(lambda:runtime.academic_catalog.add_prerequisite(auth.account_id,iid,cid,**req.model_dump()));return {'id':p.id,'course_id':p.course_id,'required_course_id':p.required_course_id,'minimum_status':p.minimum_status}
@router.post('/institutions/{iid}/curricula/{cid}/publish')
def publish(iid:str,cid:str,expected_version:int,auth:AuthContext=Depends(current_auth)):return ver(wrap(lambda:runtime.academic_catalog.publish(auth.account_id,iid,cid,expected_version)))
@router.get('/institutions/{iid}/curricula/{cid}/validate')
def validate(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):return wrap(lambda:runtime.academic_catalog.validate(auth.account_id,iid,cid))
@router.post('/institutions/{iid}/curricula/{cid}/retire')
def retire(iid:str,cid:str,expected_version:int,auth:AuthContext=Depends(current_auth)):return ver(wrap(lambda:runtime.academic_catalog.retire(auth.account_id,iid,cid,expected_version)))
class CloneIn(BaseModel):
 effective_academic_year_id:str;version:int|None=None;code:str|None=None;title:str|None=None
@router.post('/institutions/{iid}/curricula/{cid}/clone')
def clone(iid:str,cid:str,req:CloneIn,auth:AuthContext=Depends(current_auth)):return ver(wrap(lambda:runtime.academic_catalog.clone_version(auth.account_id,iid,cid,**req.model_dump())))
@router.post('/institutions/{iid}/curricula/{cid}/cohorts/{cohort_id}')
def bind(iid:str,cid:str,cohort_id:str,auth:AuthContext=Depends(current_auth)):
 b=wrap(lambda:runtime.academic_catalog.bind_cohort(auth.account_id,iid,cid,cohort_id));return {'id':b.id,'curriculum_id':b.curriculum_id,'cohort_id':b.cohort_id}
@router.get('/institutions/{iid}/curricula/{cid}')
def detail(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):
 x,courses,prs=wrap(lambda:runtime.academic_catalog.detail(auth.account_id,iid,cid));return {'curriculum':ver(x),'courses':[{'id':z.id,'semester':z.semester,'ue_code':z.ue_code,'code':z.code,'title':z.title,'credits':z.credits,'total_hours':z.total_hours,'cycle':z.cycle,'level':z.level,'ue_declared_credits':z.ue_declared_credits,'cmi':z.cmi,'tp_td':z.tp_td,'tpe':z.tpe,'percent':z.percent} for z in courses],'prerequisites':[{'course_id':p.course_id,'required_course_id':p.required_course_id,'minimum_status':p.minimum_status} for p in prs]}

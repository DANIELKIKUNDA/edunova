from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
class CampaignIn(BaseModel):
 program_unit_id:str;academic_year_id:str;curriculum_id:str;slug:str=Field(min_length=1,max_length=120);title:str=Field(min_length=1,max_length=240);summary:str=Field(default='',max_length=1200);opens_at:datetime;closes_at:datetime;capacity:int|None=None;application_fee_minor:int=0;currency:str='USD';contact_email:str|None=None;instructions:str=Field(default='',max_length=4000);study_mode:str='on_campus';campus_label:str|None=None;intake_label:str|None=None;eligibility_summary:str|None=None
class CampaignPatch(BaseModel):
 slug:str|None=None;title:str|None=None;summary:str|None=None;opens_at:datetime|None=None;closes_at:datetime|None=None;capacity:int|None=None;application_fee_minor:int|None=None;currency:str|None=None;contact_email:str|None=None;instructions:str|None=None;study_mode:str|None=None;campus_label:str|None=None;intake_label:str|None=None;eligibility_summary:str|None=None
class RequirementIn(BaseModel):code:str;label:str;description:str|None=None;required:bool=True;document_required:bool=True
def wrap(fn):
 try:return fn()
 except PermissionError as e:raise HTTPException(403,str(e)) from e
 except ValueError as e:raise HTTPException(422,str(e)) from e
def out(c,availability=None):
 d={'id':c.id,'institution_id':c.institution_id,'program_unit_id':c.program_unit_id,'academic_year_id':c.academic_year_id,'curriculum_id':c.curriculum_id,'slug':c.slug,'title':c.title,'summary':c.summary,'state':c.state.value,'opens_at':c.opens_at.isoformat(),'closes_at':c.closes_at.isoformat(),'capacity':c.capacity,'application_fee_minor':c.application_fee_minor,'currency':c.currency,'contact_email':c.contact_email,'row_version':c.row_version,'instructions':c.instructions,'study_mode':c.study_mode,'campus_label':c.campus_label,'intake_label':c.intake_label,'eligibility_summary':c.eligibility_summary}
 if availability:d['availability']=availability
 return d
@router.post('/institutions/{iid}/campaigns')
def create(iid:str,req:CampaignIn,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.admissions_catalog.create(auth.account_id,iid,**req.model_dump())))
@router.patch('/institutions/{iid}/campaigns/{cid}')
def update(iid:str,cid:str,expected_version:int,req:CampaignPatch,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.admissions_catalog.update_draft(auth.account_id,iid,cid,expected_version,**req.model_dump(exclude_unset=True))))
@router.post('/institutions/{iid}/campaigns/{cid}/requirements')
def requirement(iid:str,cid:str,req:RequirementIn,auth:AuthContext=Depends(current_auth)):
 r=wrap(lambda:runtime.admissions_catalog.add_requirement(auth.account_id,iid,cid,**req.model_dump()));return {'id':r.id,'code':r.code,'label':r.label,'description':r.description,'required':r.required,'document_required':r.document_required,'ordinal':r.ordinal}
@router.delete('/institutions/{iid}/campaigns/{cid}/requirements/{rid}',status_code=204)
def remove_requirement(iid:str,cid:str,rid:str,auth:AuthContext=Depends(current_auth)):wrap(lambda:runtime.admissions_catalog.remove_requirement(auth.account_id,iid,cid,rid))
@router.get('/institutions/{iid}/campaigns/{cid}/validate')
def validate(iid:str,cid:str,auth:AuthContext=Depends(current_auth)):return wrap(lambda:runtime.admissions_catalog.validate(auth.account_id,iid,cid))
@router.post('/institutions/{iid}/campaigns/{cid}/publish')
def publish(iid:str,cid:str,expected_version:int,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.admissions_catalog.publish(auth.account_id,iid,cid,expected_version)))
@router.post('/institutions/{iid}/campaigns/{cid}/close')
def close(iid:str,cid:str,expected_version:int,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.admissions_catalog.close(auth.account_id,iid,cid,expected_version)))
@router.post('/institutions/{iid}/campaigns/{cid}/archive')
def archive(iid:str,cid:str,expected_version:int,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.admissions_catalog.archive(auth.account_id,iid,cid,expected_version)))
@router.get('/public/institutions/{institution_slug}/campaigns')
def public_list(institution_slug:str):
 inst,rows=wrap(lambda:runtime.admissions_catalog.public_list(institution_slug));return {'institution':{'slug':inst.slug,'name':inst.name,'city':inst.city,'country_code':inst.country_code,'logo_url':inst.logo_url},'campaigns':[out(c,status) for c,status in rows]}
@router.get('/public/institutions/{institution_slug}/campaigns/{campaign_slug}')
def public_detail(institution_slug:str,campaign_slug:str):
 inst,p,y,cur,c,rs,status=wrap(lambda:runtime.admissions_catalog.public_detail(institution_slug,campaign_slug));return {'institution':{'slug':inst.slug,'name':inst.name,'city':inst.city,'country_code':inst.country_code,'logo_url':inst.logo_url},'program':{'id':p.id,'code':p.code,'name':p.name},'academic_year':{'id':y.id,'name':y.name},'curriculum':{'id':cur.id,'code':cur.code,'title':cur.title,'version':cur.version},'campaign':out(c,status),'requirements':[{'code':r.code,'label':r.label,'description':r.description,'required':r.required,'document_required':r.document_required,'ordinal':r.ordinal} for r in rs]}

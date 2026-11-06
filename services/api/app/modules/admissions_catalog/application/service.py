from __future__ import annotations
import re
from dataclasses import replace
from uuid import uuid4
from app.modules.admissions_catalog.domain.model import *
from app.modules.academic_catalog.domain.model import CurriculumState
from app.modules.campus.domain.model import CampusRole,UnitKind,PeriodKind,InstitutionState
WRITE={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.FACULTY_ADMIN}
SLUG=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$');EMAIL=re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');MODES={'on_campus','online','hybrid'}
class AdmissionsCatalogService:
 def __init__(self,repo,campus,campus_repo,academic_repo,now,audit=None):self.repo=repo;self.campus=campus;self.campus_repo=campus_repo;self.academic_repo=academic_repo;self.now=now;self.audit=audit
 def _auth(self,a,i):return self.campus.membership(a,i,WRITE)
 def _audit(self,a,action,id,meta=None):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type='admission_campaign',entity_id=id,metadata=meta or {})
 def _validate_identity(self,slug,title,summary,opens_at,closes_at,capacity,fee,currency,email,study_mode):
  if not SLUG.fullmatch(slug):raise ValueError('admissions_invalid_slug')
  if not title.strip():raise ValueError('admissions_title_required')
  if opens_at.tzinfo is None or closes_at.tzinfo is None:raise ValueError('admissions_timezone_required')
  if opens_at>=closes_at:raise ValueError('admissions_invalid_dates')
  if capacity is not None and capacity<1:raise ValueError('admissions_invalid_capacity')
  if fee<0:raise ValueError('admissions_invalid_fee')
  if len(currency)!=3 or not currency.isalpha():raise ValueError('admissions_invalid_currency')
  if email and not EMAIL.fullmatch(email):raise ValueError('admissions_invalid_contact_email')
  if study_mode not in MODES:raise ValueError('admissions_invalid_study_mode')
 def create(self,a,i,*,program_unit_id,academic_year_id,curriculum_id,slug,title,summary,opens_at,closes_at,capacity=None,application_fee_minor=0,currency='USD',contact_email=None,instructions='',study_mode='on_campus',campus_label=None,intake_label=None,eligibility_summary=None):
  self._auth(a,i);inst=self.campus_repo.institution(i);p=self.campus_repo.unit(i,program_unit_id);y=self.campus_repo.period(i,academic_year_id);cur=self.academic_repo.curriculum(i,curriculum_id);slug=slug.strip().lower();currency=currency.strip().upper();email=contact_email.strip().lower() if contact_email else None;study_mode=study_mode.strip().lower()
  if not inst or inst.state!=InstitutionState.ACTIVE:raise ValueError('admissions_institution_not_active')
  if not p or p.kind!=UnitKind.PROGRAM or not p.active:raise ValueError('admissions_active_program_required')
  if not y or y.kind!=PeriodKind.ACADEMIC_YEAR or not y.active:raise ValueError('admissions_active_academic_year_required')
  if not cur or cur.program_unit_id!=program_unit_id or cur.effective_academic_year_id!=academic_year_id or cur.state!=CurriculumState.PUBLISHED:raise ValueError('admissions_published_curriculum_required')
  self._validate_identity(slug,title,summary,opens_at,closes_at,capacity,application_fee_minor,currency,email,study_mode)
  if self.repo.slug_exists(i,slug):raise ValueError('admissions_slug_exists')
  n=self.now();x=AdmissionCampaign(uuid4().hex,i,program_unit_id,academic_year_id,curriculum_id,slug,title.strip(),summary.strip(),CampaignState.DRAFT,opens_at,closes_at,capacity,application_fee_minor,currency,email,1,a,n,None,instructions.strip(),study_mode,campus_label.strip() if campus_label else None,intake_label.strip() if intake_label else None,eligibility_summary.strip() if eligibility_summary else None,None);self.repo.save(x);self._audit(a,'admissions.campaign.created',x.id);return x
 def update_draft(self,a,i,cid,expected_version,**changes):
  self._auth(a,i);c=self.repo.campaign(i,cid)
  if not c:raise ValueError('admissions_campaign_not_found')
  if c.row_version!=expected_version:raise ValueError('admissions_campaign_concurrent_modification')
  if c.state!=CampaignState.DRAFT:raise ValueError('admissions_campaign_not_editable')
  allowed={'slug','title','summary','opens_at','closes_at','capacity','application_fee_minor','currency','contact_email','instructions','study_mode','campus_label','intake_label','eligibility_summary'};changes={k:v for k,v in changes.items() if k in allowed and v is not None}
  vals={k:getattr(c,k) for k in allowed};vals.update(changes);vals['slug']=vals['slug'].strip().lower();vals['currency']=vals['currency'].strip().upper();vals['contact_email']=vals['contact_email'].strip().lower() if vals['contact_email'] else None;vals['study_mode']=vals['study_mode'].strip().lower()
  self._validate_identity(vals['slug'],vals['title'],vals['summary'],vals['opens_at'],vals['closes_at'],vals['capacity'],vals['application_fee_minor'],vals['currency'],vals['contact_email'],vals['study_mode'])
  if vals['slug']!=c.slug and self.repo.slug_exists(i,vals['slug']):raise ValueError('admissions_slug_exists')
  x=replace(c,**vals,row_version=c.row_version+1);self.repo.save(x,c.row_version);self._audit(a,'admissions.campaign.updated',cid);return x
 def add_requirement(self,a,i,cid,*,code,label,description=None,required=True,document_required=True):
  self._auth(a,i);c=self.repo.campaign(i,cid)
  if not c:raise ValueError('admissions_campaign_not_found')
  if c.state!=CampaignState.DRAFT:raise ValueError('admissions_campaign_not_editable')
  code=code.strip().upper();label=label.strip()
  if not code or not label:raise ValueError('admissions_requirement_identity_required')
  if self.repo.requirement_by_code(cid,code):raise ValueError('admissions_requirement_code_exists')
  r=AdmissionRequirement(uuid4().hex,cid,code,label,description.strip() if description else None,required,document_required,len(self.repo.requirements(cid))+1);self.repo.add_requirement(r);self._audit(a,'admissions.requirement.added',cid,{'code':code});return r
 def remove_requirement(self,a,i,cid,rid):
  self._auth(a,i);c=self.repo.campaign(i,cid)
  if not c or c.state!=CampaignState.DRAFT:raise ValueError('admissions_campaign_not_editable')
  if not self.repo.delete_requirement(cid,rid):raise ValueError('admissions_requirement_not_found')
  self.repo.resequence_requirements(cid);self._audit(a,'admissions.requirement.removed',cid,{'requirement_id':rid})
 def validate(self,a,i,cid):
  self.campus.membership(a,i);c=self.repo.campaign(i,cid)
  if not c:raise ValueError('admissions_campaign_not_found')
  issues=[];rs=self.repo.requirements(cid);cur=self.academic_repo.curriculum(i,c.curriculum_id)
  if not rs:issues.append({'severity':'blocking','kind':'requirements_required'})
  if not any(r.required for r in rs):issues.append({'severity':'warning','kind':'no_required_requirement'})
  if not cur or cur.state!=CurriculumState.PUBLISHED:issues.append({'severity':'blocking','kind':'published_curriculum_required'})
  if c.contact_email is None:issues.append({'severity':'warning','kind':'contact_email_missing'})
  if not c.instructions:issues.append({'severity':'warning','kind':'instructions_missing'})
  return {'campaign_id':cid,'requirement_count':len(rs),'blocking_count':sum(x['severity']=='blocking' for x in issues),'issues':issues,'publishable':not any(x['severity']=='blocking' for x in issues)}
 def publish(self,a,i,cid,expected_version):
  self._auth(a,i);c=self.repo.campaign(i,cid)
  if not c:raise ValueError('admissions_campaign_not_found')
  if c.row_version!=expected_version:raise ValueError('admissions_campaign_concurrent_modification')
  if c.state!=CampaignState.DRAFT:raise ValueError('admissions_campaign_not_draft')
  report=self.validate(a,i,cid)
  if not self.repo.requirements(cid):raise ValueError('admissions_requirements_required')
  if not report['publishable']:raise ValueError('admissions_campaign_validation_failed')
  x=replace(c,state=CampaignState.PUBLISHED,row_version=c.row_version+1,published_at=self.now());self.repo.save(x,c.row_version);self._audit(a,'admissions.campaign.published',cid,{'requirements':report['requirement_count']});return x
 def close(self,a,i,cid,expected_version):
  self._auth(a,i);c=self.repo.campaign(i,cid)
  if not c:raise ValueError('admissions_campaign_not_found')
  if c.row_version!=expected_version:raise ValueError('admissions_campaign_concurrent_modification')
  if c.state!=CampaignState.PUBLISHED:raise ValueError('admissions_campaign_not_published')
  x=replace(c,state=CampaignState.CLOSED,row_version=c.row_version+1);self.repo.save(x,c.row_version);self._audit(a,'admissions.campaign.closed',cid);return x
 def archive(self,a,i,cid,expected_version):
  self._auth(a,i);c=self.repo.campaign(i,cid)
  if not c:raise ValueError('admissions_campaign_not_found')
  if c.row_version!=expected_version:raise ValueError('admissions_campaign_concurrent_modification')
  if c.state not in {CampaignState.CLOSED,CampaignState.DRAFT}:raise ValueError('admissions_campaign_must_be_closed_or_draft')
  x=replace(c,state=CampaignState.ARCHIVED,row_version=c.row_version+1,archived_at=self.now());self.repo.save(x,c.row_version);self._audit(a,'admissions.campaign.archived',cid);return x
 def availability(self,c):
  n=self.now()
  if c.state!=CampaignState.PUBLISHED:return 'closed'
  if n<c.opens_at:return 'upcoming'
  if n>=c.closes_at:return 'deadline_passed'
  return 'open'
 def public_detail(self,institution_slug,campaign_slug):
  pair=self.repo.by_public_slug(institution_slug.strip().lower(),campaign_slug.strip().lower(),self.campus_repo)
  if not pair:raise ValueError('admissions_public_campaign_not_found')
  inst,c=pair;p=self.campus_repo.unit(inst.id,c.program_unit_id);y=self.campus_repo.period(inst.id,c.academic_year_id);cur=self.academic_repo.curriculum(inst.id,c.curriculum_id)
  if not p or not p.active or not y or not cur or cur.state!=CurriculumState.PUBLISHED:raise ValueError('admissions_public_campaign_not_found')
  return inst,p,y,cur,c,self.repo.requirements(c.id),self.availability(c)
 def public_list(self,institution_slug):
  inst=self.campus_repo.institution_by_slug(institution_slug.strip().lower())
  if not inst or inst.state!=InstitutionState.ACTIVE:raise ValueError('admissions_public_institution_not_found')
  rows=self.repo.list(inst.id,public_only=True);return inst,tuple((c,self.availability(c)) for c in rows)

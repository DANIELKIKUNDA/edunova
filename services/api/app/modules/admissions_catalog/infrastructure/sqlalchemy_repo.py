from __future__ import annotations
from datetime import UTC
from sqlalchemy import String,Integer,DateTime,Boolean,UniqueConstraint,select,update,delete
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.admissions_catalog.domain.model import *
def _utc(x):return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class AdmissionCampaignRow(Base):
 __tablename__='admission_campaigns';__table_args__=(UniqueConstraint('institution_id','slug',name='uq_admission_campaign_slug'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);program_unit_id:Mapped[str]=mapped_column(String(64),index=True);academic_year_id:Mapped[str]=mapped_column(String(64),index=True);curriculum_id:Mapped[str]=mapped_column(String(64),index=True);slug:Mapped[str]=mapped_column(String(120),index=True);title:Mapped[str]=mapped_column(String(240));summary:Mapped[str]=mapped_column(String(1200));state:Mapped[str]=mapped_column(String(20),index=True);opens_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True);closes_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True);capacity:Mapped[int|None]=mapped_column(Integer,nullable=True);application_fee_minor:Mapped[int]=mapped_column(Integer);currency:Mapped[str]=mapped_column(String(3));contact_email:Mapped[str|None]=mapped_column(String(254),nullable=True);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));published_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True);instructions:Mapped[str]=mapped_column(String(4000),default='');study_mode:Mapped[str]=mapped_column(String(20),default='on_campus');campus_label:Mapped[str|None]=mapped_column(String(240),nullable=True);intake_label:Mapped[str|None]=mapped_column(String(160),nullable=True);eligibility_summary:Mapped[str|None]=mapped_column(String(2000),nullable=True);archived_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
class AdmissionRequirementRow(Base):
 __tablename__='admission_requirements';__table_args__=(UniqueConstraint('campaign_id','code',name='uq_admission_requirement_code'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);campaign_id:Mapped[str]=mapped_column(String(64),index=True);code:Mapped[str]=mapped_column(String(80));label:Mapped[str]=mapped_column(String(240));description:Mapped[str|None]=mapped_column(String(1000),nullable=True);required:Mapped[bool]=mapped_column(Boolean);document_required:Mapped[bool]=mapped_column(Boolean);ordinal:Mapped[int]=mapped_column(Integer)
class SqlAdmissionsCatalogRepository:
 def __init__(self,sf):self.sf=sf
 def _c(self,r):return AdmissionCampaign(r.id,r.institution_id,r.program_unit_id,r.academic_year_id,r.curriculum_id,r.slug,r.title,r.summary,CampaignState(r.state),_utc(r.opens_at),_utc(r.closes_at),r.capacity,r.application_fee_minor,r.currency,r.contact_email,r.row_version,r.created_by,_utc(r.created_at),_utc(r.published_at),r.instructions or '',r.study_mode or 'on_campus',r.campus_label,r.intake_label,r.eligibility_summary,_utc(r.archived_at))
 def _r(self,r):return AdmissionRequirement(r.id,r.campaign_id,r.code,r.label,r.description,r.required,r.document_required,r.ordinal)
 def campaign_any(self,cid):
  with self.sf() as s:r=s.get(AdmissionCampaignRow,cid);return self._c(r) if r else None
 def campaign(self,i,cid):
  with self.sf() as s:r=s.get(AdmissionCampaignRow,cid);return self._c(r) if r and r.institution_id==i else None
 def slug_exists(self,i,slug):
  with self.sf() as s:return s.scalar(select(AdmissionCampaignRow.id).where(AdmissionCampaignRow.institution_id==i,AdmissionCampaignRow.slug==slug)) is not None
 def by_public_slug(self,institution_slug,campaign_slug,campus_repo):
  inst=campus_repo.institution_by_slug(institution_slug)
  if not inst:return None
  with self.sf() as s:r=s.scalar(select(AdmissionCampaignRow).where(AdmissionCampaignRow.institution_id==inst.id,AdmissionCampaignRow.slug==campaign_slug,AdmissionCampaignRow.state=='published'));return (inst,self._c(r)) if r else None
 def save(self,x,expected_version=None):
  d=dict(institution_id=x.institution_id,program_unit_id=x.program_unit_id,academic_year_id=x.academic_year_id,curriculum_id=x.curriculum_id,slug=x.slug,title=x.title,summary=x.summary,state=x.state.value,opens_at=x.opens_at,closes_at=x.closes_at,capacity=x.capacity,application_fee_minor=x.application_fee_minor,currency=x.currency,contact_email=x.contact_email,row_version=x.row_version,created_by=x.created_by,created_at=x.created_at,published_at=x.published_at,instructions=x.instructions,study_mode=x.study_mode,campus_label=x.campus_label,intake_label=x.intake_label,eligibility_summary=x.eligibility_summary,archived_at=x.archived_at)
  with self.sf() as s:
   old=s.get(AdmissionCampaignRow,x.id)
   if not old:s.add(AdmissionCampaignRow(id=x.id,**d));s.commit();return
   q=update(AdmissionCampaignRow).where(AdmissionCampaignRow.id==x.id)
   if expected_version is not None:q=q.where(AdmissionCampaignRow.row_version==expected_version)
   r=s.execute(q.values(**d))
   if r.rowcount!=1:s.rollback();raise ValueError('admissions_campaign_concurrent_modification')
   s.commit()
 def list(self,i,public_only=False):
  with self.sf() as s:
   q=select(AdmissionCampaignRow).where(AdmissionCampaignRow.institution_id==i)
   if public_only:q=q.where(AdmissionCampaignRow.state=='published')
   return tuple(self._c(r) for r in s.scalars(q.order_by(AdmissionCampaignRow.opens_at.desc())).all())
 def add_requirement(self,x):
  with self.sf() as s:s.add(AdmissionRequirementRow(id=x.id,campaign_id=x.campaign_id,code=x.code,label=x.label,description=x.description,required=x.required,document_required=x.document_required,ordinal=x.ordinal));s.commit()
 def requirements(self,cid):
  with self.sf() as s:return tuple(self._r(r) for r in s.scalars(select(AdmissionRequirementRow).where(AdmissionRequirementRow.campaign_id==cid).order_by(AdmissionRequirementRow.ordinal)).all())
 def requirement_by_code(self,cid,code):
  with self.sf() as s:
   r=s.scalar(select(AdmissionRequirementRow).where(AdmissionRequirementRow.campaign_id==cid,AdmissionRequirementRow.code==code));return self._r(r) if r else None
 def delete_requirement(self,cid,rid):
  with self.sf() as s:
   r=s.execute(delete(AdmissionRequirementRow).where(AdmissionRequirementRow.campaign_id==cid,AdmissionRequirementRow.id==rid));s.commit();return r.rowcount==1
 def resequence_requirements(self,cid):
  with self.sf() as s:
   rows=s.scalars(select(AdmissionRequirementRow).where(AdmissionRequirementRow.campaign_id==cid).order_by(AdmissionRequirementRow.ordinal,AdmissionRequirementRow.id)).all()
   for n,r in enumerate(rows,1):r.ordinal=n
   s.commit()

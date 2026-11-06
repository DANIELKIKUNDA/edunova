from sqlalchemy import String,Integer,DateTime,UniqueConstraint,select,update
from datetime import UTC
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.applications.domain.model import *
class CandidateApplicationRow(Base):
 __tablename__='candidate_applications';__table_args__=(UniqueConstraint('account_id','campaign_id',name='uq_candidate_campaign_application'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);account_id:Mapped[str]=mapped_column(String(64),index=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);campaign_id:Mapped[str]=mapped_column(String(64),index=True);state:Mapped[str]=mapped_column(String(20),index=True);given_names:Mapped[str]=mapped_column(String(160));family_name:Mapped[str]=mapped_column(String(120));birth_date:Mapped[str|None]=mapped_column(String(10),nullable=True);nationality_code:Mapped[str|None]=mapped_column(String(3),nullable=True);gender:Mapped[str|None]=mapped_column(String(32),nullable=True);address:Mapped[str|None]=mapped_column(String(500),nullable=True);city:Mapped[str|None]=mapped_column(String(160),nullable=True);country_code:Mapped[str|None]=mapped_column(String(3),nullable=True);phone_number:Mapped[str|None]=mapped_column(String(40),nullable=True);email:Mapped[str|None]=mapped_column(String(254),nullable=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True));submitted_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True);withdrawn_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
class ApplicationDocumentRow(Base):
 __tablename__='candidate_application_documents';__table_args__=(UniqueConstraint('application_id','requirement_code','sha256',name='uq_application_document_digest'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);application_id:Mapped[str]=mapped_column(String(64),index=True);requirement_code:Mapped[str]=mapped_column(String(80),index=True);original_name:Mapped[str]=mapped_column(String(255));content_type:Mapped[str]=mapped_column(String(120));size_bytes:Mapped[int]=mapped_column(Integer);sha256:Mapped[str]=mapped_column(String(64));storage_key:Mapped[str]=mapped_column(String(500),unique=True);state:Mapped[str]=mapped_column(String(20),index=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));replaced_by:Mapped[str|None]=mapped_column(String(64),nullable=True)
class CandidateUploadSessionRow(Base):
 __tablename__='candidate_upload_sessions'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);application_id:Mapped[str]=mapped_column(String(64),index=True);requirement_code:Mapped[str]=mapped_column(String(80));original_name:Mapped[str]=mapped_column(String(255));content_type:Mapped[str]=mapped_column(String(120));total_bytes:Mapped[int]=mapped_column(Integer);total_chunks:Mapped[int]=mapped_column(Integer);expected_sha256:Mapped[str|None]=mapped_column(String(64),nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));expires_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True);completed_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
class CandidateUploadChunkRow(Base):
 __tablename__='candidate_upload_chunks'
 upload_id:Mapped[str]=mapped_column(String(64),primary_key=True);chunk_index:Mapped[int]=mapped_column(Integer,primary_key=True);size_bytes:Mapped[int]=mapped_column(Integer);sha256:Mapped[str]=mapped_column(String(64))

class ApplicationConsentRow(Base):
 __tablename__='candidate_application_consents'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);application_id:Mapped[str]=mapped_column(String(64),index=True);kind:Mapped[str]=mapped_column(String(40));policy_version:Mapped[str]=mapped_column(String(80));accepted_at:Mapped[object]=mapped_column(DateTime(timezone=True));evidence_hash:Mapped[str]=mapped_column(String(64))
class SubmissionSnapshotRow(Base):
 __tablename__='candidate_submission_snapshots'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);application_id:Mapped[str]=mapped_column(String(64),index=True,unique=True);row_version:Mapped[int]=mapped_column(Integer);payload_sha256:Mapped[str]=mapped_column(String(64));document_manifest_sha256:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SqlApplicationRepository:
 def __init__(self,sf):self.sf=sf
 def _a(self,r):return CandidateApplication(r.id,r.account_id,r.institution_id,r.campaign_id,ApplicationState(r.state),r.given_names,r.family_name,r.birth_date,r.nationality_code,r.gender,r.address,r.city,r.country_code,r.phone_number,r.email,r.row_version,r.created_at,r.updated_at,r.submitted_at,r.withdrawn_at)
 def _d(self,r):return ApplicationDocument(r.id,r.application_id,r.requirement_code,r.original_name,r.content_type,r.size_bytes,r.sha256,r.storage_key,DocumentState(r.state),r.created_at,r.replaced_by)
 def get(self,aid):
  with self.sf() as s:r=s.get(CandidateApplicationRow,aid);return self._a(r) if r else None
 def by_account_campaign(self,a,c):
  with self.sf() as s:r=s.scalar(select(CandidateApplicationRow).where(CandidateApplicationRow.account_id==a,CandidateApplicationRow.campaign_id==c));return self._a(r) if r else None
 def save(self,x,expected=None):
  d=x.__dict__.copy();d['state']=x.state.value
  with self.sf() as s:
   old=s.get(CandidateApplicationRow,x.id)
   if not old:s.add(CandidateApplicationRow(**d));s.commit();return
   q=update(CandidateApplicationRow).where(CandidateApplicationRow.id==x.id)
   if expected is not None:q=q.where(CandidateApplicationRow.row_version==expected)
   r=s.execute(q.values(**d));
   if r.rowcount!=1:s.rollback();raise ValueError('application_concurrent_modification')
   s.commit()
 def add_document(self,x):
  with self.sf() as s:s.add(ApplicationDocumentRow(**{**x.__dict__,'state':x.state.value}));s.commit()
 def documents(self,aid):
  with self.sf() as s:return tuple(self._d(r) for r in s.scalars(select(ApplicationDocumentRow).where(ApplicationDocumentRow.application_id==aid).order_by(ApplicationDocumentRow.created_at)).all())
 def mark_replaced(self,old_id,new_id):
  with self.sf() as s:s.execute(update(ApplicationDocumentRow).where(ApplicationDocumentRow.id==old_id).values(state='replaced',replaced_by=new_id));s.commit()

 def create_upload(self,u):
  with self.sf() as s:s.add(CandidateUploadSessionRow(**u.__dict__));s.commit()
 def upload(self,uid):
  with self.sf() as s:
   r=s.get(CandidateUploadSessionRow,uid)
   if not r:return None
   d={c:getattr(r,c) for c in UploadSession.__dataclass_fields__}
   for k in ('created_at','expires_at','completed_at'):
    if d[k] is not None and d[k].tzinfo is None:d[k]=d[k].replace(tzinfo=UTC)
   return UploadSession(**d)
 def save_chunk(self,uid,index,size,digest):
  with self.sf() as s:
   r=s.get(CandidateUploadChunkRow,(uid,index))
   if r:
    if r.sha256!=digest:raise ValueError('application_upload_chunk_conflict')
    return
   s.add(CandidateUploadChunkRow(upload_id=uid,chunk_index=index,size_bytes=size,sha256=digest));s.commit()
 def chunks(self,uid):
  with self.sf() as s:return tuple((r.chunk_index,r.size_bytes,r.sha256) for r in s.scalars(select(CandidateUploadChunkRow).where(CandidateUploadChunkRow.upload_id==uid).order_by(CandidateUploadChunkRow.chunk_index)).all())
 def complete_upload(self,uid,at):
  with self.sf() as s:s.execute(update(CandidateUploadSessionRow).where(CandidateUploadSessionRow.id==uid,CandidateUploadSessionRow.completed_at.is_(None)).values(completed_at=at));s.commit()

 def list_by_account(self,a):
  with self.sf() as s:return tuple(self._a(r) for r in s.scalars(select(CandidateApplicationRow).where(CandidateApplicationRow.account_id==a).order_by(CandidateApplicationRow.created_at.desc())).all())
 def add_consent(self,x):
  with self.sf() as s:s.add(ApplicationConsentRow(**{**x.__dict__,'kind':x.kind.value}));s.commit()
 def consents(self,aid):
  with self.sf() as s:return tuple(ApplicationConsent(r.id,r.application_id,ConsentKind(r.kind),r.policy_version,r.accepted_at,r.evidence_hash) for r in s.scalars(select(ApplicationConsentRow).where(ApplicationConsentRow.application_id==aid)).all())
 def add_snapshot(self,x):
  with self.sf() as s:s.add(SubmissionSnapshotRow(**x.__dict__));s.commit()
 def snapshot(self,aid):
  with self.sf() as s:
   r=s.scalar(select(SubmissionSnapshotRow).where(SubmissionSnapshotRow.application_id==aid));return SubmissionSnapshot(**{k:getattr(r,k) for k in SubmissionSnapshot.__dataclass_fields__}) if r else None
 def delete_document(self,did):
  with self.sf() as s:s.execute(update(ApplicationDocumentRow).where(ApplicationDocumentRow.id==did).values(state='deleted'));s.commit()

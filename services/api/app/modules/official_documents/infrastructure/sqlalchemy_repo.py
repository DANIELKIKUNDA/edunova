from sqlalchemy import String,DateTime,LargeBinary,ForeignKey,select,UniqueConstraint,update
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.official_documents.domain.model import OfficialDocument,DocumentState,OfficialDocumentEvent,OfficialDocumentTemplate,TemplateState
class OfficialDocumentRow(Base):
 __tablename__='official_documents'
 __table_args__=(UniqueConstraint('institution_id','serial_number',name='uq_official_serial'),UniqueConstraint('institution_id','service_request_id',name='uq_official_request'),UniqueConstraint('verification_token_hash',name='uq_official_token'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True)
 institution_id:Mapped[str]=mapped_column(String(64),index=True)
 student_id:Mapped[str]=mapped_column(String(64),index=True)
 service_request_id:Mapped[str]=mapped_column(String(64),ForeignKey('student_service_requests.id'))
 serial_number:Mapped[str]=mapped_column(String(100));kind:Mapped[str]=mapped_column(String(40));title:Mapped[str]=mapped_column(String(200));sha256_hex:Mapped[str]=mapped_column(String(64));pdf_bytes:Mapped[bytes]=mapped_column(LargeBinary);verification_token_hash:Mapped[str]=mapped_column(String(64),index=True);state:Mapped[str]=mapped_column(String(20));issued_by:Mapped[str]=mapped_column(String(64));issued_at:Mapped[object]=mapped_column(DateTime(timezone=True));revoked_by:Mapped[str|None]=mapped_column(String(64),nullable=True);revoked_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True);revocation_reason:Mapped[str|None]=mapped_column(String(1000),nullable=True);source_evidence_hash:Mapped[str|None]=mapped_column(String(64),nullable=True);source_jury_outcome_id:Mapped[str|None]=mapped_column(String(64),nullable=True);replaces_document_id:Mapped[str|None]=mapped_column(String(64),nullable=True);issuer_name:Mapped[str|None]=mapped_column(String(240),nullable=True);issuer_legal_name:Mapped[str|None]=mapped_column(String(240),nullable=True);issuer_country_code:Mapped[str|None]=mapped_column(String(2),nullable=True);template_version:Mapped[str]=mapped_column(String(40),default='official-v1')

class OfficialDocumentEventRow(Base):
 __tablename__='official_document_events'
 id:Mapped[str]=mapped_column(String(64),primary_key=True)
 institution_id:Mapped[str]=mapped_column(String(64),index=True)
 document_id:Mapped[str]=mapped_column(String(64),ForeignKey('official_documents.id'),index=True)
 actor_id:Mapped[str]=mapped_column(String(64))
 event_type:Mapped[str]=mapped_column(String(40))
 reason:Mapped[str|None]=mapped_column(String(1000),nullable=True)
 created_at:Mapped[object]=mapped_column(DateTime(timezone=True))

class OfficialDocumentTemplateRow(Base):
 __tablename__='official_document_templates'
 __table_args__=(UniqueConstraint('institution_id','kind','version',name='uq_official_template_version'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True)
 institution_id:Mapped[str]=mapped_column(String(64),index=True)
 kind:Mapped[str]=mapped_column(String(40),index=True)
 version:Mapped[str]=mapped_column(String(40))
 name:Mapped[str]=mapped_column(String(200))
 state:Mapped[str]=mapped_column(String(20),index=True)
 created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
 published_by:Mapped[str|None]=mapped_column(String(64),nullable=True);published_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
 retired_by:Mapped[str|None]=mapped_column(String(64),nullable=True);retired_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)

def convert(r):
 return OfficialDocument(r.id,r.institution_id,r.student_id,r.service_request_id,r.serial_number,r.kind,r.title,r.sha256_hex,r.pdf_bytes,r.verification_token_hash,DocumentState(r.state),r.issued_by,r.issued_at,r.revoked_by,r.revoked_at,r.revocation_reason,r.source_evidence_hash,r.source_jury_outcome_id,r.replaces_document_id,r.issuer_name,r.issuer_legal_name,r.issuer_country_code,r.template_version) if r else None
class SqlOfficialDocumentRepository:
 def __init__(self,sf):self.sf=sf
 def get(self,i,d):
  with self.sf() as s:return convert(s.scalar(select(OfficialDocumentRow).where(OfficialDocumentRow.institution_id==i,OfficialDocumentRow.id==d)))
 def by_request(self,i,r):
  with self.sf() as s:return convert(s.scalar(select(OfficialDocumentRow).where(OfficialDocumentRow.institution_id==i,OfficialDocumentRow.service_request_id==r)))
 def by_token_hash(self,h):
  with self.sf() as s:return convert(s.scalar(select(OfficialDocumentRow).where(OfficialDocumentRow.verification_token_hash==h)))
 def issue_with_fulfillment(self,doc,request,expected,event,document_event=None):
  from app.modules.service_desk.infrastructure.sqlalchemy_repo import ServiceRequestRow,RequestEventRow
  with self.sf() as s:
   q=s.execute(update(ServiceRequestRow).where(ServiceRequestRow.id==request.id,ServiceRequestRow.institution_id==request.institution_id,ServiceRequestRow.version==expected,ServiceRequestRow.state=='approved').values(state='fulfilled',output_document_ref=doc.id,output_sha256=doc.sha256_hex,version=request.version,updated_at=request.updated_at))
   if q.rowcount!=1:raise ValueError('official_document_request_concurrent_change')
   s.add(OfficialDocumentRow(**{**doc.__dict__,'state':doc.state.value}));s.add(RequestEventRow(**event.__dict__));
   if document_event:s.add(OfficialDocumentEventRow(**document_event.__dict__))
   s.commit()
 def revoke(self,i,d,actor,reason,now,event=None):
  with self.sf() as s:
   q=s.execute(update(OfficialDocumentRow).where(OfficialDocumentRow.institution_id==i,OfficialDocumentRow.id==d,OfficialDocumentRow.state=='issued').values(state='revoked',revoked_by=actor,revoked_at=now,revocation_reason=reason))
   if q.rowcount!=1:raise ValueError('official_document_not_active')
   if event:s.add(OfficialDocumentEventRow(**event.__dict__))
   s.commit()

 def active_template(self,i,kind):
  with self.sf() as s:
   r=s.scalar(select(OfficialDocumentTemplateRow).where(OfficialDocumentTemplateRow.institution_id==i,OfficialDocumentTemplateRow.kind==kind,OfficialDocumentTemplateRow.state=='published').order_by(OfficialDocumentTemplateRow.published_at.desc(),OfficialDocumentTemplateRow.id.desc()))
   return OfficialDocumentTemplate(r.id,r.institution_id,r.kind,r.version,r.name,TemplateState(r.state),r.created_by,r.created_at,r.published_by,r.published_at,r.retired_by,r.retired_at) if r else None
 def create_template(self,t):
  with self.sf() as s:s.add(OfficialDocumentTemplateRow(**{**t.__dict__,'state':t.state.value}));s.commit()
 def publish_template(self,i,tid,actor,now):
  with self.sf() as s:
   row=s.scalar(select(OfficialDocumentTemplateRow).where(OfficialDocumentTemplateRow.institution_id==i,OfficialDocumentTemplateRow.id==tid))
   if not row or row.state!='draft':raise ValueError('official_document_template_not_draft')
   s.execute(update(OfficialDocumentTemplateRow).where(OfficialDocumentTemplateRow.institution_id==i,OfficialDocumentTemplateRow.kind==row.kind,OfficialDocumentTemplateRow.state=='published').values(state='retired',retired_by=actor,retired_at=now))
   row.state='published';row.published_by=actor;row.published_at=now;s.commit()
 def replace_with_fulfillment(self,doc,request,expected,event,document_event,original_id,actor,reason,now):
  from app.modules.service_desk.infrastructure.sqlalchemy_repo import ServiceRequestRow,RequestEventRow
  with self.sf() as s:
   q=s.execute(update(ServiceRequestRow).where(ServiceRequestRow.id==request.id,ServiceRequestRow.institution_id==request.institution_id,ServiceRequestRow.version==expected,ServiceRequestRow.state=='approved').values(state='fulfilled',output_document_ref=doc.id,output_sha256=doc.sha256_hex,version=request.version,updated_at=request.updated_at))
   if q.rowcount!=1:raise ValueError('official_document_request_concurrent_change')
   q=s.execute(update(OfficialDocumentRow).where(OfficialDocumentRow.institution_id==doc.institution_id,OfficialDocumentRow.id==original_id,OfficialDocumentRow.state=='issued').values(state='revoked',revoked_by=actor,revoked_at=now,revocation_reason=reason))
   if q.rowcount!=1:raise ValueError('official_document_replacement_source_not_active')
   s.add(OfficialDocumentRow(**{**doc.__dict__,'state':doc.state.value}));s.add(RequestEventRow(**event.__dict__));s.add(OfficialDocumentEventRow(**document_event.__dict__));s.add(OfficialDocumentEventRow(id=__import__('uuid').uuid4().hex,institution_id=doc.institution_id,document_id=original_id,actor_id=actor,event_type='superseded',reason=reason,created_at=now));s.commit()
 def events(self,i,d):
  with self.sf() as s:
   rows=s.scalars(select(OfficialDocumentEventRow).where(OfficialDocumentEventRow.institution_id==i,OfficialDocumentEventRow.document_id==d).order_by(OfficialDocumentEventRow.created_at,OfficialDocumentEventRow.id)).all()
   return [OfficialDocumentEvent(r.id,r.institution_id,r.document_id,r.actor_id,r.event_type,r.reason,r.created_at) for r in rows]

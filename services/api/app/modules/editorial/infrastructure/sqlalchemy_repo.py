from __future__ import annotations
from datetime import UTC, datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func, or_, select, update
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base
from app.modules.editorial.domain.model import *

class EditorialMemberRow(Base):
    __tablename__='editorial_members'
    account_id:Mapped[str]=mapped_column(String(64),primary_key=True)
    role:Mapped[str]=mapped_column(String(32),index=True)
    active:Mapped[bool]=mapped_column(Boolean,default=True,index=True)
class EditorialItemRow(Base):
    __tablename__='editorial_items'
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    kind:Mapped[str]=mapped_column(String(40),index=True)
    title:Mapped[str]=mapped_column(String(240),index=True)
    faculty_domain:Mapped[str]=mapped_column(String(120),index=True)
    program:Mapped[str]=mapped_column(String(160),index=True)
    level:Mapped[str]=mapped_column(String(80),index=True)
    semester:Mapped[str|None]=mapped_column(String(80),nullable=True,index=True)
    state:Mapped[str]=mapped_column(String(40),index=True)
    risk:Mapped[str]=mapped_column(String(40),index=True)
    rights_status:Mapped[str]=mapped_column(String(40),index=True)
    rights_note:Mapped[str]=mapped_column(Text,default='')
    source_fingerprint:Mapped[str]=mapped_column(String(128),default='',index=True)
    created_by:Mapped[str]=mapped_column(String(64),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    current_revision_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True)
    published_revision_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True)
    row_version:Mapped[int]=mapped_column(Integer,default=1,index=True)
class EditorialRevisionRow(Base):
    __tablename__='editorial_revisions'
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    item_id:Mapped[str]=mapped_column(String(64),index=True)
    revision_no:Mapped[int]=mapped_column(Integer,index=True)
    payload_json:Mapped[str]=mapped_column(Text)
    source_fingerprint:Mapped[str]=mapped_column(String(128),index=True)
    ai_generated:Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    prompt_version:Mapped[str|None]=mapped_column(String(80),nullable=True)
    created_by:Mapped[str]=mapped_column(String(64),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    note:Mapped[str]=mapped_column(Text,default='')
class EditorialReviewRow(Base):
    __tablename__='editorial_reviews'
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    item_id:Mapped[str]=mapped_column(String(64),index=True)
    revision_id:Mapped[str]=mapped_column(String(64),index=True)
    reviewer_id:Mapped[str]=mapped_column(String(64),index=True)
    decision:Mapped[str]=mapped_column(String(40),index=True)
    comment:Mapped[str]=mapped_column(Text,default='')
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    checklist_json:Mapped[str]=mapped_column(Text,default='{}')
    quality_score:Mapped[int|None]=mapped_column(Integer,nullable=True)
class EditorialSourceRow(Base):
    __tablename__='editorial_sources'
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    item_id:Mapped[str]=mapped_column(String(64),index=True)
    filename:Mapped[str]=mapped_column(String(260))
    mime_type:Mapped[str|None]=mapped_column(String(120),nullable=True)
    checksum_sha256:Mapped[str]=mapped_column(String(64),index=True)
    size_bytes:Mapped[int|None]=mapped_column(Integer,nullable=True)
    storage_locator:Mapped[str|None]=mapped_column(String(512),nullable=True)
    ocr_confidence:Mapped[str|None]=mapped_column(String(32),nullable=True)
    human_verified:Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    imported_by:Mapped[str]=mapped_column(String(64),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
class EditorialPublicationRow(Base):
    __tablename__='editorial_publications'
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    item_id:Mapped[str]=mapped_column(String(64),index=True)
    revision_id:Mapped[str]=mapped_column(String(64),index=True)
    publisher_id:Mapped[str]=mapped_column(String(64),index=True)
    published_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    changelog:Mapped[str]=mapped_column(Text,default='')
class EditorialAssignmentRow(Base):
    __tablename__='editorial_assignments'
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    item_id:Mapped[str]=mapped_column(String(64),index=True)
    stage:Mapped[str]=mapped_column(String(32),index=True)
    assignee_id:Mapped[str]=mapped_column(String(64),index=True)
    assigned_by:Mapped[str]=mapped_column(String(64),index=True)
    due_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True,index=True)
    active:Mapped[bool]=mapped_column(Boolean,default=True,index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)

def _utc(x): return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class SqlAlchemyEditorialRepository:
    def __init__(self,session_factory): self.session_factory=session_factory
    def get_member(self,a):
        with self.session_factory() as s:
            r=s.get(EditorialMemberRow,a); return EditorialMember(r.account_id,EditorialRole(r.role),r.active) if r else None
    def save_member(self,m):
        with self.session_factory() as s: s.merge(EditorialMemberRow(account_id=m.account_id,role=m.role.value,active=m.active)); s.commit()
    def list_members(self):
        with self.session_factory() as s:
            return tuple(EditorialMember(r.account_id,EditorialRole(r.role),r.active) for r in s.scalars(select(EditorialMemberRow).order_by(EditorialMemberRow.role,EditorialMemberRow.account_id)).all())
    def get_item(self,i):
        with self.session_factory() as s:
            r=s.get(EditorialItemRow,i); return self._item(r) if r else None
    def find_item_by_source_fingerprint(self,fingerprint):
        with self.session_factory() as s:
            r=s.scalar(select(EditorialItemRow).where(EditorialItemRow.source_fingerprint==fingerprint).order_by(EditorialItemRow.created_at).limit(1)); return self._item(r) if r else None
    def save_item(self,i,expected_version=None):
        with self.session_factory() as s:
            existing=s.get(EditorialItemRow,i.id)
            data=dict(kind=i.kind.value,title=i.title,faculty_domain=i.faculty_domain,program=i.program,level=i.level,semester=i.semester,state=i.state.value,risk=i.risk.value,rights_status=i.rights_status.value,rights_note=i.rights_note,source_fingerprint=i.source_fingerprint,created_by=i.created_by,created_at=i.created_at,updated_at=i.updated_at,current_revision_id=i.current_revision_id,published_revision_id=i.published_revision_id,row_version=i.row_version)
            if existing is None:
                s.add(EditorialItemRow(id=i.id,**data)); s.commit(); return
            if expected_version is None:
                for k,v in data.items(): setattr(existing,k,v)
                s.commit(); return
            result=s.execute(update(EditorialItemRow).where(EditorialItemRow.id==i.id,EditorialItemRow.row_version==int(expected_version)).values(**data))
            if result.rowcount!=1:
                s.rollback(); raise ValueError('editorial_concurrent_modification')
            s.commit()
    def list_items(self,state=None,limit=100):
        return self.search_items(state=state,limit=limit,offset=0)[0]
    def search_items(self,*,query=None,state=None,kind=None,risk=None,rights_status=None,limit=100,offset=0):
        with self.session_factory() as s:
            where=[]
            if state: where.append(EditorialItemRow.state==(state.value if hasattr(state,'value') else str(state)))
            if kind: where.append(EditorialItemRow.kind==(kind.value if hasattr(kind,'value') else str(kind)))
            if risk: where.append(EditorialItemRow.risk==(risk.value if hasattr(risk,'value') else str(risk)))
            if rights_status: where.append(EditorialItemRow.rights_status==(rights_status.value if hasattr(rights_status,'value') else str(rights_status)))
            if query:
                q=f"%{str(query).strip().lower()}%"
                where.append(or_(func.lower(EditorialItemRow.title).like(q),func.lower(EditorialItemRow.program).like(q),func.lower(EditorialItemRow.faculty_domain).like(q),func.lower(EditorialItemRow.level).like(q)))
            base=select(EditorialItemRow)
            count_q=select(func.count()).select_from(EditorialItemRow)
            for w in where: base=base.where(w); count_q=count_q.where(w)
            total=int(s.scalar(count_q) or 0)
            rows=s.scalars(base.order_by(EditorialItemRow.updated_at.desc()).offset(max(0,int(offset))).limit(max(1,min(int(limit),200)))).all()
            return tuple(self._item(r) for r in rows), total
    def get_revision(self,i):
        with self.session_factory() as s:
            r=s.get(EditorialRevisionRow,i); return self._rev(r) if r else None
    def list_revisions(self,item_id):
        with self.session_factory() as s:return tuple(self._rev(r) for r in s.scalars(select(EditorialRevisionRow).where(EditorialRevisionRow.item_id==item_id).order_by(EditorialRevisionRow.revision_no)).all())
    def save_revision(self,r):
        with self.session_factory() as s:s.add(EditorialRevisionRow(id=r.id,item_id=r.item_id,revision_no=r.revision_no,payload_json=r.payload_json,source_fingerprint=r.source_fingerprint,ai_generated=r.ai_generated,prompt_version=r.prompt_version,created_by=r.created_by,created_at=r.created_at,note=r.note));s.commit()
    def save_review(self,r):
        with self.session_factory() as s:s.add(EditorialReviewRow(id=r.id,item_id=r.item_id,revision_id=r.revision_id,reviewer_id=r.reviewer_id,decision=r.decision,comment=r.comment,created_at=r.created_at,checklist_json=r.checklist_json,quality_score=r.quality_score));s.commit()
    def list_reviews(self,item_id):
        with self.session_factory() as s:
            rs=s.scalars(select(EditorialReviewRow).where(EditorialReviewRow.item_id==item_id).order_by(EditorialReviewRow.created_at)).all(); return tuple(ReviewDecision(r.id,r.item_id,r.revision_id,r.reviewer_id,r.decision,r.comment,_utc(r.created_at),r.checklist_json,r.quality_score) for r in rs)
    def save_source(self,src):
        with self.session_factory() as s:
            s.merge(EditorialSourceRow(id=src.id,item_id=src.item_id,filename=src.filename,mime_type=src.mime_type,checksum_sha256=src.checksum_sha256,size_bytes=src.size_bytes,storage_locator=src.storage_locator,ocr_confidence=None if src.ocr_confidence is None else str(src.ocr_confidence),human_verified=src.human_verified,imported_by=src.imported_by,created_at=src.created_at)); s.commit()
    def list_sources(self,item_id):
        with self.session_factory() as s:
            rs=s.scalars(select(EditorialSourceRow).where(EditorialSourceRow.item_id==item_id).order_by(EditorialSourceRow.created_at)).all(); return tuple(EditorialSource(r.id,r.item_id,r.filename,r.mime_type,r.checksum_sha256,r.size_bytes,r.storage_locator,None if r.ocr_confidence is None else float(r.ocr_confidence),r.human_verified,r.imported_by,_utc(r.created_at)) for r in rs)
    def get_source(self,source_id):
        with self.session_factory() as s:
            r=s.get(EditorialSourceRow,source_id); return EditorialSource(r.id,r.item_id,r.filename,r.mime_type,r.checksum_sha256,r.size_bytes,r.storage_locator,None if r.ocr_confidence is None else float(r.ocr_confidence),r.human_verified,r.imported_by,_utc(r.created_at)) if r else None
    def find_source_by_checksum(self,checksum):
        with self.session_factory() as s:
            r=s.scalar(select(EditorialSourceRow).where(EditorialSourceRow.checksum_sha256==checksum).limit(1)); return EditorialSource(r.id,r.item_id,r.filename,r.mime_type,r.checksum_sha256,r.size_bytes,r.storage_locator,None if r.ocr_confidence is None else float(r.ocr_confidence),r.human_verified,r.imported_by,_utc(r.created_at)) if r else None
    def save_publication(self,r):
        with self.session_factory() as s:s.add(EditorialPublicationRow(id=r.id,item_id=r.item_id,revision_id=r.revision_id,publisher_id=r.publisher_id,published_at=r.published_at,changelog=r.changelog));s.commit()
    def list_publications(self,item_id):
        with self.session_factory() as s:
            rs=s.scalars(select(EditorialPublicationRow).where(EditorialPublicationRow.item_id==item_id).order_by(EditorialPublicationRow.published_at)).all(); return tuple(PublicationRecord(r.id,r.item_id,r.revision_id,r.publisher_id,_utc(r.published_at),r.changelog) for r in rs)
    def save_assignment(self,a):
        with self.session_factory() as s:
            if a.active:
                rows=s.scalars(select(EditorialAssignmentRow).where(EditorialAssignmentRow.item_id==a.item_id,EditorialAssignmentRow.stage==a.stage.value,EditorialAssignmentRow.active==True)).all()
                for r in rows:r.active=False
            s.add(EditorialAssignmentRow(id=a.id,item_id=a.item_id,stage=a.stage.value,assignee_id=a.assignee_id,assigned_by=a.assigned_by,due_at=a.due_at,active=a.active,created_at=a.created_at)); s.commit()
    def list_assignments(self,item_id=None,assignee_id=None,active_only=False):
        with self.session_factory() as s:
            q=select(EditorialAssignmentRow)
            if item_id:q=q.where(EditorialAssignmentRow.item_id==item_id)
            if assignee_id:q=q.where(EditorialAssignmentRow.assignee_id==assignee_id)
            if active_only:q=q.where(EditorialAssignmentRow.active==True)
            rs=s.scalars(q.order_by(EditorialAssignmentRow.created_at.desc())).all()
            return tuple(EditorialAssignment(r.id,r.item_id,AssignmentStage(r.stage),r.assignee_id,r.assigned_by,_utc(r.due_at),r.active,_utc(r.created_at)) for r in rs)
    def complete_assignment(self,item_id,stage):
        with self.session_factory() as s:
            rows=s.scalars(select(EditorialAssignmentRow).where(EditorialAssignmentRow.item_id==item_id,EditorialAssignmentRow.stage==(stage.value if hasattr(stage,'value') else str(stage)),EditorialAssignmentRow.active==True)).all()
            for r in rows:r.active=False
            s.commit()

    def get_active_assignment(self,item_id,stage):
        with self.session_factory() as s:
            r=s.scalar(select(EditorialAssignmentRow).where(EditorialAssignmentRow.item_id==item_id,EditorialAssignmentRow.stage==(stage.value if hasattr(stage,'value') else str(stage)),EditorialAssignmentRow.active==True).order_by(EditorialAssignmentRow.created_at.desc()).limit(1))
            return EditorialAssignment(r.id,r.item_id,AssignmentStage(r.stage),r.assignee_id,r.assigned_by,_utc(r.due_at),r.active,_utc(r.created_at)) if r else None
    @staticmethod
    def _item(r): return EditorialItem(r.id,ContentKind(r.kind),r.title,r.faculty_domain,r.program,r.level,r.semester,EditorialState(r.state),RiskLevel(r.risk),RightsStatus(r.rights_status),r.rights_note,r.source_fingerprint,r.created_by,_utc(r.created_at),_utc(r.updated_at),r.current_revision_id,r.published_revision_id,r.row_version)
    @staticmethod
    def _rev(r): return EditorialRevision(r.id,r.item_id,r.revision_no,r.payload_json,r.source_fingerprint,r.ai_generated,r.prompt_version,r.created_by,_utc(r.created_at),r.note)

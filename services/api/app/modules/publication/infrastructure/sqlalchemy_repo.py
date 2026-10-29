from __future__ import annotations
from datetime import UTC
from sqlalchemy import String, Text, Integer, Boolean, DateTime, select, func
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.publication.domain.model import PublicationRelease,ReleaseState,RolloutMode,CatalogSnapshot
class PublicationReleaseRow(Base):
    __tablename__="publication_releases"
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    editorial_item_id:Mapped[str]=mapped_column(String(64),index=True)
    editorial_revision_id:Mapped[str]=mapped_column(String(64),index=True)
    state:Mapped[str]=mapped_column(String(24),index=True)
    version_label:Mapped[str]=mapped_column(String(120))
    placement_json:Mapped[str]=mapped_column(Text)
    audience_json:Mapped[str]=mapped_column(Text,default="{}")
    rollout_mode:Mapped[str]=mapped_column(String(24),default="all")
    rollout_percentage:Mapped[int]=mapped_column(Integer,default=100)
    premium_required:Mapped[bool]=mapped_column(Boolean,default=True)
    offline_allowed:Mapped[bool]=mapped_column(Boolean,default=True)
    scheduled_at:Mapped[object]=mapped_column(DateTime(timezone=True),nullable=True,index=True)
    published_at:Mapped[object]=mapped_column(DateTime(timezone=True),nullable=True,index=True)
    withdrawn_at:Mapped[object]=mapped_column(DateTime(timezone=True),nullable=True)
    created_by:Mapped[str]=mapped_column(String(64),index=True)
    created_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True)
    row_version:Mapped[int]=mapped_column(Integer,default=1)
class CatalogSnapshotRow(Base):
    __tablename__="publication_catalog_snapshots"
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    release_id:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    manifest_sha256:Mapped[str]=mapped_column(String(64),index=True)
    manifest_json:Mapped[str]=mapped_column(Text)
    created_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True)
def _utc(v): return v if v is None or v.tzinfo else v.replace(tzinfo=UTC)
def _release(r): return PublicationRelease(id=r.id,editorial_item_id=r.editorial_item_id,editorial_revision_id=r.editorial_revision_id,state=ReleaseState(r.state),version_label=r.version_label,placement_json=r.placement_json,audience_json=r.audience_json,rollout_mode=RolloutMode(r.rollout_mode),rollout_percentage=r.rollout_percentage,premium_required=r.premium_required,offline_allowed=r.offline_allowed,scheduled_at=_utc(r.scheduled_at),published_at=_utc(r.published_at),withdrawn_at=_utc(r.withdrawn_at),created_by=r.created_by,created_at=_utc(r.created_at),row_version=r.row_version)
class SqlAlchemyPublicationRepository:
    def __init__(self,sf): self.sf=sf
    def save(self,r):
      with self.sf() as s:
       s.merge(PublicationReleaseRow(**r.__dict__,state=r.state.value,rollout_mode=r.rollout_mode.value)); s.commit()
    def get(self,id):
      with self.sf() as s:
       r=s.get(PublicationReleaseRow,id); return _release(r) if r else None
    def list(self,state=None,limit=200):
      with self.sf() as s:
       q=select(PublicationReleaseRow)
       if state:q=q.where(PublicationReleaseRow.state==state.value)
       rows=s.scalars(q.order_by(PublicationReleaseRow.created_at.desc()).limit(limit)).all(); return tuple(_release(x) for x in rows)
    def due(self,now,limit=100):
      with self.sf() as s:
       rows=s.scalars(select(PublicationReleaseRow).where(PublicationReleaseRow.state=="scheduled",PublicationReleaseRow.scheduled_at<=now).order_by(PublicationReleaseRow.scheduled_at).limit(limit)).all(); return tuple(_release(x) for x in rows)
    def save_snapshot(self,x):
      with self.sf() as s: s.merge(CatalogSnapshotRow(**x.__dict__)); s.commit()
    def snapshot(self,release_id):
      with self.sf() as s:
       r=s.scalar(select(CatalogSnapshotRow).where(CatalogSnapshotRow.release_id==release_id)); return CatalogSnapshot(id=r.id,release_id=r.release_id,manifest_sha256=r.manifest_sha256,manifest_json=r.manifest_json,created_at=_utc(r.created_at)) if r else None
    def dashboard(self):
      with self.sf() as s:
       rows=s.execute(select(PublicationReleaseRow.state,func.count()).group_by(PublicationReleaseRow.state)).all(); return {k:int(v) for k,v in rows}

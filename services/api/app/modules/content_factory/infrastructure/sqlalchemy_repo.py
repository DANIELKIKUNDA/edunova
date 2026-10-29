from __future__ import annotations
from datetime import UTC, datetime
from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base
from ..domain.model import FactoryRun,FactoryAsset,EvidenceLink,QualityGate,FactoryState,AssetKind,GateSeverity

def _utc(v): return v if v is None or v.tzinfo else v.replace(tzinfo=UTC)
class FactoryRunRow(Base):
    __tablename__='content_factory_runs'; __table_args__=(UniqueConstraint('ingestion_document_id','pipeline_version','requested_assets_json',name='uq_factory_run_idempotency'),)
    id:Mapped[str]=mapped_column(String(64),primary_key=True); ingestion_document_id:Mapped[str]=mapped_column(String(64),index=True); editorial_item_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True); requested_by:Mapped[str]=mapped_column(String(64),index=True); state:Mapped[str]=mapped_column(String(40),index=True); pipeline_version:Mapped[str]=mapped_column(String(80),index=True); prompt_version:Mapped[str]=mapped_column(String(80)); source_sha256:Mapped[str]=mapped_column(String(64),index=True); academic_context_json:Mapped[str]=mapped_column(Text); requested_assets_json:Mapped[str]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True); started_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); lease_owner:Mapped[str|None]=mapped_column(String(160),nullable=True,index=True); lease_expires_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True,index=True); attempt:Mapped[int]=mapped_column(Integer,default=0); max_attempts:Mapped[int]=mapped_column(Integer,default=3); last_error:Mapped[str|None]=mapped_column(Text,nullable=True); quality_score:Mapped[int|None]=mapped_column(Integer,nullable=True)
class FactoryAssetRow(Base):
    __tablename__='content_factory_assets'; __table_args__=(UniqueConstraint('run_id','kind','ordinal',name='uq_factory_asset_ordinal'),)
    id:Mapped[str]=mapped_column(String(64),primary_key=True); run_id:Mapped[str]=mapped_column(String(64),index=True); kind:Mapped[str]=mapped_column(String(40),index=True); ordinal:Mapped[int]=mapped_column(Integer); title:Mapped[str]=mapped_column(String(320)); payload_json:Mapped[str]=mapped_column(Text); content_sha256:Mapped[str]=mapped_column(String(64),index=True); confidence:Mapped[float]=mapped_column(Float); status:Mapped[str]=mapped_column(String(40),index=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
class FactoryEvidenceRow(Base):
    __tablename__='content_factory_evidence'; id:Mapped[str]=mapped_column(String(64),primary_key=True); run_id:Mapped[str]=mapped_column(String(64),index=True); asset_id:Mapped[str]=mapped_column(String(64),index=True); source_document_id:Mapped[str]=mapped_column(String(64),index=True); page_start:Mapped[int]=mapped_column(Integer); page_end:Mapped[int]=mapped_column(Integer); quote:Mapped[str]=mapped_column(Text); quote_sha256:Mapped[str]=mapped_column(String(64),index=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
class FactoryGateRow(Base):
    __tablename__='content_factory_quality_gates'; id:Mapped[str]=mapped_column(String(64),primary_key=True); run_id:Mapped[str]=mapped_column(String(64),index=True); code:Mapped[str]=mapped_column(String(120),index=True); severity:Mapped[str]=mapped_column(String(30)); passed:Mapped[int]=mapped_column(Integer,index=True); detail:Mapped[str]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)

def run_from(r): return FactoryRun(r.id,r.ingestion_document_id,r.editorial_item_id,r.requested_by,FactoryState(r.state),r.pipeline_version,r.prompt_version,r.source_sha256,r.academic_context_json,r.requested_assets_json,_utc(r.created_at),_utc(r.updated_at),_utc(r.started_at),_utc(r.completed_at),r.lease_owner,_utc(r.lease_expires_at),r.attempt,r.max_attempts,r.last_error,r.quality_score)
def asset_from(r): return FactoryAsset(r.id,r.run_id,AssetKind(r.kind),r.ordinal,r.title,r.payload_json,r.content_sha256,r.confidence,r.status,_utc(r.created_at))
def evidence_from(r): return EvidenceLink(r.id,r.run_id,r.asset_id,r.source_document_id,r.page_start,r.page_end,r.quote,r.quote_sha256,_utc(r.created_at))
def gate_from(r): return QualityGate(r.id,r.run_id,r.code,GateSeverity(r.severity),bool(r.passed),r.detail,_utc(r.created_at))
class SqlAlchemyContentFactoryRepository:
    def __init__(self,sf): self.sf=sf
    def save_run(self,x):
        with self.sf() as s: s.merge(FactoryRunRow(**{**{f:getattr(x,f) for f in x.__dataclass_fields__},'state':x.state.value})); s.commit()
    def get_run(self,id):
        with self.sf() as s: r=s.get(FactoryRunRow,id); return run_from(r) if r else None
    def find_idempotent(self,doc,pipeline,assets):
        with self.sf() as s: r=s.scalar(select(FactoryRunRow).where(FactoryRunRow.ingestion_document_id==doc,FactoryRunRow.pipeline_version==pipeline,FactoryRunRow.requested_assets_json==assets)); return run_from(r) if r else None
    def list_runs(self,limit=100):
        with self.sf() as s: return tuple(run_from(x) for x in s.scalars(select(FactoryRunRow).order_by(FactoryRunRow.created_at.desc()).limit(limit)).all())
    def save_asset(self,x):
        with self.sf() as s: s.merge(FactoryAssetRow(**{**{f:getattr(x,f) for f in x.__dataclass_fields__},'kind':x.kind.value})); s.commit()
    def save_evidence(self,x):
        with self.sf() as s: s.merge(FactoryEvidenceRow(**{f:getattr(x,f) for f in x.__dataclass_fields__})); s.commit()
    def save_gate(self,x):
        with self.sf() as s: s.merge(FactoryGateRow(**{**{f:getattr(x,f) for f in x.__dataclass_fields__},'severity':x.severity.value,'passed':1 if x.passed else 0})); s.commit()
    def assets(self,run_id):
        with self.sf() as s: return tuple(asset_from(x) for x in s.scalars(select(FactoryAssetRow).where(FactoryAssetRow.run_id==run_id).order_by(FactoryAssetRow.kind,FactoryAssetRow.ordinal)).all())
    def evidence(self,run_id):
        with self.sf() as s: return tuple(evidence_from(x) for x in s.scalars(select(FactoryEvidenceRow).where(FactoryEvidenceRow.run_id==run_id)).all())
    def gates(self,run_id):
        with self.sf() as s: return tuple(gate_from(x) for x in s.scalars(select(FactoryGateRow).where(FactoryGateRow.run_id==run_id)).all())

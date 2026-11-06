from __future__ import annotations
from sqlalchemy import String,Integer,Text,DateTime,select
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.knowledge_graph.domain.model import *
class NodeRow(Base):
 __tablename__='knowledge_graph_nodes';id:Mapped[str]=mapped_column(String(64),primary_key=True);tenant_id:Mapped[str]=mapped_column(String(64),index=True);kind:Mapped[str]=mapped_column(String(32),index=True);label:Mapped[str]=mapped_column(String(300));description:Mapped[str]=mapped_column(Text);course_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);source_revision_id:Mapped[str|None]=mapped_column(String(64),nullable=True);source_locator:Mapped[str|None]=mapped_column(String(255),nullable=True);provenance_sha256:Mapped[str|None]=mapped_column(String(64),nullable=True);state:Mapped[str]=mapped_column(String(24),index=True);origin:Mapped[str]=mapped_column(String(24));version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class ExtractionBatchRow(Base):
 __tablename__='knowledge_graph_extraction_batches';id:Mapped[str]=mapped_column(String(64),primary_key=True);tenant_id:Mapped[str]=mapped_column(String(64),index=True);source_revision_id:Mapped[str]=mapped_column(String(64),index=True);source_sha256:Mapped[str]=mapped_column(String(64));course_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);state:Mapped[str]=mapped_column(String(24),index=True);created_by:Mapped[str]=mapped_column(String(64));reviewed_by:Mapped[str|None]=mapped_column(String(64),nullable=True);candidate_count:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class ExtractionCandidateRow(Base):
 __tablename__='knowledge_graph_extraction_candidates';id:Mapped[str]=mapped_column(String(64),primary_key=True);batch_id:Mapped[str]=mapped_column(String(64),index=True);tenant_id:Mapped[str]=mapped_column(String(64),index=True);candidate_type:Mapped[str]=mapped_column(String(24));label:Mapped[str]=mapped_column(String(300));source_label:Mapped[str|None]=mapped_column(String(300),nullable=True);target_label:Mapped[str|None]=mapped_column(String(300),nullable=True);kind:Mapped[str]=mapped_column(String(32));rationale:Mapped[str]=mapped_column(Text);source_locator:Mapped[str]=mapped_column(String(255));confidence:Mapped[int]=mapped_column(Integer);fingerprint:Mapped[str]=mapped_column(String(64),index=True);state:Mapped[str]=mapped_column(String(24),index=True);created_node_id:Mapped[str|None]=mapped_column(String(64),nullable=True);created_relation_id:Mapped[str|None]=mapped_column(String(64),nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SnapshotRow(Base):
 __tablename__='knowledge_graph_snapshots';id:Mapped[str]=mapped_column(String(64),primary_key=True);tenant_id:Mapped[str]=mapped_column(String(64),index=True);sequence:Mapped[int]=mapped_column(Integer);content_sha256:Mapped[str]=mapped_column(String(64));node_count:Mapped[int]=mapped_column(Integer);relation_count:Mapped[int]=mapped_column(Integer);reason:Mapped[str]=mapped_column(String(255));created_by:Mapped[str]=mapped_column(String(64));state:Mapped[str]=mapped_column(String(24),index=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class ImpactRow(Base):
 __tablename__='knowledge_graph_impacts';id:Mapped[str]=mapped_column(String(64),primary_key=True);tenant_id:Mapped[str]=mapped_column(String(64),index=True);relation_id:Mapped[str]=mapped_column(String(64),index=True);change_kind:Mapped[str]=mapped_column(String(32));affected_concept_id:Mapped[str]=mapped_column(String(64),index=True);distance:Mapped[int]=mapped_column(Integer);path:Mapped[str]=mapped_column(Text);snapshot_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class RelationRow(Base):
 __tablename__='knowledge_graph_relations';id:Mapped[str]=mapped_column(String(64),primary_key=True);tenant_id:Mapped[str]=mapped_column(String(64),index=True);source_id:Mapped[str]=mapped_column(String(64),index=True);target_id:Mapped[str]=mapped_column(String(64),index=True);kind:Mapped[str]=mapped_column(String(32),index=True);rationale:Mapped[str]=mapped_column(Text);confidence:Mapped[int]=mapped_column(Integer);state:Mapped[str]=mapped_column(String(24),index=True);origin:Mapped[str]=mapped_column(String(24));source_revision_id:Mapped[str|None]=mapped_column(String(64),nullable=True);provenance_sha256:Mapped[str|None]=mapped_column(String(64),nullable=True);version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));validated_by:Mapped[str|None]=mapped_column(String(64),nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
def _n(r):return KnowledgeNode(r.id,r.tenant_id,NodeKind(r.kind),r.label,r.description,r.course_id,r.source_revision_id,r.source_locator,r.provenance_sha256,GovernanceState(r.state),Origin(r.origin),r.version,r.created_at,r.updated_at)
def _b(r):return ExtractionBatch(r.id,r.tenant_id,r.source_revision_id,r.source_sha256,r.course_id,ExtractionState(r.state),r.created_by,r.reviewed_by,r.candidate_count,r.created_at,r.updated_at)
def _c(r):return ExtractionCandidate(r.id,r.batch_id,r.tenant_id,r.candidate_type,r.label,r.source_label,r.target_label,r.kind,r.rationale,r.source_locator,r.confidence,r.fingerprint,ExtractionState(r.state),r.created_node_id,r.created_relation_id,r.created_at,r.updated_at)
def _s(r):return GraphSnapshot(r.id,r.tenant_id,r.sequence,r.content_sha256,r.node_count,r.relation_count,r.reason,r.created_by,SnapshotState(r.state),r.created_at)
def _i(r):
 import json
 return GraphImpact(r.id,r.tenant_id,r.relation_id,r.change_kind,r.affected_concept_id,r.distance,tuple(json.loads(r.path)),r.snapshot_id,r.created_at)
def _r(r):return KnowledgeRelation(r.id,r.tenant_id,r.source_id,r.target_id,RelationKind(r.kind),r.rationale,r.confidence,GovernanceState(r.state),Origin(r.origin),r.source_revision_id,r.provenance_sha256,r.version,r.created_by,r.validated_by,r.created_at,r.updated_at)
class SqlAlchemyKnowledgeGraphRepository:
 def __init__(self,sf):self.sf=sf
 def save_node(self,x):
  d=x.__dict__.copy();d.update(kind=x.kind.value,state=x.state.value,origin=x.origin.value)
  with self.sf() as s:s.merge(NodeRow(**d));s.commit()
 def node(self,t,id):
  with self.sf() as s:r=s.get(NodeRow,id);return _n(r) if r and r.tenant_id==t else None
 def save_relation(self,x):
  d=x.__dict__.copy();d.update(kind=x.kind.value,state=x.state.value,origin=x.origin.value)
  with self.sf() as s:s.merge(RelationRow(**d));s.commit()
 def relation(self,t,id):
  with self.sf() as s:r=s.get(RelationRow,id);return _r(r) if r and r.tenant_id==t else None
 def relations(self,t):
  with self.sf() as s:return tuple(_r(r) for r in s.scalars(select(RelationRow).where(RelationRow.tenant_id==t)).all())
 def nodes(self,t):
  with self.sf() as s:return tuple(_n(r) for r in s.scalars(select(NodeRow).where(NodeRow.tenant_id==t)).all())
 def save_batch(self,x):
  d=x.__dict__.copy();d.update(state=x.state.value)
  with self.sf() as s:s.merge(ExtractionBatchRow(**d));s.commit()
 def batch(self,t,id):
  with self.sf() as s:r=s.get(ExtractionBatchRow,id);return _b(r) if r and r.tenant_id==t else None
 def save_candidate(self,x):
  d=x.__dict__.copy();d.update(state=x.state.value)
  with self.sf() as s:s.merge(ExtractionCandidateRow(**d));s.commit()
 def candidate(self,t,id):
  with self.sf() as s:r=s.get(ExtractionCandidateRow,id);return _c(r) if r and r.tenant_id==t else None
 def all_candidates(self,t):
  with self.sf() as s:return tuple(_c(r) for r in s.scalars(select(ExtractionCandidateRow).where(ExtractionCandidateRow.tenant_id==t)).all())

 def save_snapshot(self,x):
  d=x.__dict__.copy();d.update(state=x.state.value)
  with self.sf() as s:s.merge(SnapshotRow(**d));s.commit()
 def latest_snapshot(self,t):
  with self.sf() as s:
   r=s.scalars(select(SnapshotRow).where(SnapshotRow.tenant_id==t).order_by(SnapshotRow.sequence.desc())).first();return _s(r) if r else None
 def save_impact(self,x):
  import json
  d=x.__dict__.copy();d['path']=json.dumps(x.path)
  with self.sf() as s:s.merge(ImpactRow(**d));s.commit()
 def impacts(self,t):
  with self.sf() as s:return tuple(_i(r) for r in s.scalars(select(ImpactRow).where(ImpactRow.tenant_id==t)).all())

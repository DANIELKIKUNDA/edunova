import json
from uuid import uuid4
from sqlalchemy import String,Float,Integer,DateTime,Text,select
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
class AdaptiveSnapshotRow(Base):
 __tablename__='adaptive_learning_snapshots'; id:Mapped[str]=mapped_column(String(64),primary_key=True); account_id:Mapped[str]=mapped_column(String(64),index=True); mastery:Mapped[float]=mapped_column(Float); readiness:Mapped[float]=mapped_column(Float,index=True); consistency:Mapped[float]=mapped_column(Float); risk:Mapped[str]=mapped_column(String(16),index=True); evidence_count:Mapped[int]=mapped_column(Integer); model_version:Mapped[str]=mapped_column(String(32)); payload:Mapped[str]=mapped_column(Text); generated_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True)
class SqlAlchemyAdaptiveLearningRepository:
 def __init__(self,sf):self.sf=sf
 def save(self,a,x,now):
  payload=json.dumps({'confidence':x.confidence.value,'decisions':[d.__dict__ for d in x.decisions],'gaps':[g.__dict__ for g in x.gaps],'exam_readiness':[e.__dict__ for e in x.exam_readiness]},separators=(',',':'),ensure_ascii=False)
  with self.sf() as s:s.add(AdaptiveSnapshotRow(id=uuid4().hex,account_id=a,mastery=x.mastery,readiness=x.readiness,consistency=x.consistency,risk=x.risk.value,evidence_count=x.evidence_count,model_version=x.model_version,payload=payload,generated_at=now));s.commit()
 def history(self,a,limit=30):
  with self.sf() as s:
   rows=s.scalars(select(AdaptiveSnapshotRow).where(AdaptiveSnapshotRow.account_id==a).order_by(AdaptiveSnapshotRow.generated_at.desc()).limit(max(1,min(limit,90)))).all()
   return tuple({'mastery':r.mastery,'readiness':r.readiness,'consistency':r.consistency,'risk':r.risk,'evidence_count':r.evidence_count,'model_version':r.model_version,'generated_at':r.generated_at} for r in rows)

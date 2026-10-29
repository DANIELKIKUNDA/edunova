from __future__ import annotations
import json
from sqlalchemy import String,Integer,DateTime,Boolean,Text,select
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.tutor.domain.model import *
class TutorSessionRow(Base):
 __tablename__='tutor_sessions';id:Mapped[str]=mapped_column(String(64),primary_key=True);account_id:Mapped[str]=mapped_column(String(64),index=True);course_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);target_concept_id:Mapped[str|None]=mapped_column(String(128),nullable=True);subject_domain:Mapped[str]=mapped_column(String(80));high_stakes:Mapped[bool]=mapped_column(Boolean);state:Mapped[str]=mapped_column(String(24),index=True);hint_level:Mapped[int]=mapped_column(Integer);turn_count:Mapped[int]=mapped_column(Integer);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class TutorTurnRow(Base):
 __tablename__='tutor_turns';id:Mapped[str]=mapped_column(String(64),primary_key=True);session_id:Mapped[str]=mapped_column(String(64),index=True);account_id:Mapped[str]=mapped_column(String(64),index=True);question:Mapped[str]=mapped_column(Text);move:Mapped[str]=mapped_column(String(24));reason:Mapped[str]=mapped_column(String(128));target_concept_id:Mapped[str|None]=mapped_column(String(128),nullable=True);bloom_target:Mapped[str]=mapped_column(String(24));hint_level:Mapped[int]=mapped_column(Integer);requires_sources:Mapped[bool]=mapped_column(Boolean);next_action:Mapped[str]=mapped_column(String(128));evidence:Mapped[str]=mapped_column(Text);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));mutation_id:Mapped[str|None]=mapped_column(String(96),nullable=True,index=True)
def _s(r):return TutorSession(r.id,r.account_id,r.course_id,r.target_concept_id,r.subject_domain,r.high_stakes,TutorSessionState(r.state),r.hint_level,r.turn_count,r.row_version,r.created_at,r.updated_at)
def _t(r):return TutorTurn(r.id,r.session_id,r.account_id,r.question,TutorDecision(TutorMove(r.move),r.reason,r.target_concept_id,r.bloom_target,r.hint_level,r.requires_sources,r.next_action),tuple(json.loads(r.evidence)),r.created_at,r.mutation_id)
class SqlAlchemyTutorRepository:
 def __init__(self,sf):self.sf=sf
 def save_session(self,x):
  d=x.__dict__.copy();d['state']=x.state.value
  with self.sf() as s:s.merge(TutorSessionRow(**d));s.commit()
 def session(self,a,id):
  with self.sf() as s:r=s.get(TutorSessionRow,id);return _s(r) if r and r.account_id==a else None
 def save_turn(self,x):
  d={'id':x.id,'session_id':x.session_id,'account_id':x.account_id,'question':x.question,'move':x.decision.move.value,'reason':x.decision.reason,'target_concept_id':x.decision.target_concept_id,'bloom_target':x.decision.bloom_target,'hint_level':x.decision.hint_level,'requires_sources':x.decision.requires_sources,'next_action':x.decision.next_action,'evidence':json.dumps(list(x.evidence)),'created_at':x.created_at,'mutation_id':x.mutation_id}
  with self.sf() as s:s.add(TutorTurnRow(**d));s.commit()
 def turn_by_mutation(self,a,m):
  with self.sf() as s:r=s.scalar(select(TutorTurnRow).where(TutorTurnRow.account_id==a,TutorTurnRow.mutation_id==m));return _t(r) if r else None
 def turns(self,a,sid,limit=50):
  with self.sf() as s:return tuple(_t(r) for r in s.scalars(select(TutorTurnRow).where(TutorTurnRow.account_id==a,TutorTurnRow.session_id==sid).order_by(TutorTurnRow.created_at).limit(limit)).all())

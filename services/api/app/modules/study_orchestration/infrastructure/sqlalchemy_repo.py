from __future__ import annotations
from datetime import UTC
from sqlalchemy import String,Integer,DateTime,Date,Text,select,delete
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.study_orchestration.domain.model import *
def _utc(x): return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class PlannerPreferencesRow(Base):
 __tablename__='study_planner_preferences'; account_id:Mapped[str]=mapped_column(String(64),primary_key=True); timezone:Mapped[str]=mapped_column(String(64),default='Africa/Lubumbashi'); daily_limit_minutes:Mapped[int]=mapped_column(Integer,default=120); session_max_minutes:Mapped[int]=mapped_column(Integer,default=45); preferred_start_hour:Mapped[int]=mapped_column(Integer,default=18); preferred_end_hour:Mapped[int]=mapped_column(Integer,default=22); buffer_minutes:Mapped[int]=mapped_column(Integer,default=10); weekend_enabled:Mapped[int]=mapped_column(Integer,default=1); row_version:Mapped[int]=mapped_column(Integer,default=1)
class BusyBlockRow(Base):
 __tablename__='study_planner_busy_blocks'; id:Mapped[str]=mapped_column(String(64),primary_key=True); account_id:Mapped[str]=mapped_column(String(64),index=True); starts_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True); ends_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True); label:Mapped[str]=mapped_column(String(180)); source:Mapped[str]=mapped_column(String(32),default='manual')
class StudyPlanItemRow(Base):
 __tablename__='study_plan_items'; id:Mapped[str]=mapped_column(String(64),primary_key=True); account_id:Mapped[str]=mapped_column(String(64),index=True); plan_date:Mapped[object]=mapped_column(Date,index=True); starts_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True); ends_at:Mapped[object]=mapped_column(DateTime(timezone=True)); course_id:Mapped[str]=mapped_column(String(64),index=True); chapter_id:Mapped[str|None]=mapped_column(String(64),nullable=True); action:Mapped[str]=mapped_column(String(40)); label:Mapped[str]=mapped_column(String(180)); source:Mapped[str]=mapped_column(String(24)); priority:Mapped[int]=mapped_column(Integer); reason:Mapped[str]=mapped_column(Text); expected_outcome:Mapped[str]=mapped_column(Text); state:Mapped[str]=mapped_column(String(24),index=True); row_version:Mapped[int]=mapped_column(Integer,default=1)
def _p(r): return PlannerPreferences(r.account_id,r.timezone,r.daily_limit_minutes,r.session_max_minutes,r.preferred_start_hour,r.preferred_end_hour,r.buffer_minutes,bool(r.weekend_enabled),r.row_version)
def _b(r): return BusyBlock(r.id,r.account_id,_utc(r.starts_at),_utc(r.ends_at),r.label,r.source)
def _i(r): return StudyPlanItem(r.id,r.account_id,r.plan_date,_utc(r.starts_at),_utc(r.ends_at),r.course_id,r.chapter_id,r.action,r.label,PlanSource(r.source),r.priority,r.reason,r.expected_outcome,PlanItemState(r.state),r.row_version)
class SqlAlchemyStudyPlannerRepository:
 def __init__(self,sf): self.sf=sf
 def preferences(self,a):
  with self.sf() as s:
   r=s.get(PlannerPreferencesRow,a); return _p(r) if r else PlannerPreferences(a)
 def save_preferences(self,x):
  with self.sf() as s:s.merge(PlannerPreferencesRow(**{**x.__dict__,'weekend_enabled':int(x.weekend_enabled)}));s.commit()
 def busy_blocks(self,a,start,end):
  with self.sf() as s:return tuple(_b(r) for r in s.scalars(select(BusyBlockRow).where(BusyBlockRow.account_id==a,BusyBlockRow.ends_at>start,BusyBlockRow.starts_at<end).order_by(BusyBlockRow.starts_at)).all())
 def save_busy(self,x):
  with self.sf() as s:s.merge(BusyBlockRow(**x.__dict__));s.commit()
 def items_for_day(self,a,d):
  with self.sf() as s:return tuple(_i(r) for r in s.scalars(select(StudyPlanItemRow).where(StudyPlanItemRow.account_id==a,StudyPlanItemRow.plan_date==d,StudyPlanItemRow.state!='superseded').order_by(StudyPlanItemRow.starts_at)).all())
 def replace_planned_day(self,a,d,items):
  with self.sf() as s:
   rows=s.scalars(select(StudyPlanItemRow).where(StudyPlanItemRow.account_id==a,StudyPlanItemRow.plan_date==d,StudyPlanItemRow.state=='planned')).all()
   for r in rows:r.state='superseded';r.row_version+=1
   for x in items:s.add(StudyPlanItemRow(**{**x.__dict__,'source':x.source.value,'state':x.state.value}))
   s.commit()
 def item(self,a,id):
  with self.sf() as s:r=s.get(StudyPlanItemRow,id);return _i(r) if r and r.account_id==a else None
 def save_item(self,x):
  with self.sf() as s:s.merge(StudyPlanItemRow(**{**x.__dict__,'source':x.source.value,'state':x.state.value}));s.commit()

from __future__ import annotations
from datetime import UTC
from sqlalchemy import String,Integer,Float,Boolean,DateTime,Text,select,func,and_
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.learning_experience.domain.model import *

def _utc(v): return v if v is None or v.tzinfo else v.replace(tzinfo=UTC)
class StudySessionRow(Base):
 __tablename__='learning_study_sessions'
 id:Mapped[str]=mapped_column(String(64),primary_key=True); account_id:Mapped[str]=mapped_column(String(64),index=True); course_id:Mapped[str]=mapped_column(String(64),index=True); chapter_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True); mode:Mapped[str]=mapped_column(String(24)); state:Mapped[str]=mapped_column(String(24),index=True); started_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True); updated_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True); ended_at:Mapped[object]=mapped_column(DateTime(timezone=True),nullable=True); active_seconds:Mapped[int]=mapped_column(Integer,default=0); last_position:Mapped[str|None]=mapped_column(String(255),nullable=True); objective:Mapped[str|None]=mapped_column(String(500),nullable=True); row_version:Mapped[int]=mapped_column(Integer,default=1)
class LearningProgressRow(Base):
 __tablename__='learning_progress'; account_id:Mapped[str]=mapped_column(String(64),primary_key=True); course_id:Mapped[str]=mapped_column(String(64),primary_key=True); chapter_id:Mapped[str]=mapped_column(String(64),primary_key=True,default='__course__'); stage:Mapped[str]=mapped_column(String(24),index=True); completion_ratio:Mapped[float]=mapped_column(Float,default=0); practice_attempts:Mapped[int]=mapped_column(Integer,default=0); assessment_attempts:Mapped[int]=mapped_column(Integer,default=0); correct_answers:Mapped[int]=mapped_column(Integer,default=0); total_answers:Mapped[int]=mapped_column(Integer,default=0); updated_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True)
class ErrorItemRow(Base):
 __tablename__='learning_error_bank'; id:Mapped[str]=mapped_column(String(64),primary_key=True); account_id:Mapped[str]=mapped_column(String(64),index=True); course_id:Mapped[str]=mapped_column(String(64),index=True); chapter_id:Mapped[str|None]=mapped_column(String(64),nullable=True); source_type:Mapped[str]=mapped_column(String(32)); source_id:Mapped[str]=mapped_column(String(64)); prompt:Mapped[str]=mapped_column(Text); correct_answer:Mapped[str|None]=mapped_column(Text,nullable=True); attempts:Mapped[int]=mapped_column(Integer,default=1); resolved:Mapped[bool]=mapped_column(Boolean,default=False,index=True); next_review_at:Mapped[object]=mapped_column(DateTime(timezone=True),nullable=True,index=True); created_at:Mapped[object]=mapped_column(DateTime(timezone=True)); updated_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True)
class ReviewCardRow(Base):
 __tablename__='learning_review_cards'; account_id:Mapped[str]=mapped_column(String(64),primary_key=True); card_id:Mapped[str]=mapped_column(String(64),primary_key=True); course_id:Mapped[str]=mapped_column(String(64),index=True); chapter_id:Mapped[str|None]=mapped_column(String(64),nullable=True); repetitions:Mapped[int]=mapped_column(Integer,default=0); interval_days:Mapped[int]=mapped_column(Integer,default=0); ease_factor:Mapped[float]=mapped_column(Float,default=2.5); due_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True); updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))

class ExamPlanRow(Base):
 __tablename__='learning_exam_plans'; id:Mapped[str]=mapped_column(String(64),primary_key=True); account_id:Mapped[str]=mapped_column(String(64),index=True); title:Mapped[str]=mapped_column(String(160)); exam_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True); daily_minutes:Mapped[int]=mapped_column(Integer); course_ids:Mapped[str]=mapped_column(Text); state:Mapped[str]=mapped_column(String(24),index=True); created_at:Mapped[object]=mapped_column(DateTime(timezone=True)); updated_at:Mapped[object]=mapped_column(DateTime(timezone=True)); row_version:Mapped[int]=mapped_column(Integer,default=1)

def _s(r): return StudySession(r.id,r.account_id,r.course_id,r.chapter_id,StudyMode(r.mode),SessionState(r.state),_utc(r.started_at),_utc(r.updated_at),_utc(r.ended_at),r.active_seconds,r.last_position,r.objective,r.row_version)
def _p(r): return LearningProgress(r.account_id,r.course_id,None if r.chapter_id=='__course__' else r.chapter_id,MasteryStage(r.stage),r.completion_ratio,r.practice_attempts,r.assessment_attempts,r.correct_answers,r.total_answers,_utc(r.updated_at))
def _c(r): return ReviewCard(r.account_id,r.card_id,r.course_id,r.chapter_id,r.repetitions,r.interval_days,r.ease_factor,_utc(r.due_at),_utc(r.updated_at))
def _e(r): return ErrorItem(r.id,r.account_id,r.course_id,r.chapter_id,r.source_type,r.source_id,r.prompt,r.correct_answer,r.attempts,r.resolved,_utc(r.next_review_at),_utc(r.created_at),_utc(r.updated_at))
def _x(r): return ExamPlan(r.id,r.account_id,r.title,_utc(r.exam_at),r.daily_minutes,tuple(filter(None,r.course_ids.split('\n'))),ExamPlanState(r.state),_utc(r.created_at),_utc(r.updated_at),r.row_version)
class SqlAlchemyLearningRepository:
 def __init__(self,sf): self.sf=sf
 def save_session(self,x):
  with self.sf() as s: s.merge(StudySessionRow(**x.__dict__,mode=x.mode.value,state=x.state.value)); s.commit()
 def session(self,id):
  with self.sf() as s: r=s.get(StudySessionRow,id); return _s(r) if r else None
 def active_session(self,account_id):
  with self.sf() as s:
   r=s.scalar(select(StudySessionRow).where(StudySessionRow.account_id==account_id,StudySessionRow.state.in_(['active','paused'])).order_by(StudySessionRow.updated_at.desc())); return _s(r) if r else None
 def recent_sessions(self,account_id,limit=20):
  with self.sf() as s: return tuple(_s(r) for r in s.scalars(select(StudySessionRow).where(StudySessionRow.account_id==account_id).order_by(StudySessionRow.updated_at.desc()).limit(limit)).all())
 def progress(self,a,c,ch=None):
  with self.sf() as s: r=s.get(LearningProgressRow,(a,c,ch or '__course__')); return _p(r) if r else None
 def save_progress(self,x):
  with self.sf() as s: s.merge(LearningProgressRow(**x.__dict__,chapter_id=x.chapter_id or '__course__',stage=x.stage.value)); s.commit()
 def save_error(self,x):
  with self.sf() as s: s.merge(ErrorItemRow(**x.__dict__)); s.commit()
 def unresolved_errors(self,a,limit=50):
  with self.sf() as s: return tuple(_e(r) for r in s.scalars(select(ErrorItemRow).where(ErrorItemRow.account_id==a,ErrorItemRow.resolved==False).order_by(ErrorItemRow.updated_at.desc()).limit(limit)).all())
 def error(self,a,id):
  with self.sf() as s:
   r=s.get(ErrorItemRow,id); return _e(r) if r and r.account_id==a else None
 def due_errors(self,a,now,limit=50):
  with self.sf() as s: return tuple(_e(r) for r in s.scalars(select(ErrorItemRow).where(ErrorItemRow.account_id==a,ErrorItemRow.resolved==False,ErrorItemRow.next_review_at<=now).order_by(ErrorItemRow.next_review_at).limit(limit)).all())
 def save_exam_plan(self,x):
  d=x.__dict__.copy(); d['course_ids']='\n'.join(x.course_ids); d['state']=x.state.value
  with self.sf() as s: s.merge(ExamPlanRow(**d)); s.commit()
 def exam_plans(self,a):
  with self.sf() as s: return tuple(_x(r) for r in s.scalars(select(ExamPlanRow).where(ExamPlanRow.account_id==a).order_by(ExamPlanRow.exam_at)).all())
 def review_card(self,a,card_id):
  with self.sf() as s: r=s.get(ReviewCardRow,(a,card_id)); return _c(r) if r else None
 def save_review_card(self,x):
  with self.sf() as s: s.merge(ReviewCardRow(**x.__dict__)); s.commit()
 def due_cards(self,a,now,limit=100):
  with self.sf() as s: return tuple(_c(r) for r in s.scalars(select(ReviewCardRow).where(ReviewCardRow.account_id==a,ReviewCardRow.due_at<=now).order_by(ReviewCardRow.due_at).limit(limit)).all())
 def all_progress(self,a,limit=1000):
  with self.sf() as s:return tuple(_p(r) for r in s.scalars(select(LearningProgressRow).where(LearningProgressRow.account_id==a).limit(limit)).all())
 def all_review_cards(self,a,limit=1000):
  with self.sf() as s:return tuple(_c(r) for r in s.scalars(select(ReviewCardRow).where(ReviewCardRow.account_id==a).limit(limit)).all())
 def dashboard(self,a,now):
  with self.sf() as s:
   studied=s.scalar(select(func.coalesce(func.sum(StudySessionRow.active_seconds),0)).where(StudySessionRow.account_id==a,StudySessionRow.state=='completed')) or 0
   errors=s.scalar(select(func.count()).select_from(ErrorItemRow).where(ErrorItemRow.account_id==a,ErrorItemRow.resolved==False)) or 0
   due=s.scalar(select(func.count()).select_from(ReviewCardRow).where(ReviewCardRow.account_id==a,ReviewCardRow.due_at<=now)) or 0
   mastered=s.scalar(select(func.count()).select_from(LearningProgressRow).where(LearningProgressRow.account_id==a,LearningProgressRow.stage=='mastered')) or 0
   return {'study_seconds':int(studied),'open_errors':int(errors),'due_flashcards':int(due),'mastered_units':int(mastered)}

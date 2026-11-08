from sqlalchemy import String,Integer,DateTime,ForeignKey,select,update,func
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.student_success.domain.model import SuccessCase,SuccessEvent,SuccessPlan,SuccessAction,SuccessAssessment
from app.modules.academic_delivery.infrastructure.sqlalchemy_repo import PublishedCourseResultRow
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import AttendanceSessionRow,AttendanceRecordRow

class SuccessCaseRow(Base):
 __tablename__='student_success_cases'
 id:Mapped[str]=mapped_column(String(64),primary_key=True)
 institution_id:Mapped[str]=mapped_column(String(64),index=True)
 student_id:Mapped[str]=mapped_column(String(64),index=True)
 category:Mapped[str]=mapped_column(String(40))
 severity:Mapped[str]=mapped_column(String(20))
 description:Mapped[str]=mapped_column(String(2000))
 state:Mapped[str]=mapped_column(String(20),index=True)
 assigned_to:Mapped[str|None]=mapped_column(String(64),nullable=True)
 created_by:Mapped[str]=mapped_column(String(64))
 created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
 updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
 version:Mapped[int]=mapped_column(Integer)
 source_kind:Mapped[str|None]=mapped_column(String(40),nullable=True,index=True)
 source_key:Mapped[str|None]=mapped_column(String(160),nullable=True,index=True)
 evidence_hash:Mapped[str|None]=mapped_column(String(64),nullable=True)

class SuccessEventRow(Base):
 __tablename__='student_success_events'
 id:Mapped[str]=mapped_column(String(64),primary_key=True)
 case_id:Mapped[str]=mapped_column(String(64),index=True)
 actor_id:Mapped[str]=mapped_column(String(64))
 action:Mapped[str]=mapped_column(String(30))
 note:Mapped[str]=mapped_column(String(2000))
 created_at:Mapped[object]=mapped_column(DateTime(timezone=True))


class SuccessPlanRow(Base):
 __tablename__='student_success_plans'
 id:Mapped[str]=mapped_column(String(64),primary_key=True)
 case_id:Mapped[str]=mapped_column(String(64),index=True)
 institution_id:Mapped[str]=mapped_column(String(64),index=True)
 student_id:Mapped[str]=mapped_column(String(64),index=True)
 objective:Mapped[str]=mapped_column(String(2000))
 state:Mapped[str]=mapped_column(String(20))
 target_date:Mapped[str|None]=mapped_column(String(10),nullable=True)
 created_by:Mapped[str]=mapped_column(String(64))
 created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
 updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
 version:Mapped[int]=mapped_column(Integer)

class SuccessActionRow(Base):
 __tablename__='student_success_actions'
 id:Mapped[str]=mapped_column(String(64),primary_key=True)
 plan_id:Mapped[str]=mapped_column(String(64),index=True)
 title:Mapped[str]=mapped_column(String(500))
 assigned_to:Mapped[str]=mapped_column(String(64),index=True)
 due_date:Mapped[str|None]=mapped_column(String(10),nullable=True)
 state:Mapped[str]=mapped_column(String(20),index=True)
 completion_note:Mapped[str|None]=mapped_column(String(2000),nullable=True)
 created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
 completed_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
 version:Mapped[int]=mapped_column(Integer)

class SuccessAssessmentRow(Base):
 __tablename__='student_success_assessments'
 id:Mapped[str]=mapped_column(String(64),primary_key=True)
 plan_id:Mapped[str]=mapped_column(String(64),index=True)
 case_id:Mapped[str]=mapped_column(String(64),index=True)
 institution_id:Mapped[str]=mapped_column(String(64),index=True)
 student_id:Mapped[str]=mapped_column(String(64),index=True)
 failed_results:Mapped[int]=mapped_column(Integer)
 published_results:Mapped[int]=mapped_column(Integer)
 attendance_records:Mapped[int]=mapped_column(Integer)
 attendance_rate:Mapped[float|None]=mapped_column(nullable=True)
 outcome:Mapped[str]=mapped_column(String(20),index=True)
 evidence_hash:Mapped[str]=mapped_column(String(64))
 assessed_by:Mapped[str]=mapped_column(String(64))
 created_at:Mapped[object]=mapped_column(DateTime(timezone=True))

class SqlSuccessRepository:
 def __init__(self,sf):self.sf=sf
 def get(self,cid):
  with self.sf() as s:
   x=s.get(SuccessCaseRow,cid);return SuccessCase(**{k:getattr(x,k) for k in SuccessCase.__dataclass_fields__}) if x else None
 def save_with_event(self,c,e,expected=None):
  with self.sf() as s:
   if expected is None:s.add(SuccessCaseRow(**c.__dict__))
   else:
    changes={k:getattr(c,k) for k in SuccessCase.__dataclass_fields__ if k!='id'}
    result=s.execute(update(SuccessCaseRow).where(SuccessCaseRow.id==c.id,SuccessCaseRow.version==expected).values(**changes))
    if result.rowcount!=1:raise ValueError('success_case_concurrent_modification')
   s.add(SuccessEventRow(**e.__dict__));s.commit()
 def list(self,i,sid=None):
  with self.sf() as s:
   q=select(SuccessCaseRow).where(SuccessCaseRow.institution_id==i)
   if sid:q=q.where(SuccessCaseRow.student_id==sid)
   rows=s.scalars(q.order_by(SuccessCaseRow.created_at.desc(),SuccessCaseRow.id).limit(200)).all()
   return tuple(SuccessCase(**{k:getattr(x,k) for k in SuccessCase.__dataclass_fields__}) for x in rows)

 def by_source(self,i,source_key):
  with self.sf() as s:
   x=s.scalar(select(SuccessCaseRow).where(SuccessCaseRow.institution_id==i,SuccessCaseRow.source_key==source_key))
   return SuccessCase(**{k:getattr(x,k) for k in SuccessCase.__dataclass_fields__}) if x else None
 def evidence(self,i,student_id,student_account_id):
  with self.sf() as s:
   results=s.scalars(select(PublishedCourseResultRow).where(PublishedCourseResultRow.institution_id==i,PublishedCourseResultRow.student_id==student_id)).all()
   closed=s.scalars(select(AttendanceSessionRow.id).where(AttendanceSessionRow.institution_id==i,AttendanceSessionRow.state=='closed')).all()
   attendance=s.scalars(select(AttendanceRecordRow).where(AttendanceRecordRow.institution_id==i,AttendanceRecordRow.student_account_id==student_account_id,AttendanceRecordRow.attendance_session_id.in_(closed))).all() if closed else []
   return tuple(results),tuple(attendance)
 def events(self,cid):
  with self.sf() as s:
   return tuple(SuccessEvent(**{k:getattr(x,k) for k in SuccessEvent.__dataclass_fields__}) for x in s.scalars(select(SuccessEventRow).where(SuccessEventRow.case_id==cid).order_by(SuccessEventRow.created_at,SuccessEventRow.id)).all())
 def active_plan(self,case_id):
  with self.sf() as s:
   x=s.scalar(select(SuccessPlanRow).where(SuccessPlanRow.case_id==case_id,SuccessPlanRow.state=='active'))
   return SuccessPlan(**{k:getattr(x,k) for k in SuccessPlan.__dataclass_fields__}) if x else None
 def get_plan(self,pid):
  with self.sf() as s:
   x=s.get(SuccessPlanRow,pid);return SuccessPlan(**{k:getattr(x,k) for k in SuccessPlan.__dataclass_fields__}) if x else None
 def save_plan_with_event(self,p,e,expected=None):
  with self.sf() as s:
   if expected is None:s.add(SuccessPlanRow(**p.__dict__))
   else:
    changes={k:getattr(p,k) for k in SuccessPlan.__dataclass_fields__ if k!='id'}
    r=s.execute(update(SuccessPlanRow).where(SuccessPlanRow.id==p.id,SuccessPlanRow.version==expected).values(**changes))
    if r.rowcount!=1:raise ValueError('success_plan_concurrent_modification')
   s.add(SuccessEventRow(**e.__dict__));s.commit()
 def add_action_with_event(self,a,e):
  with self.sf() as s:s.add(SuccessActionRow(**a.__dict__));s.add(SuccessEventRow(**e.__dict__));s.commit()
 def get_action(self,aid):
  with self.sf() as s:
   x=s.get(SuccessActionRow,aid);return SuccessAction(**{k:getattr(x,k) for k in SuccessAction.__dataclass_fields__}) if x else None
 def save_action_with_event(self,a,e,expected):
  with self.sf() as s:
   changes={k:getattr(a,k) for k in SuccessAction.__dataclass_fields__ if k!='id'}
   r=s.execute(update(SuccessActionRow).where(SuccessActionRow.id==a.id,SuccessActionRow.version==expected).values(**changes))
   if r.rowcount!=1:raise ValueError('success_action_concurrent_modification')
   s.add(SuccessEventRow(**e.__dict__));s.commit()
 def actions(self,pid):
  with self.sf() as s:
   rows=s.scalars(select(SuccessActionRow).where(SuccessActionRow.plan_id==pid).order_by(SuccessActionRow.created_at,SuccessActionRow.id)).all()
   return tuple(SuccessAction(**{k:getattr(x,k) for k in SuccessAction.__dataclass_fields__}) for x in rows)
 def add_assessment_with_event(self,a,e):
  with self.sf() as s:s.add(SuccessAssessmentRow(**a.__dict__));s.add(SuccessEventRow(**e.__dict__));s.commit()
 def assessments(self,pid):
  with self.sf() as s:
   rows=s.scalars(select(SuccessAssessmentRow).where(SuccessAssessmentRow.plan_id==pid).order_by(SuccessAssessmentRow.created_at,SuccessAssessmentRow.id)).all()
   return tuple(SuccessAssessment(**{k:getattr(x,k) for k in SuccessAssessment.__dataclass_fields__}) for x in rows)
 def dashboard(self,i,today):
  with self.sf() as s:
   cases=s.scalars(select(SuccessCaseRow).where(SuccessCaseRow.institution_id==i)).all();plans=s.scalars(select(SuccessPlanRow).where(SuccessPlanRow.institution_id==i)).all()
   pids=[p.id for p in plans];actions=s.scalars(select(SuccessActionRow).where(SuccessActionRow.plan_id.in_(pids))).all() if pids else []
   assessments=s.scalars(select(SuccessAssessmentRow).where(SuccessAssessmentRow.institution_id==i)).all()
   latest={}
   for x in assessments:
    if x.plan_id not in latest or (x.created_at,x.id)>(latest[x.plan_id].created_at,latest[x.plan_id].id):latest[x.plan_id]=x
   outcomes={}
   for x in latest.values():outcomes[x.outcome]=outcomes.get(x.outcome,0)+1
   return {'open_cases':sum(c.state!='closed' for c in cases),'high_severity_open':sum(c.state!='closed' and c.severity=='high' for c in cases),'active_plans':sum(p.state=='active' for p in plans),'overdue_plans':sum(p.state=='active' and p.target_date is not None and p.target_date<today for p in plans),'pending_actions':sum(a.state=='pending' for a in actions),'overdue_actions':sum(a.state=='pending' and a.due_date is not None and a.due_date<today for a in actions),'latest_assessment_outcomes':outcomes}


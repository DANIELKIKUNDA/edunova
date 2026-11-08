from datetime import UTC
from sqlalchemy import String,Integer,Float,DateTime,UniqueConstraint,select,update,Text
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.gradebook.domain.model import *
def u(x):return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class GradebookRow(Base):
 __tablename__='academic_gradebooks';__table_args__=(UniqueConstraint('offering_id',name='uq_academic_gradebook_offering'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);offering_id:Mapped[str]=mapped_column(String(64),index=True);title:Mapped[str]=mapped_column(String(240));state:Mapped[str]=mapped_column(String(24),index=True);pass_percent:Mapped[float]=mapped_column(Float);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class ComponentRow(Base):
 __tablename__='academic_grade_components';__table_args__=(UniqueConstraint('gradebook_id','position',name='uq_grade_component_position'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);gradebook_id:Mapped[str]=mapped_column(String(64),index=True);title:Mapped[str]=mapped_column(String(240));kind:Mapped[str]=mapped_column(String(24));weight_percent:Mapped[float]=mapped_column(Float);max_score:Mapped[float]=mapped_column(Float);source_assignment_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);position:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class MarkRow(Base):
 __tablename__='academic_student_marks';__table_args__=(UniqueConstraint('component_id','student_account_id',name='uq_academic_component_student'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);gradebook_id:Mapped[str]=mapped_column(String(64),index=True);component_id:Mapped[str]=mapped_column(String(64),index=True);student_account_id:Mapped[str]=mapped_column(String(64),index=True);score:Mapped[float|None]=mapped_column(Float,nullable=True);state:Mapped[str]=mapped_column(String(24),index=True);source_ref:Mapped[str|None]=mapped_column(String(128),nullable=True);validated_by:Mapped[str|None]=mapped_column(String(64),nullable=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True));attendance:Mapped[str]=mapped_column(String(32),default='present');note:Mapped[str|None]=mapped_column(Text,nullable=True)
class ExamSessionRow(Base):
 __tablename__='academic_exam_sessions';id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);gradebook_id:Mapped[str]=mapped_column(String(64),index=True);component_id:Mapped[str]=mapped_column(String(64),index=True);kind:Mapped[str]=mapped_column(String(24));state:Mapped[str]=mapped_column(String(24),index=True);starts_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True);ends_at:Mapped[object]=mapped_column(DateTime(timezone=True));room:Mapped[str|None]=mapped_column(String(160),nullable=True);instructions:Mapped[str|None]=mapped_column(Text,nullable=True);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SqlAlchemyGradebookRepository:
 def __init__(self,sf):self.sf=sf
 def _g(self,r):return Gradebook(r.id,r.institution_id,r.offering_id,r.title,GradebookState(r.state),r.pass_percent,r.row_version,r.created_by,u(r.created_at),u(r.updated_at))
 def _c(self,r):return GradeComponent(r.id,r.institution_id,r.gradebook_id,r.title,ComponentKind(r.kind),r.weight_percent,r.max_score,r.source_assignment_id,r.position,u(r.created_at))
 def _m(self,r):return StudentMark(r.id,r.institution_id,r.gradebook_id,r.component_id,r.student_account_id,r.score,MarkState(r.state),r.source_ref,r.validated_by,r.row_version,u(r.created_at),u(r.updated_at),AttendanceOutcome(getattr(r,'attendance','present')),getattr(r,'note',None))
 def gradebook(self,i,id):
  with self.sf() as s:r=s.get(GradebookRow,id);return self._g(r) if r and r.institution_id==i else None
 def for_offering(self,i,o):
  with self.sf() as s:r=s.scalar(select(GradebookRow).where(GradebookRow.institution_id==i,GradebookRow.offering_id==o));return self._g(r) if r else None
 def save_gradebook(self,x,expected=None):
  d=dict(institution_id=x.institution_id,offering_id=x.offering_id,title=x.title,state=x.state.value,pass_percent=x.pass_percent,row_version=x.row_version,created_by=x.created_by,created_at=x.created_at,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(GradebookRow,x.id)
   if not old:s.add(GradebookRow(id=x.id,**d));s.commit();return
   q=update(GradebookRow).where(GradebookRow.id==x.id)
   if expected is not None:q=q.where(GradebookRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('gradebook_concurrent_modification')
   s.commit()
 def save_component(self,x):
  with self.sf() as s:s.add(ComponentRow(id=x.id,institution_id=x.institution_id,gradebook_id=x.gradebook_id,title=x.title,kind=x.kind.value,weight_percent=x.weight_percent,max_score=x.max_score,source_assignment_id=x.source_assignment_id,position=x.position,created_at=x.created_at));s.commit()
 def components(self,g):
  with self.sf() as s:return tuple(self._c(r) for r in s.scalars(select(ComponentRow).where(ComponentRow.gradebook_id==g).order_by(ComponentRow.position)).all())
 def component(self,i,id):
  with self.sf() as s:r=s.get(ComponentRow,id);return self._c(r) if r and r.institution_id==i else None
 def mark(self,i,c,stu):
  with self.sf() as s:r=s.scalar(select(MarkRow).where(MarkRow.institution_id==i,MarkRow.component_id==c,MarkRow.student_account_id==stu));return self._m(r) if r else None
 def save_mark(self,x,expected=None):
  d=dict(institution_id=x.institution_id,gradebook_id=x.gradebook_id,component_id=x.component_id,student_account_id=x.student_account_id,score=x.score,state=x.state.value,source_ref=x.source_ref,validated_by=x.validated_by,row_version=x.row_version,created_at=x.created_at,updated_at=x.updated_at,attendance=x.attendance.value,note=x.note)
  with self.sf() as s:
   old=s.scalar(select(MarkRow).where(MarkRow.component_id==x.component_id,MarkRow.student_account_id==x.student_account_id))
   if not old:s.add(MarkRow(id=x.id,**d));s.commit();return
   q=update(MarkRow).where(MarkRow.id==old.id)
   if expected is not None:q=q.where(MarkRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('gradebook_concurrent_modification')
   s.commit()
 def marks(self,g,stu=None):
  with self.sf() as s:
   q=select(MarkRow).where(MarkRow.gradebook_id==g)
   if stu:q=q.where(MarkRow.student_account_id==stu)
   return tuple(self._m(r) for r in s.scalars(q).all())

 def _s(self,r):return ExamSession(r.id,r.institution_id,r.gradebook_id,r.component_id,ExamSessionKind(r.kind),ExamSessionState(r.state),u(r.starts_at),u(r.ends_at),r.room,r.instructions,r.row_version,r.created_by,u(r.created_at),u(r.updated_at))
 def session(self,i,id):
  with self.sf() as s:r=s.get(ExamSessionRow,id);return self._s(r) if r and r.institution_id==i else None
 def sessions_for_gradebook(self,i,g):
  with self.sf() as s:return tuple(self._s(r) for r in s.scalars(select(ExamSessionRow).where(ExamSessionRow.institution_id==i,ExamSessionRow.gradebook_id==g).order_by(ExamSessionRow.starts_at)).all())
 def save_session(self,x,expected=None):
  d=dict(institution_id=x.institution_id,gradebook_id=x.gradebook_id,component_id=x.component_id,kind=x.kind.value,state=x.state.value,starts_at=x.starts_at,ends_at=x.ends_at,room=x.room,instructions=x.instructions,row_version=x.row_version,created_by=x.created_by,created_at=x.created_at,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(ExamSessionRow,x.id)
   if not old:s.add(ExamSessionRow(id=x.id,**d));s.commit();return
   q=update(ExamSessionRow).where(ExamSessionRow.id==x.id)
   if expected is not None:q=q.where(ExamSessionRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('gradebook_concurrent_modification')
   s.commit()

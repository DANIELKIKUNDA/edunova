from __future__ import annotations
from datetime import UTC
from sqlalchemy import String,Integer,DateTime,Boolean,UniqueConstraint,select,update
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.teaching.domain.model import *
def u(x):return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class CourseRow(Base):
 __tablename__='teaching_courses';__table_args__=(UniqueConstraint('institution_id','code',name='uq_teaching_course_code'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);code:Mapped[str]=mapped_column(String(64));title:Mapped[str]=mapped_column(String(240));description:Mapped[str]=mapped_column(String(4000),default='');credits:Mapped[int|None]=mapped_column(Integer,nullable=True);state:Mapped[str]=mapped_column(String(24),index=True);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class OfferingRow(Base):
 __tablename__='teaching_offerings';id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);course_id:Mapped[str]=mapped_column(String(64),index=True);cohort_id:Mapped[str]=mapped_column(String(64),index=True);academic_period_id:Mapped[str]=mapped_column(String(64),index=True);label:Mapped[str]=mapped_column(String(240));state:Mapped[str]=mapped_column(String(24),index=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class AssignmentRow(Base):
 __tablename__='teaching_teacher_assignments';__table_args__=(UniqueConstraint('offering_id','teacher_account_id',name='uq_teaching_assignment'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);offering_id:Mapped[str]=mapped_column(String(64),index=True);teacher_account_id:Mapped[str]=mapped_column(String(64),index=True);role:Mapped[str]=mapped_column(String(24));active:Mapped[bool]=mapped_column(Boolean,index=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SessionRow(Base):
 __tablename__='teaching_sessions';id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);offering_id:Mapped[str]=mapped_column(String(64),index=True);title:Mapped[str]=mapped_column(String(240));starts_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True);ends_at:Mapped[object]=mapped_column(DateTime(timezone=True));state:Mapped[str]=mapped_column(String(24),index=True);summary:Mapped[str]=mapped_column(String(8000),default='');next_topic:Mapped[str]=mapped_column(String(2000),default='');row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class ResourceRow(Base):
 __tablename__='teaching_resources';id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);offering_id:Mapped[str]=mapped_column(String(64),index=True);title:Mapped[str]=mapped_column(String(240));resource_type:Mapped[str]=mapped_column(String(48));uri:Mapped[str]=mapped_column(String(1500));source_revision:Mapped[str|None]=mapped_column(String(128),nullable=True);state:Mapped[str]=mapped_column(String(24),index=True);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SyllabusRow(Base):
 __tablename__='teaching_syllabi';__table_args__=(UniqueConstraint('offering_id','version',name='uq_teaching_syllabus_version'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);offering_id:Mapped[str]=mapped_column(String(64),index=True);version:Mapped[int]=mapped_column(Integer);title:Mapped[str]=mapped_column(String(240));overview:Mapped[str]=mapped_column(String(8000),default='');learning_outcomes:Mapped[str]=mapped_column(String(12000),default='');state:Mapped[str]=mapped_column(String(24),index=True);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));approved_by:Mapped[str|None]=mapped_column(String(64),nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class TopicRow(Base):
 __tablename__='teaching_syllabus_topics';__table_args__=(UniqueConstraint('syllabus_id','position',name='uq_teaching_topic_position'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);syllabus_id:Mapped[str]=mapped_column(String(64),index=True);position:Mapped[int]=mapped_column(Integer);title:Mapped[str]=mapped_column(String(240));description:Mapped[str]=mapped_column(String(8000),default='');learning_objectives:Mapped[str]=mapped_column(String(12000),default='');concept_refs:Mapped[str]=mapped_column(String(12000),default='');planned_minutes:Mapped[int]=mapped_column(Integer,default=0);state:Mapped[str]=mapped_column(String(24),index=True);row_version:Mapped[int]=mapped_column(Integer);updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class ResourceRevisionRow(Base):
 __tablename__='teaching_resource_revisions';__table_args__=(UniqueConstraint('resource_id','revision_no',name='uq_teaching_resource_revision'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);resource_id:Mapped[str]=mapped_column(String(64),index=True);revision_no:Mapped[int]=mapped_column(Integer);title:Mapped[str]=mapped_column(String(240));uri:Mapped[str]=mapped_column(String(1500));source_revision:Mapped[str|None]=mapped_column(String(128),nullable=True);change_note:Mapped[str]=mapped_column(String(2000),default='');created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SqlAlchemyTeachingRepository:
 def __init__(self,sf):self.sf=sf
 def _c(self,r):return Course(r.id,r.institution_id,r.code,r.title,r.description,r.credits,CourseState(r.state),r.row_version,r.created_by,u(r.created_at),u(r.updated_at))
 def _o(self,r):return CourseOffering(r.id,r.institution_id,r.course_id,r.cohort_id,r.academic_period_id,r.label,CourseState(r.state),r.row_version,u(r.created_at),u(r.updated_at))
 def _a(self,r):return TeacherAssignment(r.id,r.institution_id,r.offering_id,r.teacher_account_id,TeacherRole(r.role),r.active,u(r.created_at))
 def _s(self,r):return TeachingSession(r.id,r.institution_id,r.offering_id,r.title,u(r.starts_at),u(r.ends_at),SessionState(r.state),r.summary,r.next_topic,r.row_version,r.created_by,u(r.created_at),u(r.updated_at))
 def _r(self,r):return CourseResource(r.id,r.institution_id,r.offering_id,r.title,r.resource_type,r.uri,r.source_revision,ResourceState(r.state),r.row_version,r.created_by,u(r.created_at),u(r.updated_at))
 def course(self,i,id):
  with self.sf() as s:r=s.get(CourseRow,id);return self._c(r) if r and r.institution_id==i else None
 def course_by_code(self,i,code):
  with self.sf() as s:r=s.scalar(select(CourseRow).where(CourseRow.institution_id==i,CourseRow.code==code.strip().upper()));return self._c(r) if r else None
 def save_course(self,x):
  with self.sf() as s:s.add(CourseRow(id=x.id,institution_id=x.institution_id,code=x.code,title=x.title,description=x.description,credits=x.credits,state=x.state.value,row_version=x.row_version,created_by=x.created_by,created_at=x.created_at,updated_at=x.updated_at));s.commit()
 def offering(self,i,id):
  with self.sf() as s:r=s.get(OfferingRow,id);return self._o(r) if r and r.institution_id==i else None
 def save_offering(self,x,expected=None):
  d=dict(institution_id=x.institution_id,course_id=x.course_id,cohort_id=x.cohort_id,academic_period_id=x.academic_period_id,label=x.label,state=x.state.value,row_version=x.row_version,created_at=x.created_at,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(OfferingRow,x.id)
   if not old:s.add(OfferingRow(id=x.id,**d));s.commit();return
   q=update(OfferingRow).where(OfferingRow.id==x.id)
   if expected is not None:q=q.where(OfferingRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('teaching_concurrent_modification')
   s.commit()
 def list_offerings(self,i):
  with self.sf() as s:return tuple(self._o(r) for r in s.scalars(select(OfferingRow).where(OfferingRow.institution_id==i)).all())
 def assignment(self,o,a):
  with self.sf() as s:r=s.scalar(select(AssignmentRow).where(AssignmentRow.offering_id==o,AssignmentRow.teacher_account_id==a));return self._a(r) if r else None
 def save_assignment(self,x):
  with self.sf() as s:
   old=s.scalar(select(AssignmentRow).where(AssignmentRow.offering_id==x.offering_id,AssignmentRow.teacher_account_id==x.teacher_account_id))
   if old:
    old.role=x.role.value;old.active=x.active
   else:s.add(AssignmentRow(id=x.id,institution_id=x.institution_id,offering_id=x.offering_id,teacher_account_id=x.teacher_account_id,role=x.role.value,active=x.active,created_at=x.created_at))
   s.commit()
 def list_assignments(self,o):
  with self.sf() as s:return tuple(self._a(r) for r in s.scalars(select(AssignmentRow).where(AssignmentRow.offering_id==o,AssignmentRow.active==True)).all())
 def session(self,i,id):
  with self.sf() as s:r=s.get(SessionRow,id);return self._s(r) if r and r.institution_id==i else None
 def save_session(self,x,expected=None):
  d=dict(institution_id=x.institution_id,offering_id=x.offering_id,title=x.title,starts_at=x.starts_at,ends_at=x.ends_at,state=x.state.value,summary=x.summary,next_topic=x.next_topic,row_version=x.row_version,created_by=x.created_by,created_at=x.created_at,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(SessionRow,x.id)
   if not old:s.add(SessionRow(id=x.id,**d));s.commit();return
   q=update(SessionRow).where(SessionRow.id==x.id)
   if expected is not None:q=q.where(SessionRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('teaching_concurrent_modification')
   s.commit()
 def list_sessions(self,o):
  with self.sf() as s:return tuple(self._s(r) for r in s.scalars(select(SessionRow).where(SessionRow.offering_id==o).order_by(SessionRow.starts_at)).all())
 def resource(self,i,id):
  with self.sf() as s:r=s.get(ResourceRow,id);return self._r(r) if r and r.institution_id==i else None
 def save_resource(self,x,expected=None):
  d=dict(institution_id=x.institution_id,offering_id=x.offering_id,title=x.title,resource_type=x.resource_type,uri=x.uri,source_revision=x.source_revision,state=x.state.value,row_version=x.row_version,created_by=x.created_by,created_at=x.created_at,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(ResourceRow,x.id)
   if not old:s.add(ResourceRow(id=x.id,**d));s.commit();return
   q=update(ResourceRow).where(ResourceRow.id==x.id)
   if expected is not None:q=q.where(ResourceRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('teaching_concurrent_modification')
   s.commit()
 def list_resources(self,o):
  with self.sf() as s:return tuple(self._r(r) for r in s.scalars(select(ResourceRow).where(ResourceRow.offering_id==o)).all())

 def _sy(self,r):return Syllabus(r.id,r.institution_id,r.offering_id,r.version,r.title,r.overview,tuple(filter(None,r.learning_outcomes.split('\n'))),SyllabusState(r.state),r.row_version,r.created_by,r.approved_by,u(r.created_at),u(r.updated_at))
 def _t(self,r):return SyllabusTopic(r.id,r.institution_id,r.syllabus_id,r.position,r.title,r.description,tuple(filter(None,r.learning_objectives.split('\n'))),tuple(filter(None,r.concept_refs.split('\n'))),r.planned_minutes,TopicState(r.state),r.row_version,u(r.updated_at))
 def _rr(self,r):return ResourceRevision(r.id,r.institution_id,r.resource_id,r.revision_no,r.title,r.uri,r.source_revision,r.change_note,r.created_by,u(r.created_at))
 def syllabus(self,i,id):
  with self.sf() as s:r=s.get(SyllabusRow,id);return self._sy(r) if r and r.institution_id==i else None
 def list_syllabi(self,o):
  with self.sf() as s:return tuple(self._sy(r) for r in s.scalars(select(SyllabusRow).where(SyllabusRow.offering_id==o).order_by(SyllabusRow.version)).all())
 def save_syllabus(self,x,expected=None):
  d=dict(institution_id=x.institution_id,offering_id=x.offering_id,version=x.version,title=x.title,overview=x.overview,learning_outcomes='\n'.join(x.learning_outcomes),state=x.state.value,row_version=x.row_version,created_by=x.created_by,approved_by=x.approved_by,created_at=x.created_at,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(SyllabusRow,x.id)
   if not old:s.add(SyllabusRow(id=x.id,**d));s.commit();return
   q=update(SyllabusRow).where(SyllabusRow.id==x.id)
   if expected is not None:q=q.where(SyllabusRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('teaching_concurrent_modification')
   s.commit()
 def topic(self,i,id):
  with self.sf() as s:r=s.get(TopicRow,id);return self._t(r) if r and r.institution_id==i else None
 def list_topics(self,sy):
  with self.sf() as s:return tuple(self._t(r) for r in s.scalars(select(TopicRow).where(TopicRow.syllabus_id==sy).order_by(TopicRow.position)).all())
 def save_topic(self,x,expected=None):
  d=dict(institution_id=x.institution_id,syllabus_id=x.syllabus_id,position=x.position,title=x.title,description=x.description,learning_objectives='\n'.join(x.learning_objectives),concept_refs='\n'.join(x.concept_refs),planned_minutes=x.planned_minutes,state=x.state.value,row_version=x.row_version,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(TopicRow,x.id)
   if not old:s.add(TopicRow(id=x.id,**d));s.commit();return
   q=update(TopicRow).where(TopicRow.id==x.id)
   if expected is not None:q=q.where(TopicRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('teaching_concurrent_modification')
   s.commit()
 def list_resource_revisions(self,rid):
  with self.sf() as s:return tuple(self._rr(r) for r in s.scalars(select(ResourceRevisionRow).where(ResourceRevisionRow.resource_id==rid).order_by(ResourceRevisionRow.revision_no)).all())
 def save_resource_revision(self,x):
  with self.sf() as s:s.add(ResourceRevisionRow(id=x.id,institution_id=x.institution_id,resource_id=x.resource_id,revision_no=x.revision_no,title=x.title,uri=x.uri,source_revision=x.source_revision,change_note=x.change_note,created_by=x.created_by,created_at=x.created_at));s.commit()

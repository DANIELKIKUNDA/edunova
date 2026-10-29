from __future__ import annotations
from datetime import UTC
from sqlalchemy import String,Integer,DateTime,Float,UniqueConstraint,select,update
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.academic_catalog.domain.model import *
def _utc(x): return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class CurriculumVersionRow(Base):
 __tablename__='academic_curriculum_versions'; __table_args__=(UniqueConstraint('institution_id','program_unit_id','version',name='uq_academic_curriculum_version'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True); institution_id:Mapped[str]=mapped_column(String(64),index=True); program_unit_id:Mapped[str]=mapped_column(String(64),index=True); code:Mapped[str]=mapped_column(String(80)); title:Mapped[str]=mapped_column(String(240)); version:Mapped[int]=mapped_column(Integer); state:Mapped[str]=mapped_column(String(20),index=True); effective_academic_year_id:Mapped[str]=mapped_column(String(64),index=True); source_catalog_id:Mapped[str|None]=mapped_column(String(160),nullable=True); row_version:Mapped[int]=mapped_column(Integer); created_by:Mapped[str]=mapped_column(String(64)); created_at:Mapped[object]=mapped_column(DateTime(timezone=True)); published_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True); retired_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
class CurriculumCourseRow(Base):
 __tablename__='academic_curriculum_courses'; __table_args__=(UniqueConstraint('curriculum_id','semester','ordinal',name='uq_academic_course_ordinal'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True); curriculum_id:Mapped[str]=mapped_column(String(64),index=True); semester:Mapped[int]=mapped_column(Integer,index=True); ue_code:Mapped[str]=mapped_column(String(80)); code:Mapped[str|None]=mapped_column(String(80),nullable=True,index=True); title:Mapped[str]=mapped_column(String(320)); credits:Mapped[float|None]=mapped_column(Float,nullable=True); total_hours:Mapped[int|None]=mapped_column(Integer,nullable=True); ordinal:Mapped[int]=mapped_column(Integer);cycle:Mapped[str|None]=mapped_column(String(80),nullable=True);level:Mapped[str|None]=mapped_column(String(80),nullable=True);ue_declared_credits:Mapped[float|None]=mapped_column(Float,nullable=True);cmi:Mapped[int|None]=mapped_column(Integer,nullable=True);tp_td:Mapped[int|None]=mapped_column(Integer,nullable=True);tpe:Mapped[int|None]=mapped_column(Integer,nullable=True);percent:Mapped[float|None]=mapped_column(Float,nullable=True)
class PrerequisiteRow(Base):
 __tablename__='academic_curriculum_prerequisites'; __table_args__=(UniqueConstraint('curriculum_id','course_id','required_course_id',name='uq_academic_prerequisite'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True); curriculum_id:Mapped[str]=mapped_column(String(64),index=True); course_id:Mapped[str]=mapped_column(String(64),index=True); required_course_id:Mapped[str]=mapped_column(String(64),index=True); minimum_status:Mapped[str]=mapped_column(String(24))
class CurriculumCohortBindingRow(Base):
 __tablename__='academic_curriculum_cohort_bindings';__table_args__=(UniqueConstraint('cohort_id',name='uq_academic_curriculum_cohort'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);curriculum_id:Mapped[str]=mapped_column(String(64),index=True);cohort_id:Mapped[str]=mapped_column(String(64),index=True);bound_by:Mapped[str]=mapped_column(String(64));bound_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SqlAcademicCatalogRepository:
 def __init__(self,sf): self.sf=sf
 def _v(self,r): return CurriculumVersion(r.id,r.institution_id,r.program_unit_id,r.code,r.title,r.version,CurriculumState(r.state),r.effective_academic_year_id,r.source_catalog_id,r.row_version,r.created_by,_utc(r.created_at),_utc(r.published_at),_utc(r.retired_at))
 def _c(self,r): return CurriculumCourse(r.id,r.curriculum_id,r.semester,r.ue_code,r.code,r.title,r.credits,r.total_hours,r.ordinal,r.cycle,r.level,r.ue_declared_credits,r.cmi,r.tp_td,r.tpe,r.percent)
 def curriculum(self,i,cid):
  with self.sf() as s:r=s.get(CurriculumVersionRow,cid);return self._v(r) if r and r.institution_id==i else None
 def list_curricula(self,i,pid=None):
  with self.sf() as s:
   q=select(CurriculumVersionRow).where(CurriculumVersionRow.institution_id==i)
   if pid:q=q.where(CurriculumVersionRow.program_unit_id==pid)
   return tuple(self._v(r) for r in s.scalars(q.order_by(CurriculumVersionRow.program_unit_id,CurriculumVersionRow.version.desc())).all())
 def save_curriculum(self,x,expected_version=None):
  d=dict(institution_id=x.institution_id,program_unit_id=x.program_unit_id,code=x.code,title=x.title,version=x.version,state=x.state.value,effective_academic_year_id=x.effective_academic_year_id,source_catalog_id=x.source_catalog_id,row_version=x.row_version,created_by=x.created_by,created_at=x.created_at,published_at=x.published_at,retired_at=x.retired_at)
  with self.sf() as s:
   old=s.get(CurriculumVersionRow,x.id)
   if not old:s.add(CurriculumVersionRow(id=x.id,**d));s.commit();return
   q=update(CurriculumVersionRow).where(CurriculumVersionRow.id==x.id)
   if expected_version is not None:q=q.where(CurriculumVersionRow.row_version==expected_version)
   r=s.execute(q.values(**d));
   if r.rowcount!=1:s.rollback();raise ValueError('academic_catalog_concurrent_modification')
   s.commit()
 def add_courses(self,rows):
  with self.sf() as s:
   for x in rows:s.add(CurriculumCourseRow(id=x.id,curriculum_id=x.curriculum_id,semester=x.semester,ue_code=x.ue_code,code=x.code,title=x.title,credits=x.credits,total_hours=x.total_hours,ordinal=x.ordinal,cycle=x.cycle,level=x.level,ue_declared_credits=x.ue_declared_credits,cmi=x.cmi,tp_td=x.tp_td,tpe=x.tpe,percent=x.percent))
   s.commit()
 def courses(self,cid):
  with self.sf() as s:return tuple(self._c(r) for r in s.scalars(select(CurriculumCourseRow).where(CurriculumCourseRow.curriculum_id==cid).order_by(CurriculumCourseRow.semester,CurriculumCourseRow.ordinal)).all())
 def add_prerequisite(self,x):
  with self.sf() as s:s.add(PrerequisiteRow(id=x.id,curriculum_id=x.curriculum_id,course_id=x.course_id,required_course_id=x.required_course_id,minimum_status=x.minimum_status));s.commit()
 def prerequisites(self,cid):
  with self.sf() as s:return tuple(Prerequisite(r.id,r.curriculum_id,r.course_id,r.required_course_id,r.minimum_status) for r in s.scalars(select(PrerequisiteRow).where(PrerequisiteRow.curriculum_id==cid)).all())
 def add_binding(self,x):
  with self.sf() as s:s.add(CurriculumCohortBindingRow(id=x.id,curriculum_id=x.curriculum_id,cohort_id=x.cohort_id,bound_by=x.bound_by,bound_at=x.bound_at));s.commit()
 def binding_for_cohort(self,i,cohort_id):
  with self.sf() as s:
   r=s.scalar(select(CurriculumCohortBindingRow).join(CurriculumVersionRow,CurriculumVersionRow.id==CurriculumCohortBindingRow.curriculum_id).where(CurriculumCohortBindingRow.cohort_id==cohort_id,CurriculumVersionRow.institution_id==i));return CurriculumCohortBinding(r.id,r.curriculum_id,r.cohort_id,r.bound_by,_utc(r.bound_at)) if r else None

from __future__ import annotations
from datetime import UTC
from sqlalchemy import String,Integer,DateTime,Date,Boolean,UniqueConstraint,select,func,update
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.campus.domain.model import *
def _utc(x):return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class InstitutionRow(Base):
 __tablename__='campus_institutions';id:Mapped[str]=mapped_column(String(64),primary_key=True);slug:Mapped[str]=mapped_column(String(96),unique=True,index=True);name:Mapped[str]=mapped_column(String(240));legal_name:Mapped[str]=mapped_column(String(240),default='');country_code:Mapped[str]=mapped_column(String(2));city:Mapped[str|None]=mapped_column(String(120),nullable=True);logo_url:Mapped[str|None]=mapped_column(String(1000),nullable=True);state:Mapped[str]=mapped_column(String(24),index=True);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64),index=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class UnitRow(Base):
 __tablename__='campus_academic_units';__table_args__=(UniqueConstraint('institution_id','code',name='uq_campus_unit_code'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);kind:Mapped[str]=mapped_column(String(24),index=True);name:Mapped[str]=mapped_column(String(240));code:Mapped[str]=mapped_column(String(64));parent_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);active:Mapped[bool]=mapped_column(Boolean,index=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class PeriodRow(Base):
 __tablename__='campus_academic_periods';id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);kind:Mapped[str]=mapped_column(String(24),index=True);name:Mapped[str]=mapped_column(String(160));starts_on:Mapped[object]=mapped_column(Date);ends_on:Mapped[object]=mapped_column(Date);parent_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);active:Mapped[bool]=mapped_column(Boolean,index=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class MembershipRow(Base):
 __tablename__='campus_memberships';__table_args__=(UniqueConstraint('institution_id','account_id',name='uq_campus_member'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);account_id:Mapped[str]=mapped_column(String(64),index=True);role:Mapped[str]=mapped_column(String(32),index=True);state:Mapped[str]=mapped_column(String(24),index=True);unit_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);invited_by:Mapped[str|None]=mapped_column(String(64),nullable=True);joined_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class CohortRow(Base):
 __tablename__='campus_cohorts';id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);program_unit_id:Mapped[str]=mapped_column(String(64),index=True);academic_period_id:Mapped[str]=mapped_column(String(64),index=True);name:Mapped[str]=mapped_column(String(160));level:Mapped[str]=mapped_column(String(80));active:Mapped[bool]=mapped_column(Boolean,index=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class EnrollmentRow(Base):
 __tablename__='campus_enrollments';__table_args__=(UniqueConstraint('cohort_id','student_account_id',name='uq_campus_enrollment'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);cohort_id:Mapped[str]=mapped_column(String(64),index=True);student_account_id:Mapped[str]=mapped_column(String(64),index=True);active:Mapped[bool]=mapped_column(Boolean,index=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SqlAlchemyCampusRepository:
 def __init__(self,sf):self.sf=sf
 def _i(self,r):return Institution(r.id,r.slug,r.name,r.legal_name,r.country_code,r.city,r.logo_url,InstitutionState(r.state),r.row_version,r.created_by,_utc(r.created_at),_utc(r.updated_at))
 def _u(self,r):return AcademicUnit(r.id,r.institution_id,UnitKind(r.kind),r.name,r.code,r.parent_id,r.active,r.row_version,_utc(r.created_at),_utc(r.updated_at))
 def _p(self,r):return AcademicPeriod(r.id,r.institution_id,PeriodKind(r.kind),r.name,r.starts_on,r.ends_on,r.parent_id,r.active,r.row_version,_utc(r.created_at))
 def _m(self,r):return Membership(r.id,r.institution_id,r.account_id,CampusRole(r.role),MembershipState(r.state),r.unit_id,r.invited_by,_utc(r.joined_at),r.row_version,_utc(r.created_at),_utc(r.updated_at))
 def _c(self,r):return Cohort(r.id,r.institution_id,r.program_unit_id,r.academic_period_id,r.name,r.level,r.active,r.row_version,_utc(r.created_at),_utc(r.updated_at))
 def institution(self,i):
  with self.sf() as s:r=s.get(InstitutionRow,i);return self._i(r) if r else None
 def institution_by_slug(self,slug):
  with self.sf() as s:r=s.scalar(select(InstitutionRow).where(InstitutionRow.slug==slug));return self._i(r) if r else None
 def save_institution(self,x,expected_version=None):
  d=dict(slug=x.slug,name=x.name,legal_name=x.legal_name,country_code=x.country_code,city=x.city,logo_url=x.logo_url,state=x.state.value,row_version=x.row_version,created_by=x.created_by,created_at=x.created_at,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(InstitutionRow,x.id)
   if not old:s.add(InstitutionRow(id=x.id,**d));s.commit();return
   q=update(InstitutionRow).where(InstitutionRow.id==x.id)
   if expected_version is not None:q=q.where(InstitutionRow.row_version==expected_version)
   r=s.execute(q.values(**d));
   if r.rowcount!=1:s.rollback();raise ValueError('campus_concurrent_modification')
   s.commit()
 def membership(self,i,a):
  with self.sf() as s:r=s.scalar(select(MembershipRow).where(MembershipRow.institution_id==i,MembershipRow.account_id==a));return self._m(r) if r else None
 def save_membership(self,x,expected_version=None):
  d=dict(institution_id=x.institution_id,account_id=x.account_id,role=x.role.value,state=x.state.value,unit_id=x.unit_id,invited_by=x.invited_by,joined_at=x.joined_at,row_version=x.row_version,created_at=x.created_at,updated_at=x.updated_at)
  with self.sf() as s:
   old=s.get(MembershipRow,x.id)
   if not old:s.add(MembershipRow(id=x.id,**d));s.commit();return
   q=update(MembershipRow).where(MembershipRow.id==x.id)
   if expected_version is not None:q=q.where(MembershipRow.row_version==expected_version)
   r=s.execute(q.values(**d));
   if r.rowcount!=1:s.rollback();raise ValueError('campus_concurrent_modification')
   s.commit()
 def institutions_for_account(self,a):
  with self.sf() as s:
   rows=s.execute(select(InstitutionRow,MembershipRow).join(MembershipRow,MembershipRow.institution_id==InstitutionRow.id).where(MembershipRow.account_id==a,MembershipRow.state.in_(['active','invited'])).order_by(InstitutionRow.name)).all();return tuple((self._i(i),self._m(m)) for i,m in rows)
 def unit(self,i,id):
  with self.sf() as s:r=s.get(UnitRow,id);return self._u(r) if r and r.institution_id==i else None
 def unit_by_code(self,i,code):
  with self.sf() as s:r=s.scalar(select(UnitRow).where(UnitRow.institution_id==i,UnitRow.code==code.strip().upper()));return self._u(r) if r else None
 def save_unit(self,x):
  with self.sf() as s:s.add(UnitRow(id=x.id,institution_id=x.institution_id,kind=x.kind.value,name=x.name,code=x.code,parent_id=x.parent_id,active=x.active,row_version=x.row_version,created_at=x.created_at,updated_at=x.updated_at));s.commit()
 def period(self,i,id):
  with self.sf() as s:r=s.get(PeriodRow,id);return self._p(r) if r and r.institution_id==i else None
 def save_period(self,x):
  with self.sf() as s:s.add(PeriodRow(id=x.id,institution_id=x.institution_id,kind=x.kind.value,name=x.name,starts_on=x.starts_on,ends_on=x.ends_on,parent_id=x.parent_id,active=x.active,row_version=x.row_version,created_at=x.created_at));s.commit()
 def cohort(self,i,id):
  with self.sf() as s:r=s.get(CohortRow,id);return self._c(r) if r and r.institution_id==i else None
 def save_cohort(self,x):
  with self.sf() as s:s.add(CohortRow(id=x.id,institution_id=x.institution_id,program_unit_id=x.program_unit_id,academic_period_id=x.academic_period_id,name=x.name,level=x.level,active=x.active,row_version=x.row_version,created_at=x.created_at,updated_at=x.updated_at));s.commit()
 def enrollment(self,c,a):
  with self.sf() as s:
   r=s.scalar(select(EnrollmentRow).where(EnrollmentRow.cohort_id==c,EnrollmentRow.student_account_id==a));return Enrollment(r.id,r.institution_id,r.cohort_id,r.student_account_id,r.active,_utc(r.created_at)) if r else None
 def save_enrollment(self,x):
  with self.sf() as s:s.merge(EnrollmentRow(id=x.id,institution_id=x.institution_id,cohort_id=x.cohort_id,student_account_id=x.student_account_id,active=x.active,created_at=x.created_at));s.commit()
 def list_units(self,i):
  with self.sf() as s:return tuple(self._u(r) for r in s.scalars(select(UnitRow).where(UnitRow.institution_id==i).order_by(UnitRow.kind,UnitRow.name)).all())
 def list_periods(self,i):
  with self.sf() as s:return tuple(self._p(r) for r in s.scalars(select(PeriodRow).where(PeriodRow.institution_id==i).order_by(PeriodRow.starts_on.desc())).all())
 def list_members(self,i):
  with self.sf() as s:return tuple(self._m(r) for r in s.scalars(select(MembershipRow).where(MembershipRow.institution_id==i).order_by(MembershipRow.role,MembershipRow.account_id)).all())
 def list_cohorts(self,i):
  with self.sf() as s:return tuple(self._c(r) for r in s.scalars(select(CohortRow).where(CohortRow.institution_id==i).order_by(CohortRow.name)).all())
 def overview(self,i):
  with self.sf() as s:
   def n(model,*where):return int(s.scalar(select(func.count()).select_from(model).where(*where)) or 0)
   return {'institution_id':i,'units':n(UnitRow,UnitRow.institution_id==i,UnitRow.active==True),'members_active':n(MembershipRow,MembershipRow.institution_id==i,MembershipRow.state=='active'),'students_active':n(MembershipRow,MembershipRow.institution_id==i,MembershipRow.state=='active',MembershipRow.role=='student'),'teachers_active':n(MembershipRow,MembershipRow.institution_id==i,MembershipRow.state=='active',MembershipRow.role=='teacher'),'cohorts_active':n(CohortRow,CohortRow.institution_id==i,CohortRow.active==True),'enrollments_active':n(EnrollmentRow,EnrollmentRow.institution_id==i,EnrollmentRow.active==True)}
 def enrollments_for_cohort(self,c):
  with self.sf() as s:
   rows=s.scalars(select(EnrollmentRow).where(EnrollmentRow.cohort_id==c)).all();return tuple(Enrollment(r.id,r.institution_id,r.cohort_id,r.student_account_id,r.active,_utc(r.created_at)) for r in rows)
 def enrollments_for_student(self,i,a):
  with self.sf() as s:
   rows=s.scalars(select(EnrollmentRow).where(EnrollmentRow.institution_id==i,EnrollmentRow.student_account_id==a)).all();return tuple(Enrollment(r.id,r.institution_id,r.cohort_id,r.student_account_id,r.active,_utc(r.created_at)) for r in rows)

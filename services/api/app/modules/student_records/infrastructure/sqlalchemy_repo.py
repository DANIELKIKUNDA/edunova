from sqlalchemy import String,Integer,DateTime,Text,UniqueConstraint,select,update,insert
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.student_records.domain.model import *
class StudentRecordRow(Base):
 __tablename__='student_records';__table_args__=(UniqueConstraint('institution_id','account_id',name='uq_student_record_account'),UniqueConstraint('institution_id','matricule',name='uq_student_record_matricule'),UniqueConstraint('admission_review_id',name='uq_student_record_admission'))
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);account_id:Mapped[str]=mapped_column(String(64),index=True);matricule:Mapped[str]=mapped_column(String(80),index=True);admission_review_id:Mapped[str]=mapped_column(String(64),index=True);application_id:Mapped[str]=mapped_column(String(64),index=True);program_unit_id:Mapped[str]=mapped_column(String(64),index=True);curriculum_id:Mapped[str]=mapped_column(String(64),index=True);cohort_id:Mapped[str]=mapped_column(String(64),index=True);given_names:Mapped[str]=mapped_column(String(160));family_name:Mapped[str]=mapped_column(String(120));birth_date:Mapped[str|None]=mapped_column(String(20),nullable=True);nationality_code:Mapped[str|None]=mapped_column(String(8),nullable=True);email:Mapped[str|None]=mapped_column(String(320),nullable=True);phone_number:Mapped[str|None]=mapped_column(String(40),nullable=True);state:Mapped[str]=mapped_column(String(24),index=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class AcademicRegistrationRow(Base):
 __tablename__='student_academic_registrations';__table_args__=(UniqueConstraint('student_id','academic_year_id',name='uq_student_registration_year'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);student_id:Mapped[str]=mapped_column(String(64),index=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);academic_year_id:Mapped[str]=mapped_column(String(64),index=True);cohort_id:Mapped[str]=mapped_column(String(64),index=True);curriculum_id:Mapped[str]=mapped_column(String(64),index=True);state:Mapped[str]=mapped_column(String(24),index=True);registered_by:Mapped[str]=mapped_column(String(64));registered_at:Mapped[object]=mapped_column(DateTime(timezone=True));row_version:Mapped[int]=mapped_column(Integer)
class StudentEventRow(Base):
 __tablename__='student_record_events';id:Mapped[str]=mapped_column(String(64),primary_key=True);student_id:Mapped[str]=mapped_column(String(64),index=True);actor_id:Mapped[str]=mapped_column(String(64));event_type:Mapped[str]=mapped_column(String(80),index=True);from_state:Mapped[str|None]=mapped_column(String(24),nullable=True);to_state:Mapped[str|None]=mapped_column(String(24),nullable=True);note:Mapped[str|None]=mapped_column(String(1000),nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))

class StudentAdministrativeHistoryRow(Base):
 __tablename__='student_administrative_history'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);student_id:Mapped[str]=mapped_column(String(64),index=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);actor_id:Mapped[str]=mapped_column(String(64));action_type:Mapped[str]=mapped_column(String(64),index=True);reason:Mapped[str]=mapped_column(String(1000));before_json:Mapped[str|None]=mapped_column(Text,nullable=True);after_json:Mapped[str|None]=mapped_column(Text,nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))

class StudentMatriculeSequenceRow(Base):
 __tablename__='student_matricule_sequences';institution_id:Mapped[str]=mapped_column(String(64),primary_key=True);academic_year_id:Mapped[str]=mapped_column(String(64),primary_key=True);next_value:Mapped[int]=mapped_column(Integer)
class SqlStudentRecordRepository:
 def __init__(self,sf):self.sf=sf
 def _s(self,x):return StudentRecord(x.id,x.institution_id,x.account_id,x.matricule,x.admission_review_id,x.application_id,x.program_unit_id,x.curriculum_id,x.cohort_id,x.given_names,x.family_name,x.birth_date,x.nationality_code,x.email,x.phone_number,StudentState(x.state),x.row_version,x.created_at,x.updated_at)
 def _r(self,x):return AcademicRegistration(x.id,x.student_id,x.institution_id,x.academic_year_id,x.cohort_id,x.curriculum_id,RegistrationState(x.state),x.registered_by,x.registered_at,x.row_version)
 def get(self,sid):
  with self.sf() as s:x=s.get(StudentRecordRow,sid);return self._s(x) if x else None
 def by_account(self,i,a):
  with self.sf() as s:x=s.scalar(select(StudentRecordRow).where(StudentRecordRow.institution_id==i,StudentRecordRow.account_id==a));return self._s(x) if x else None
 def by_admission(self,rid):
  with self.sf() as s:x=s.scalar(select(StudentRecordRow).where(StudentRecordRow.admission_review_id==rid));return self._s(x) if x else None
 def save(self,x,expected=None):
  d=x.__dict__.copy();d['state']=x.state.value
  with self.sf() as s:
   old=s.get(StudentRecordRow,x.id)
   if not old:s.add(StudentRecordRow(**d));s.commit();return
   q=update(StudentRecordRow).where(StudentRecordRow.id==x.id)
   if expected is not None:q=q.where(StudentRecordRow.row_version==expected)
   r=s.execute(q.values(**d));
   if r.rowcount!=1:s.rollback();raise ValueError('student_record_concurrent_modification')
   s.commit()
 def registration(self,student_id,year_id):
  with self.sf() as s:x=s.scalar(select(AcademicRegistrationRow).where(AcademicRegistrationRow.student_id==student_id,AcademicRegistrationRow.academic_year_id==year_id));return self._r(x) if x else None
 def registrations(self,student_id):
  with self.sf() as s:return tuple(self._r(x) for x in s.scalars(select(AcademicRegistrationRow).where(AcademicRegistrationRow.student_id==student_id).order_by(AcademicRegistrationRow.registered_at)).all())
 def save_registration(self,x,expected=None):
  d=x.__dict__.copy();d['state']=x.state.value
  with self.sf() as s:
   old=s.get(AcademicRegistrationRow,x.id)
   if not old:s.add(AcademicRegistrationRow(**d));s.commit();return
   q=update(AcademicRegistrationRow).where(AcademicRegistrationRow.id==x.id)
   if expected is not None:q=q.where(AcademicRegistrationRow.row_version==expected)
   r=s.execute(q.values(**d))
   if r.rowcount!=1:s.rollback();raise ValueError('student_registration_concurrent_modification')
   s.commit()
 def next_matricule(self,institution_id,year_id,prefix):
  # Atomic increment for concurrent admissions; insert race retries as an update.
  with self.sf() as s:
   new_value=s.execute(update(StudentMatriculeSequenceRow).where(StudentMatriculeSequenceRow.institution_id==institution_id,StudentMatriculeSequenceRow.academic_year_id==year_id).values(next_value=StudentMatriculeSequenceRow.next_value+1).returning(StudentMatriculeSequenceRow.next_value)).scalar_one_or_none()
   if new_value is not None:s.commit();n=new_value-1
   else:
    try:s.execute(insert(StudentMatriculeSequenceRow).values(institution_id=institution_id,academic_year_id=year_id,next_value=2));s.commit();n=1
    except Exception:
     s.rollback();new_value=s.execute(update(StudentMatriculeSequenceRow).where(StudentMatriculeSequenceRow.institution_id==institution_id,StudentMatriculeSequenceRow.academic_year_id==year_id).values(next_value=StudentMatriculeSequenceRow.next_value+1).returning(StudentMatriculeSequenceRow.next_value)).scalar_one();s.commit();n=new_value-1
   return f'{prefix}-{n:06d}'
 def event(self,e):
  with self.sf() as s:s.add(StudentEventRow(**e.__dict__));s.commit()
 def events(self,sid):
  with self.sf() as s:return tuple(StudentEvent(x.id,x.student_id,x.actor_id,x.event_type,x.from_state,x.to_state,x.note,x.created_at) for x in s.scalars(select(StudentEventRow).where(StudentEventRow.student_id==sid).order_by(StudentEventRow.created_at)).all())
class StudentCourseRegistrationRow(Base):
 __tablename__='student_course_registrations';__table_args__=(UniqueConstraint('registration_id','curriculum_course_id',name='uq_student_course_registration'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);registration_id:Mapped[str]=mapped_column(String(64),index=True);student_id:Mapped[str]=mapped_column(String(64),index=True);curriculum_course_id:Mapped[str]=mapped_column(String(64),index=True);semester:Mapped[int]=mapped_column(Integer,index=True);course_code:Mapped[str|None]=mapped_column(String(80),nullable=True);course_title:Mapped[str]=mapped_column(String(300));credits:Mapped[str|None]=mapped_column(String(32),nullable=True);state:Mapped[str]=mapped_column(String(24),index=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
def _save_course_regs(self,rows):
 with self.sf() as s:
  for x in rows:s.add(StudentCourseRegistrationRow(id=x.id,registration_id=x.registration_id,student_id=x.student_id,curriculum_course_id=x.curriculum_course_id,semester=x.semester,course_code=x.course_code,course_title=x.course_title,credits=str(x.credits) if x.credits is not None else None,state=x.state.value,created_at=x.created_at))
  s.commit()
def _course_regs(self,sid):
 with self.sf() as s:
  rows=s.scalars(select(StudentCourseRegistrationRow).where(StudentCourseRegistrationRow.student_id==sid).order_by(StudentCourseRegistrationRow.semester,StudentCourseRegistrationRow.course_title)).all();return tuple(StudentCourseRegistration(x.id,x.registration_id,x.student_id,x.curriculum_course_id,x.semester,x.course_code,x.course_title,float(x.credits) if x.credits is not None else None,CourseRegistrationState(x.state),x.created_at) for x in rows)
SqlStudentRecordRepository.save_course_registrations=_save_course_regs
SqlStudentRecordRepository.course_registrations=_course_regs

def _admin_history_add(self,x):
 with self.sf() as s:s.add(StudentAdministrativeHistoryRow(**x.__dict__));s.commit()
def _admin_history(self,sid):
 with self.sf() as s:
  rows=s.scalars(select(StudentAdministrativeHistoryRow).where(StudentAdministrativeHistoryRow.student_id==sid).order_by(StudentAdministrativeHistoryRow.created_at)).all();return tuple(StudentAdministrativeHistory(x.id,x.student_id,x.institution_id,x.actor_id,x.action_type,x.reason,x.before_json,x.after_json,x.created_at) for x in rows)
SqlStudentRecordRepository.add_administrative_history=_admin_history_add
SqlStudentRecordRepository.administrative_history=_admin_history

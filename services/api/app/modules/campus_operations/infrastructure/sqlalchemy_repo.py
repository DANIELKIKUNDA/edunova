from __future__ import annotations
from datetime import UTC
from sqlalchemy import CheckConstraint, String,Integer,Float,DateTime,Boolean,UniqueConstraint,select,update
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.campus_operations.domain.model import *
def u(x):return x if x is None or x.tzinfo else x.replace(tzinfo=UTC)
class PolicyRow(Base):
 __tablename__='campus_attendance_policies';id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),unique=True,index=True);qr_ttl_seconds:Mapped[int]=mapped_column(Integer);require_device_binding:Mapped[bool]=mapped_column(Boolean);require_location:Mapped[bool]=mapped_column(Boolean);location_latitude:Mapped[float|None]=mapped_column(Float,nullable=True);location_longitude:Mapped[float|None]=mapped_column(Float,nullable=True);radius_meters:Mapped[int]=mapped_column(Integer);max_accuracy_meters:Mapped[int]=mapped_column(Integer);require_network_proof:Mapped[bool]=mapped_column(Boolean);proximity_mode:Mapped[str]=mapped_column(String(24),default='none');proximity_ttl_seconds:Mapped[int]=mapped_column(Integer,default=10);row_version:Mapped[int]=mapped_column(Integer);updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class AttendanceSessionRow(Base):
 __tablename__='campus_attendance_sessions';__table_args__=(UniqueConstraint('teaching_session_id',name='uq_attendance_teaching_session'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);teaching_session_id:Mapped[str]=mapped_column(String(64),index=True);offering_id:Mapped[str]=mapped_column(String(64),index=True);state:Mapped[str]=mapped_column(String(24),index=True);opens_at:Mapped[object]=mapped_column(DateTime(timezone=True));closes_at:Mapped[object]=mapped_column(DateTime(timezone=True));qr_epoch:Mapped[int]=mapped_column(Integer);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class AttendanceRecordRow(Base):
 __tablename__='campus_attendance_records';__table_args__=(UniqueConstraint('attendance_session_id','student_account_id',name='uq_attendance_student_session'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);attendance_session_id:Mapped[str]=mapped_column(String(64),index=True);student_account_id:Mapped[str]=mapped_column(String(64),index=True);status:Mapped[str]=mapped_column(String(24));recorded_at:Mapped[object]=mapped_column(DateTime(timezone=True));method:Mapped[str]=mapped_column(String(32));device_id:Mapped[str|None]=mapped_column(String(128),nullable=True);risk_score:Mapped[int]=mapped_column(Integer);review:Mapped[str]=mapped_column(String(24),index=True);evidence:Mapped[str]=mapped_column(String(4000));row_version:Mapped[int]=mapped_column(Integer);updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class DeviceRow(Base):
 __tablename__='campus_attendance_devices';__table_args__=(UniqueConstraint('institution_id','student_account_id',name='uq_attendance_student_device'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);student_account_id:Mapped[str]=mapped_column(String(64),index=True);device_id:Mapped[str]=mapped_column(String(128),index=True);bound_at:Mapped[object]=mapped_column(DateTime(timezone=True));active:Mapped[bool]=mapped_column(Boolean)
class AnnouncementRow(Base):
 __tablename__='campus_announcements';id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);offering_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);title:Mapped[str]=mapped_column(String(240));body:Mapped[str]=mapped_column(String(8000));audience:Mapped[str]=mapped_column(String(32));state:Mapped[str]=mapped_column(String(24),default='draft',index=True);publish_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True);published_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True,index=True);created_by:Mapped[str]=mapped_column(String(64));row_version:Mapped[int]=mapped_column(Integer,default=1);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class AbsenceRequestRow(Base):
 __tablename__='campus_absence_requests';__table_args__=(UniqueConstraint('attendance_session_id','student_account_id',name='uq_absence_request_student_session'),);id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);attendance_session_id:Mapped[str]=mapped_column(String(64),index=True);student_account_id:Mapped[str]=mapped_column(String(64),index=True);reason:Mapped[str]=mapped_column(String(2000));evidence_uri:Mapped[str|None]=mapped_column(String(1000),nullable=True);state:Mapped[str]=mapped_column(String(24),index=True);decision_reason:Mapped[str|None]=mapped_column(String(2000),nullable=True);decided_by:Mapped[str|None]=mapped_column(String(64),nullable=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class CalendarEventRow(Base):
 __tablename__='campus_calendar_events';id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);offering_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);cohort_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);kind:Mapped[str]=mapped_column(String(24),index=True);title:Mapped[str]=mapped_column(String(240));details:Mapped[str]=mapped_column(String(4000));starts_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True);ends_at:Mapped[object]=mapped_column(DateTime(timezone=True));location:Mapped[str|None]=mapped_column(String(240),nullable=True);state:Mapped[str]=mapped_column(String(24),index=True);source_ref:Mapped[str|None]=mapped_column(String(128),nullable=True,index=True);registration_capacity:Mapped[int]=mapped_column(Integer,CheckConstraint('registration_capacity BETWEEN 0 AND 5000',name='ck_campus_event_capacity'),nullable=False,default=0);row_version:Mapped[int]=mapped_column(Integer);created_by:Mapped[str]=mapped_column(String(64));created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SqlAlchemyCampusOperationsRepository:
 def __init__(self,sf):self.sf=sf
 def _p(self,r):return AttendancePolicy(r.id,r.institution_id,r.qr_ttl_seconds,r.require_device_binding,r.require_location,r.location_latitude,r.location_longitude,r.radius_meters,r.max_accuracy_meters,r.require_network_proof,ProximityMode(r.proximity_mode),r.proximity_ttl_seconds,r.row_version,u(r.updated_at))
 def policy(self,i):
  with self.sf() as s:r=s.scalar(select(PolicyRow).where(PolicyRow.institution_id==i));return self._p(r) if r else None
 def save_policy(self,x):
  with self.sf() as s:
   r=s.scalar(select(PolicyRow).where(PolicyRow.institution_id==x.institution_id))
   if r:
    for k in ('qr_ttl_seconds','require_device_binding','require_location','location_latitude','location_longitude','radius_meters','max_accuracy_meters','require_network_proof','proximity_mode','proximity_ttl_seconds','row_version','updated_at'):setattr(r,k,getattr(x,k).value if k=='proximity_mode' else getattr(x,k))
   else:s.add(PolicyRow(**{k:(getattr(x,k).value if k=='proximity_mode' else getattr(x,k)) for k in x.__dataclass_fields__}))
   s.commit()
 def _s(self,r):return AttendanceSession(r.id,r.institution_id,r.teaching_session_id,r.offering_id,AttendanceSessionState(r.state),u(r.opens_at),u(r.closes_at),r.qr_epoch,r.row_version,r.created_by,u(r.created_at),u(r.updated_at))
 def attendance_session(self,i,id):
  with self.sf() as s:r=s.get(AttendanceSessionRow,id);return self._s(r) if r and r.institution_id==i else None
 def attendance_for_teaching_session(self,i,tid):
  with self.sf() as s:r=s.scalar(select(AttendanceSessionRow).where(AttendanceSessionRow.institution_id==i,AttendanceSessionRow.teaching_session_id==tid));return self._s(r) if r else None
 def save_session(self,x,expected=None):
  d={k:getattr(x,k) for k in x.__dataclass_fields__};d['state']=x.state.value
  with self.sf() as s:
   old=s.get(AttendanceSessionRow,x.id)
   if not old:s.add(AttendanceSessionRow(**d));s.commit();return
   q=update(AttendanceSessionRow).where(AttendanceSessionRow.id==x.id)
   if expected is not None:q=q.where(AttendanceSessionRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('attendance_concurrent_modification')
   s.commit()
 def bound_device(self,i,a):
  with self.sf() as s:r=s.scalar(select(DeviceRow).where(DeviceRow.institution_id==i,DeviceRow.student_account_id==a,DeviceRow.active==True));return r.device_id if r else None
 def bind_device(self,i,a,d,now):
  with self.sf() as s:
   r=s.scalar(select(DeviceRow).where(DeviceRow.institution_id==i,DeviceRow.student_account_id==a))
   if r:r.device_id=d;r.bound_at=now;r.active=True
   else:s.add(DeviceRow(id=f'dev_{__import__("uuid").uuid4().hex}',institution_id=i,student_account_id=a,device_id=d,bound_at=now,active=True))
   s.commit()
 def _r(self,r):return AttendanceRecord(r.id,r.institution_id,r.attendance_session_id,r.student_account_id,AttendanceStatus(r.status),u(r.recorded_at),r.method,r.device_id,r.risk_score,AttendanceReview(r.review),r.evidence,r.row_version,u(r.updated_at))
 def record(self,sid,a):
  with self.sf() as s:r=s.scalar(select(AttendanceRecordRow).where(AttendanceRecordRow.attendance_session_id==sid,AttendanceRecordRow.student_account_id==a));return self._r(r) if r else None
 def save_record(self,x,expected=None):
  d={k:getattr(x,k) for k in x.__dataclass_fields__};d['status']=x.status.value;d['review']=x.review.value
  with self.sf() as s:
   old=s.get(AttendanceRecordRow,x.id)
   if not old:s.add(AttendanceRecordRow(**d));s.commit();return
   q=update(AttendanceRecordRow).where(AttendanceRecordRow.id==x.id)
   if expected is not None:q=q.where(AttendanceRecordRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('attendance_concurrent_modification')
   s.commit()
 def records(self,sid):
  with self.sf() as s:return tuple(self._r(r) for r in s.scalars(select(AttendanceRecordRow).where(AttendanceRecordRow.attendance_session_id==sid)).all())
 def _an(self,r):return Announcement(r.id,r.institution_id,r.offering_id,r.title,r.body,r.audience,AnnouncementState(r.state),u(r.publish_at),u(r.published_at),r.created_by,r.row_version,u(r.created_at),u(r.updated_at))
 def announcement(self,i,id):
  with self.sf() as s:r=s.get(AnnouncementRow,id);return self._an(r) if r and r.institution_id==i else None
 def save_announcement(self,x,expected=None):
  d={k:getattr(x,k) for k in x.__dataclass_fields__};d['state']=x.state.value
  with self.sf() as s:
   old=s.get(AnnouncementRow,x.id)
   if not old:s.add(AnnouncementRow(**d));s.commit();return
   q=update(AnnouncementRow).where(AnnouncementRow.id==x.id)
   if expected is not None:q=q.where(AnnouncementRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('campus_operations_concurrent_modification')
   s.commit()
 def announcements(self,i):
  with self.sf() as s:return tuple(self._an(r) for r in s.scalars(select(AnnouncementRow).where(AnnouncementRow.institution_id==i).order_by(AnnouncementRow.publish_at.desc())).all())
 def _ab(self,r):return AbsenceRequest(r.id,r.institution_id,r.attendance_session_id,r.student_account_id,r.reason,r.evidence_uri,AbsenceRequestState(r.state),r.decision_reason,r.decided_by,r.row_version,u(r.created_at),u(r.updated_at))
 def absence_request(self,i,id):
  with self.sf() as s:r=s.get(AbsenceRequestRow,id);return self._ab(r) if r and r.institution_id==i else None
 def absence_for_student_session(self,sid,a):
  with self.sf() as s:r=s.scalar(select(AbsenceRequestRow).where(AbsenceRequestRow.attendance_session_id==sid,AbsenceRequestRow.student_account_id==a));return self._ab(r) if r else None
 def save_absence(self,x,expected=None):
  d={k:getattr(x,k) for k in x.__dataclass_fields__};d['state']=x.state.value
  with self.sf() as s:
   old=s.get(AbsenceRequestRow,x.id)
   if not old:s.add(AbsenceRequestRow(**d));s.commit();return
   q=update(AbsenceRequestRow).where(AbsenceRequestRow.id==x.id)
   if expected is not None:q=q.where(AbsenceRequestRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('campus_operations_concurrent_modification')
   s.commit()
 def absences(self,i):
  with self.sf() as s:return tuple(self._ab(r) for r in s.scalars(select(AbsenceRequestRow).where(AbsenceRequestRow.institution_id==i).order_by(AbsenceRequestRow.created_at.desc())).all())
 def _ev(self,r):return CalendarEvent(r.id,r.institution_id,r.offering_id,r.cohort_id,CalendarEventKind(r.kind),r.title,r.details,u(r.starts_at),u(r.ends_at),r.location,CalendarEventState(r.state),r.source_ref,r.row_version,r.created_by,u(r.created_at),u(r.updated_at))
 def event(self,i,id):
  with self.sf() as s:r=s.get(CalendarEventRow,id);return self._ev(r) if r and r.institution_id==i else None
 def save_event(self,x,expected=None):
  d={k:getattr(x,k) for k in x.__dataclass_fields__};d['kind']=x.kind.value;d['state']=x.state.value
  with self.sf() as s:
   old=s.get(CalendarEventRow,x.id)
   if not old:s.add(CalendarEventRow(**d));s.commit();return
   q=update(CalendarEventRow).where(CalendarEventRow.id==x.id)
   if expected is not None:q=q.where(CalendarEventRow.row_version==expected)
   if s.execute(q.values(**d)).rowcount!=1:s.rollback();raise ValueError('campus_operations_concurrent_modification')
   s.commit()
 def events(self,i):
  with self.sf() as s:return tuple(self._ev(r) for r in s.scalars(select(CalendarEventRow).where(CalendarEventRow.institution_id==i).order_by(CalendarEventRow.starts_at)).all())

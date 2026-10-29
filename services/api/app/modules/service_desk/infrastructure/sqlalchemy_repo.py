from sqlalchemy import String,Integer,DateTime,ForeignKey,select,update,func
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.service_desk.domain.model import *
class ServiceRequestRow(Base):
 __tablename__='student_service_requests'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);student_id:Mapped[str]=mapped_column(String(64),index=True);requester_account_id:Mapped[str]=mapped_column(String(64),index=True);kind:Mapped[str]=mapped_column(String(32));subject:Mapped[str]=mapped_column(String(200));details:Mapped[str]=mapped_column(String(4000));state:Mapped[str]=mapped_column(String(32),index=True);assigned_to:Mapped[str|None]=mapped_column(String(64),nullable=True);decision_reason:Mapped[str|None]=mapped_column(String(2000),nullable=True);output_document_ref:Mapped[str|None]=mapped_column(String(500),nullable=True);output_sha256:Mapped[str|None]=mapped_column(String(64),nullable=True);version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class RequestEventRow(Base):
 __tablename__='student_service_request_events'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);request_id:Mapped[str]=mapped_column(String(64),ForeignKey('student_service_requests.id'),index=True);actor_id:Mapped[str]=mapped_column(String(64));event_type:Mapped[str]=mapped_column(String(64));note:Mapped[str|None]=mapped_column(String(2000),nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
def cv(r):return ServiceRequest(r.id,r.institution_id,r.student_id,r.requester_account_id,RequestKind(r.kind),r.subject,r.details,RequestState(r.state),r.assigned_to,r.decision_reason,r.output_document_ref,r.output_sha256,r.version,r.created_at,r.updated_at) if r else None
def ev(r):return RequestEvent(r.id,r.request_id,r.actor_id,r.event_type,r.note,r.created_at)
class SqlServiceDeskRepository:
 def __init__(self,sf):self.sf=sf
 def create(self,x):
  with self.sf() as s:s.add(ServiceRequestRow(**{**x.__dict__,'kind':x.kind.value,'state':x.state.value}));s.commit()
 def get(self,i,rid):
  with self.sf() as s:return cv(s.scalar(select(ServiceRequestRow).where(ServiceRequestRow.id==rid,ServiceRequestRow.institution_id==i)))
 def save(self,x,expected):
  with self.sf() as s:
   q=s.execute(update(ServiceRequestRow).where(ServiceRequestRow.id==x.id,ServiceRequestRow.institution_id==x.institution_id,ServiceRequestRow.version==expected).values(state=x.state.value,assigned_to=x.assigned_to,decision_reason=x.decision_reason,output_document_ref=x.output_document_ref,output_sha256=x.output_sha256,version=x.version,updated_at=x.updated_at))
   if q.rowcount!=1:s.rollback();raise ValueError('service_request_concurrent_modification')
   s.commit()

 def create_with_event(self,x,event):
  """Persist the request and its first timeline event in one DB transaction."""
  with self.sf() as s:
   s.add(ServiceRequestRow(**{**x.__dict__,'kind':x.kind.value,'state':x.state.value}))
   s.add(RequestEventRow(**event.__dict__))
   s.commit()
 def save_with_event(self,x,expected,event):
  """Optimistic-lock the request mutation and append its timeline event atomically."""
  with self.sf() as s:
   q=s.execute(update(ServiceRequestRow).where(ServiceRequestRow.id==x.id,ServiceRequestRow.institution_id==x.institution_id,ServiceRequestRow.version==expected).values(state=x.state.value,assigned_to=x.assigned_to,decision_reason=x.decision_reason,output_document_ref=x.output_document_ref,output_sha256=x.output_sha256,version=x.version,updated_at=x.updated_at))
   if q.rowcount!=1:
    s.rollback();raise ValueError('service_request_concurrent_modification')
   s.add(RequestEventRow(**event.__dict__))
   s.commit()
 def list_student(self,i,sid):
  with self.sf() as s:return [cv(x) for x in s.scalars(select(ServiceRequestRow).where(ServiceRequestRow.institution_id==i,ServiceRequestRow.student_id==sid).order_by(ServiceRequestRow.created_at.desc())).all()]
 def add_event(self,x):
  with self.sf() as s:s.add(RequestEventRow(**x.__dict__));s.commit()
 def events(self,rid):
  with self.sf() as s:return [ev(x) for x in s.scalars(select(RequestEventRow).where(RequestEventRow.request_id==rid).order_by(RequestEventRow.created_at)).all()]

 def list_queue(self,i,state=None,assigned_to=None,limit=100,offset=0):
  with self.sf() as s:
   stmt=select(ServiceRequestRow).where(ServiceRequestRow.institution_id==i)
   if state is not None:stmt=stmt.where(ServiceRequestRow.state==state)
   if assigned_to is not None:stmt=stmt.where(ServiceRequestRow.assigned_to==assigned_to)
   stmt=stmt.order_by(ServiceRequestRow.created_at.desc(),ServiceRequestRow.id).limit(limit).offset(offset)
   return [cv(row) for row in s.scalars(stmt).all()]
 def status_counts(self,i):
  with self.sf() as s:
   rows=s.execute(select(ServiceRequestRow.state,func.count()).where(ServiceRequestRow.institution_id==i).group_by(ServiceRequestRow.state)).all()
   return {'institution_id':i,'total':sum(count for _,count in rows),'by_status':{state:count for state,count in rows}}

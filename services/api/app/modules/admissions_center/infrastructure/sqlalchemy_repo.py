from sqlalchemy import String,Integer,DateTime,UniqueConstraint,select,update,Boolean
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.admissions_center.domain.model import *
class AdmissionReviewRow(Base):
 __tablename__='admission_reviews';__table_args__=(UniqueConstraint('application_id',name='uq_admission_review_application'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);application_id:Mapped[str]=mapped_column(String(64),index=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);state:Mapped[str]=mapped_column(String(32),index=True);assigned_to:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);decision_reason:Mapped[str|None]=mapped_column(String(1000),nullable=True);row_version:Mapped[int]=mapped_column(Integer);created_at:Mapped[object]=mapped_column(DateTime(timezone=True));updated_at:Mapped[object]=mapped_column(DateTime(timezone=True));decided_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
class DocumentReviewRow(Base):
 __tablename__='admission_document_reviews';__table_args__=(UniqueConstraint('review_id','document_id',name='uq_review_document'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);review_id:Mapped[str]=mapped_column(String(64),index=True);document_id:Mapped[str]=mapped_column(String(64),index=True);state:Mapped[str]=mapped_column(String(32),index=True);note:Mapped[str|None]=mapped_column(String(1000),nullable=True);reviewed_by:Mapped[str]=mapped_column(String(64));reviewed_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SqlAdmissionReviewRepository:
 def __init__(self,sf):self.sf=sf
 def _r(self,x):return AdmissionReview(x.id,x.application_id,x.institution_id,ReviewState(x.state),x.assigned_to,x.decision_reason,x.row_version,x.created_at,x.updated_at,x.decided_at)
 def _d(self,x):return DocumentReview(x.id,x.review_id,x.document_id,DocumentReviewState(x.state),x.note,x.reviewed_by,x.reviewed_at)
 def by_application(self,aid):
  with self.sf() as s:x=s.scalar(select(AdmissionReviewRow).where(AdmissionReviewRow.application_id==aid));return self._r(x) if x else None
 def get(self,rid):
  with self.sf() as s:x=s.get(AdmissionReviewRow,rid);return self._r(x) if x else None
 def save(self,x,expected=None):
  d=x.__dict__.copy();d['state']=x.state.value
  with self.sf() as s:
   old=s.get(AdmissionReviewRow,x.id)
   if not old:s.add(AdmissionReviewRow(**d));s.commit();return
   q=update(AdmissionReviewRow).where(AdmissionReviewRow.id==x.id)
   if expected is not None:q=q.where(AdmissionReviewRow.row_version==expected)
   r=s.execute(q.values(**d));
   if r.rowcount!=1:s.rollback();raise ValueError('admission_review_concurrent_modification')
   s.commit()
 def list(self,iid,state=None):
  with self.sf() as s:
   q=select(AdmissionReviewRow).where(AdmissionReviewRow.institution_id==iid)
   if state:q=q.where(AdmissionReviewRow.state==state)
   return tuple(self._r(x) for x in s.scalars(q.order_by(AdmissionReviewRow.created_at)).all())
 def save_doc_review(self,x):
  with self.sf() as s:
   old=s.scalar(select(DocumentReviewRow).where(DocumentReviewRow.review_id==x.review_id,DocumentReviewRow.document_id==x.document_id));d=x.__dict__.copy();d['state']=x.state.value
   if old:
    for k,v in d.items():setattr(old,k,v)
   else:s.add(DocumentReviewRow(**d))
   s.commit()
 def doc_reviews(self,rid):
  with self.sf() as s:return tuple(self._d(x) for x in s.scalars(select(DocumentReviewRow).where(DocumentReviewRow.review_id==rid)).all())
class AdmissionCommitteeRow(Base):
 __tablename__='admission_committees'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);institution_id:Mapped[str]=mapped_column(String(64),index=True);campaign_id:Mapped[str]=mapped_column(String(64),index=True);name:Mapped[str]=mapped_column(String(200));chair_account_id:Mapped[str]=mapped_column(String(64));quorum:Mapped[int]=mapped_column(Integer);active:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class AdmissionCommitteeMemberRow(Base):
 __tablename__='admission_committee_members';__table_args__=(UniqueConstraint('committee_id','account_id',name='uq_admission_committee_member'),)
 committee_id:Mapped[str]=mapped_column(String(64),primary_key=True);account_id:Mapped[str]=mapped_column(String(64),primary_key=True);voting:Mapped[bool]=mapped_column(Boolean,default=True)
class AdmissionCommitteeVoteRow(Base):
 __tablename__='admission_committee_votes';__table_args__=(UniqueConstraint('committee_id','review_id','voter_account_id',name='uq_admission_committee_vote'),)
 id:Mapped[str]=mapped_column(String(64),primary_key=True);committee_id:Mapped[str]=mapped_column(String(64),index=True);review_id:Mapped[str]=mapped_column(String(64),index=True);voter_account_id:Mapped[str]=mapped_column(String(64));recommendation:Mapped[str]=mapped_column(String(24));note:Mapped[str|None]=mapped_column(String(1000),nullable=True);voted_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class AdmissionEventRow(Base):
 __tablename__='admission_events'
 id:Mapped[str]=mapped_column(String(64),primary_key=True);review_id:Mapped[str]=mapped_column(String(64),index=True);actor_id:Mapped[str]=mapped_column(String(64));event_type:Mapped[str]=mapped_column(String(80),index=True);from_state:Mapped[str|None]=mapped_column(String(32),nullable=True);to_state:Mapped[str|None]=mapped_column(String(32),nullable=True);note:Mapped[str|None]=mapped_column(String(1000),nullable=True);created_at:Mapped[object]=mapped_column(DateTime(timezone=True))

def _save_event(self,e):
 with self.sf() as s:s.add(AdmissionEventRow(**e.__dict__));s.commit()
def _events(self,rid):
 with self.sf() as s:return tuple(AdmissionEvent(x.id,x.review_id,x.actor_id,x.event_type,x.from_state,x.to_state,x.note,x.created_at) for x in s.scalars(select(AdmissionEventRow).where(AdmissionEventRow.review_id==rid).order_by(AdmissionEventRow.created_at)).all())
def _save_committee(self,c,members):
 with self.sf() as s:
  s.add(AdmissionCommitteeRow(**c.__dict__))
  for a,v in members:s.add(AdmissionCommitteeMemberRow(committee_id=c.id,account_id=a,voting=v))
  s.commit()
def _committee(self,cid):
 with self.sf() as s:
  x=s.get(AdmissionCommitteeRow,cid)
  if not x:return None
  return AdmissionCommittee(x.id,x.institution_id,x.campaign_id,x.name,x.chair_account_id,x.quorum,x.active,x.created_at)
def _committee_members(self,cid):
 with self.sf() as s:return tuple(CommitteeMember(x.committee_id,x.account_id,x.voting) for x in s.scalars(select(AdmissionCommitteeMemberRow).where(AdmissionCommitteeMemberRow.committee_id==cid)).all())
def _save_vote(self,v):
 with self.sf() as s:
  old=s.scalar(select(AdmissionCommitteeVoteRow).where(AdmissionCommitteeVoteRow.committee_id==v.committee_id,AdmissionCommitteeVoteRow.review_id==v.review_id,AdmissionCommitteeVoteRow.voter_account_id==v.voter_account_id))
  if old:
   old.recommendation=v.recommendation;old.note=v.note;old.voted_at=v.voted_at
  else:s.add(AdmissionCommitteeVoteRow(**v.__dict__))
  s.commit()
def _votes(self,cid,rid):
 with self.sf() as s:return tuple(CommitteeVote(x.id,x.committee_id,x.review_id,x.voter_account_id,x.recommendation,x.note,x.voted_at) for x in s.scalars(select(AdmissionCommitteeVoteRow).where(AdmissionCommitteeVoteRow.committee_id==cid,AdmissionCommitteeVoteRow.review_id==rid)).all())
def _count_state_for_campaign(self,campaign_id,state,apps):
 count=0
 for r in self.list_all():
  app=apps.get(r.application_id)
  if app and app.campaign_id==campaign_id and r.state==state:count+=1
 return count
def _list_all(self):
 with self.sf() as s:return tuple(self._r(x) for x in s.scalars(select(AdmissionReviewRow)).all())
SqlAdmissionReviewRepository.save_event=_save_event
SqlAdmissionReviewRepository.events=_events
SqlAdmissionReviewRepository.save_committee=_save_committee
SqlAdmissionReviewRepository.committee=_committee
SqlAdmissionReviewRepository.committee_members=_committee_members
SqlAdmissionReviewRepository.save_vote=_save_vote
SqlAdmissionReviewRepository.votes=_votes
SqlAdmissionReviewRepository.list_all=_list_all
SqlAdmissionReviewRepository.count_state_for_campaign=_count_state_for_campaign

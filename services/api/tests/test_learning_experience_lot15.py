from datetime import UTC,datetime
from app.modules.learning_experience.domain.model import *
from app.modules.learning_experience.application.service import LearningExperienceService
class Repo:
 def __init__(self): self.sessions={}; self.progresses={}; self.cards={}; self.errors=[]
 def save_session(self,x): self.sessions[x.id]=x
 def session(self,id): return self.sessions.get(id)
 def active_session(self,a): return next((x for x in self.sessions.values() if x.account_id==a and x.state in {SessionState.ACTIVE,SessionState.PAUSED}),None)
 def recent_sessions(self,a,limit=20): return tuple(list(self.sessions.values())[-limit:])
 def progress(self,a,c,ch=None): return self.progresses.get((a,c,ch))
 def save_progress(self,x): self.progresses[(x.account_id,x.course_id,x.chapter_id)]=x
 def save_error(self,x):
  self.errors=[e for e in self.errors if e.id!=x.id]; self.errors.append(x)
 def unresolved_errors(self,a,limit=50): return [x for x in self.errors if x.account_id==a and not x.resolved]
 def error(self,a,id): return next((x for x in self.errors if x.account_id==a and x.id==id),None)
 def due_errors(self,a,now,limit=50): return [x for x in self.errors if x.account_id==a and not x.resolved and x.next_review_at and x.next_review_at<=now][:limit]
 def review_card(self,a,id): return self.cards.get((a,id))
 def save_review_card(self,x): self.cards[(x.account_id,x.card_id)]=x
 def due_cards(self,a,now,limit=100): return tuple(x for x in self.cards.values() if x.account_id==a and x.due_at<=now)
 def dashboard(self,a,now): return {'study_seconds':0,'open_errors':len(self.errors),'due_flashcards':0,'mastered_units':0}
def svc(): return LearningExperienceService(Repo(),lambda:datetime(2026,9,24,tzinfo=UTC))
def test_session_lifecycle_and_optimistic_version():
 s=svc(); x=s.start('u','c','ch',StudyMode.FOCUS,'Réviser'); y=s.mutate('u',x.id,'checkpoint',active_seconds=600,last_position='page:12',expected_version=1); assert y.active_seconds==600 and y.row_version==2
 z=s.mutate('u',x.id,'complete',active_seconds=60,expected_version=2); assert z.state==SessionState.COMPLETED and z.active_seconds==660
def test_only_one_open_session():
 import pytest
 s=svc(); s.start('u','c',None,StudyMode.READ)
 with pytest.raises(ValueError,match='active_session_exists'): s.start('u','c2',None,StudyMode.READ)
def test_mastery_is_monotonic_and_accuracy_accumulates():
 s=svc(); a=s.record_progress('u','c','ch',MasteryStage.ASSESSED,.8,8,10); b=s.record_progress('u','c','ch',MasteryStage.VIEWED,.2,0,0); assert b.stage==MasteryStage.ASSESSED and b.completion_ratio==.8 and b.accuracy==.8
def test_spaced_repetition_sm2_semantics():
 now=datetime(2026,9,24,tzinfo=UTC); c=next_spaced_review(None,quality=5,now=now,account_id='u',card_id='x',course_id='c',chapter_id=None); assert c.repetitions==1 and c.interval_days==1
 c2=next_spaced_review(c,quality=5,now=now,account_id='u',card_id='x',course_id='c',chapter_id=None); assert c2.repetitions==2 and c2.interval_days==6
 c3=next_spaced_review(c2,quality=1,now=now,account_id='u',card_id='x',course_id='c',chapter_id=None); assert c3.repetitions==0 and c3.interval_days==1
def test_error_bank_and_home_resume():
 s=svc(); x=s.start('u','c','ch',StudyMode.QUIZ); s.add_error('u','c','ch','quiz','q1','Question?','Réponse'); h=s.home('u'); assert h['active_session']==x.id and h['open_errors']==1
def test_invalid_progress_rejected():
 import pytest
 s=svc()
 with pytest.raises(ValueError): s.record_progress('u','c',None,MasteryStage.ASSESSED,.5,6,5)

def test_error_review_resolves_or_reschedules():
 s=svc(); e=s.add_error('u','c','ch','quiz','q1','Question?','R'); bad=s.review_error('u',e.id,correct=False); assert bad.attempts==2 and not bad.resolved and bad.next_review_at>e.next_review_at
 good=s.review_error('u',e.id,correct=True); assert good.resolved and good.next_review_at is None

def test_exam_plan_requires_future_date_and_courses():
 from datetime import timedelta
 import pytest
 s=svc(); r=s.repo; r.exam_plans_store={}; r.save_exam_plan=lambda x:r.exam_plans_store.__setitem__(x.id,x)
 x=s.create_exam_plan('u','Session janvier',datetime(2026,10,24,tzinfo=UTC),45,['anatomie','physio','anatomie']); assert x.daily_minutes==45 and x.course_ids==('anatomie','physio')
 with pytest.raises(ValueError,match='exam_must_be_future'): s.create_exam_plan('u','Passé',datetime(2026,9,1,tzinfo=UTC),45,['c'])

def test_recommendations_prioritize_resume():
 s=svc(); r=s.repo
 r.due_errors=lambda a,now,limit=10: []
 s.start('u','c','ch',StudyMode.READ)
 rec=s.recommendations('u'); assert rec[0].kind=='resume' and rec[0].priority==120

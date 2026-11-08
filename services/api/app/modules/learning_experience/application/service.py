from __future__ import annotations
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4
from app.modules.learning_experience.domain.model import *
class LearningExperienceService:
 def __init__(self,repo,now,audit=None): self.repo=repo; self.now=now; self.audit=audit
 def _audit(self,actor,action,target,payload=None):
  if self.audit:
   try:self.audit.record(actor_id=actor,action=action,target_type='learning',target_id=target,payload=payload or {})
   except TypeError: pass
 def start(self,a,course,chapter,mode,objective=None):
  old=self.repo.active_session(a)
  if old and old.state==SessionState.ACTIVE: raise ValueError('active_session_exists')
  now=self.now(); x=StudySession(uuid4().hex,a,course,chapter,mode,SessionState.ACTIVE,now,now,None,0,None,objective,1); self.repo.save_session(x); self._audit(a,'study.started',x.id,{'mode':mode.value}); return x
 def mutate(self,a,id,action,*,active_seconds=0,last_position=None,expected_version=None):
  x=self.repo.session(id)
  if not x or x.account_id!=a: raise LookupError('session_not_found')
  if expected_version is not None and x.row_version!=expected_version: raise ValueError('concurrent_session_update')
  now=self.now(); state=x.state; ended=x.ended_at
  if action=='pause' and state==SessionState.ACTIVE: state=SessionState.PAUSED
  elif action=='resume' and state==SessionState.PAUSED: state=SessionState.ACTIVE
  elif action=='complete' and state in {SessionState.ACTIVE,SessionState.PAUSED}: state=SessionState.COMPLETED; ended=now
  elif action=='abandon' and state in {SessionState.ACTIVE,SessionState.PAUSED}: state=SessionState.ABANDONED; ended=now
  elif action=='checkpoint' and state in {SessionState.ACTIVE,SessionState.PAUSED}: pass
  else: raise ValueError('invalid_session_transition')
  y=replace(x,state=state,updated_at=now,ended_at=ended,active_seconds=x.active_seconds+max(0,min(active_seconds,7200)),last_position=last_position or x.last_position,row_version=x.row_version+1); self.repo.save_session(y); self._audit(a,'study.'+action,id); return y
 def record_progress(self,a,course,chapter,stage,completion_ratio,correct=0,total=0):
  if not 0<=completion_ratio<=1 or correct<0 or total<0 or correct>total: raise ValueError('invalid_progress_signal')
  now=self.now(); old=self.repo.progress(a,course,chapter)
  if old:
   final=old.promote(stage); x=replace(old,stage=final,completion_ratio=max(old.completion_ratio,completion_ratio),practice_attempts=old.practice_attempts+(1 if stage==MasteryStage.PRACTICED else 0),assessment_attempts=old.assessment_attempts+(1 if stage in {MasteryStage.ASSESSED,MasteryStage.MASTERED} else 0),correct_answers=old.correct_answers+correct,total_answers=old.total_answers+total,updated_at=now)
  else:x=LearningProgress(a,course,chapter,stage,completion_ratio,1 if stage==MasteryStage.PRACTICED else 0,1 if stage in {MasteryStage.ASSESSED,MasteryStage.MASTERED} else 0,correct,total,now)
  self.repo.save_progress(x); return x
 def add_error(self,a,course,chapter,source_type,source_id,prompt,correct_answer=None):
  now=self.now(); x=ErrorItem(uuid4().hex,a,course,chapter,source_type,source_id,prompt,correct_answer,1,False,now+timedelta(days=1),now,now); self.repo.save_error(x); return x
 def review(self,a,card_id,course,chapter,quality):
  x=next_spaced_review(self.repo.review_card(a,card_id),quality=quality,now=self.now(),account_id=a,card_id=card_id,course_id=course,chapter_id=chapter); self.repo.save_review_card(x); return x
 def home(self,a):
  now=self.now(); active=self.repo.active_session(a); d=self.repo.dashboard(a,now); d.update({'active_session': active.id if active else None,'recent':[{'id':x.id,'course_id':x.course_id,'mode':x.mode.value,'state':x.state.value,'last_position':x.last_position,'updated_at':x.updated_at} for x in self.repo.recent_sessions(a,5)]}); return d

 def review_error(self,a,error_id,*,correct:bool):
  x=self.repo.error(a,error_id)
  if not x: raise LookupError('error_not_found')
  now=self.now(); attempts=x.attempts+1
  if correct:
   y=replace(x,attempts=attempts,resolved=True,next_review_at=None,updated_at=now)
  else:
   delay=min(14,2**min(attempts-1,3)); y=replace(x,attempts=attempts,resolved=False,next_review_at=now+timedelta(days=delay),updated_at=now)
  self.repo.save_error(y); self._audit(a,'error.reviewed',error_id,{'correct':correct,'resolved':y.resolved}); return y
 def create_exam_plan(self,a,title,exam_at,daily_minutes,course_ids):
  now=self.now()
  if exam_at<=now: raise ValueError('exam_must_be_future')
  if not 10<=daily_minutes<=480 or not course_ids or len(course_ids)>30: raise ValueError('invalid_exam_plan')
  clean=tuple(dict.fromkeys(x.strip() for x in course_ids if x.strip()))
  if not clean: raise ValueError('invalid_exam_plan')
  x=ExamPlan(uuid4().hex,a,title.strip()[:160],exam_at,daily_minutes,clean,ExamPlanState.ACTIVE,now,now,1); self.repo.save_exam_plan(x); self._audit(a,'exam_plan.created',x.id,{'courses':len(clean)}); return x
 def exam_plans(self,a): return self.repo.exam_plans(a)

 def recommendations(self,a):
  now=self.now(); out=[]
  for e in self.repo.due_errors(a,now,10): out.append(StudyRecommendation('error',100,'Revoir une erreur','Erreur arrivée à échéance',e.course_id,e.chapter_id))
  for c in self.repo.due_cards(a,now,10): out.append(StudyRecommendation('flashcard',80,'Réviser une flashcard','Répétition espacée arrivée à échéance',c.course_id,c.chapter_id))
  active=self.repo.active_session(a)
  if active: out.append(StudyRecommendation('resume',120,'Continuer la session','Une session est déjà ouverte',active.course_id,active.chapter_id))
  return tuple(sorted(out,key=lambda x:-x.priority))

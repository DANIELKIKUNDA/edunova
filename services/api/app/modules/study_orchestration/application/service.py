from __future__ import annotations
from dataclasses import replace
from datetime import datetime,time,timedelta,UTC
from uuid import uuid4
from zoneinfo import ZoneInfo
from app.modules.study_orchestration.domain.model import *

class StudyPlannerService:
 def __init__(self,repo,adaptive,learning,now,audit=None):self.repo=repo;self.adaptive=adaptive;self.learning=learning;self.now=now;self.audit=audit
 def preferences(self,a):return self.repo.preferences(a)
 def update_preferences(self,a,**kw):
  old=self.repo.preferences(a); rv=kw.pop('row_version',old.row_version)
  if rv!=old.row_version:raise ValueError('planner_version_conflict')
  x=replace(old,**kw,row_version=old.row_version+1)
  if not 30<=x.daily_limit_minutes<=480 or not 10<=x.session_max_minutes<=120 or not 0<=x.preferred_start_hour<24 or not 1<=x.preferred_end_hour<=24 or x.preferred_start_hour>=x.preferred_end_hour:raise ValueError('invalid_planner_preferences')
  self.repo.save_preferences(x);return x
 def add_busy(self,a,starts_at,ends_at,label,source='manual'):
  if ends_at<=starts_at:raise ValueError('invalid_busy_block')
  x=BusyBlock(uuid4().hex,a,starts_at,ends_at,label[:180],source);self.repo.save_busy(x);return x
 def _slots(self,p,d,busy):
  tz=ZoneInfo(p.timezone); start=datetime.combine(d,time(p.preferred_start_hour),tz); end=datetime.combine(d,time(p.preferred_end_hour%24),tz)
  if p.preferred_end_hour==24:end=datetime.combine(d+timedelta(days=1),time(0),tz)
  blocks=sorted([(max(start,b.starts_at.astimezone(tz)),min(end,b.ends_at.astimezone(tz))) for b in busy if b.ends_at.astimezone(tz)>start and b.starts_at.astimezone(tz)<end])
  slots=[];cur=start
  for bs,be in blocks:
   if bs>cur:slots.append((cur,bs))
   cur=max(cur,be)
  if cur<end:slots.append((cur,end))
  return slots
 def generate_day(self,a,d,force=False):
  p=self.repo.preferences(a); now=self.now(); tz=ZoneInfo(p.timezone)
  if d.weekday()>=5 and not p.weekend_enabled:return DailyPlan(d,(),0,0,0,('Week-end désactivé dans vos préférences.',),now)
  day0=datetime.combine(d,time(0),tz); day1=day0+timedelta(days=1); busy=self.repo.busy_blocks(a,day0,day1); slots=self._slots(p,d,busy)
  raw_capacity=sum(int((b-a0).total_seconds()//60) for a0,b in slots); capacity=max(0,min(p.daily_limit_minutes,raw_capacity))
  profile=self.adaptive.profile(a); candidates=[]
  for dec in profile.decisions:
   source=PlanSource.EXAM if dec.action=='exam_focus' else PlanSource.ERROR if dec.action=='error_repair' else PlanSource.REVIEW if dec.action=='spaced_review' else PlanSource.ADAPTIVE
   candidates.append((dec.priority,dec.minutes,dec.course_id,dec.chapter_id,dec.action,dec.reason,dec.expected_outcome,source))
  candidates.sort(key=lambda x:(-x[0],x[2],x[4]))
  items=[];used=0;slot_i=0;cursor=slots[0][0] if slots else day0;overflow=0
  for pri,mins,course,ch,action,reason,outcome,source in candidates:
   requested=max(10,min(mins,p.session_max_minutes)); remaining=requested
   if used>=capacity:overflow+=requested;continue
   requested=min(requested,capacity-used);remaining=requested
   while remaining and slot_i<len(slots):
    ss,se=slots[slot_i];cursor=max(cursor,ss); available=int((se-cursor).total_seconds()//60)
    if available<10:slot_i+=1;cursor=slots[slot_i][0] if slot_i<len(slots) else cursor;continue
    take=min(remaining,available,p.session_max_minutes); end=cursor+timedelta(minutes=take)
    label={'resume':'Reprendre votre session','error_repair':'Corriger les erreurs','spaced_review':'Révision espacée','exam_focus':'Préparation examen','assess':'S’évaluer','practice':'Pratiquer'}.get(action,'Étudier')
    items.append(StudyPlanItem(uuid4().hex,a,d,cursor,end,course,ch,action,label,source,pri,reason,outcome));used+=take;remaining-=take;cursor=end+timedelta(minutes=p.buffer_minutes)
    if cursor>=se:slot_i+=1;cursor=slots[slot_i][0] if slot_i<len(slots) else cursor
   if remaining:overflow+=remaining
  self.repo.replace_planned_day(a,d,items)
  expl=[f'{used} min planifiées sur {capacity} min disponibles.',f'{len(busy)} indisponibilité(s) respectée(s).','Priorités: examen, erreurs, répétition espacée, évaluation et pratique.']
  if overflow:expl.append(f'{overflow} min non planifiées: EduNova protège votre limite quotidienne au lieu de surcharger la journée.')
  return DailyPlan(d,tuple(items),used,capacity,overflow,tuple(expl),now)
 def day(self,a,d):
  p=self.repo.preferences(a);items=self.repo.items_for_day(a,d);return {'date':d,'items':items,'planned_minutes':sum(x.minutes for x in items if x.state==PlanItemState.PLANNED),'daily_limit_minutes':p.daily_limit_minutes}
 def transition(self,a,id,state,row_version):
  x=self.repo.item(a,id)
  if not x:raise ValueError('plan_item_not_found')
  if x.row_version!=row_version:raise ValueError('planner_version_conflict')
  if x.state!=PlanItemState.PLANNED:raise ValueError('plan_item_not_planned')
  y=replace(x,state=PlanItemState(state),row_version=x.row_version+1);self.repo.save_item(y);return y
 def replan_from_today(self,a,days=7):
  now=self.now();p=self.repo.preferences(a);local=now.astimezone(ZoneInfo(p.timezone)).date();return tuple(self.generate_day(a,local+timedelta(days=i),True) for i in range(max(1,min(days,14))))

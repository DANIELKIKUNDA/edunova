from datetime import UTC,date,datetime,timedelta
from app.modules.study_orchestration.application.service import StudyPlannerService
from app.modules.study_orchestration.domain.model import *
from app.modules.adaptive_learning.domain.model import AdaptiveDecision,IntelligenceProfile,RiskBand,ConfidenceBand
N=datetime(2026,9,24,10,tzinfo=UTC)
class A:
 def profile(self,a):return IntelligenceProfile(60,55,70,RiskBand.WATCH,5,(AdaptiveDecision('error_repair',110,'anat','osteo','2 erreurs',('errors=2',),20,.9,'now','Réduire les erreurs'),AdaptiveDecision('spaced_review',95,'phys','mem','12 cartes',('due=12',),12,.9,'today','Rétention'),AdaptiveDecision('exam_focus',105,'chim',None,'Examen proche',('days=5',),40,.8,'today','Préparer examen')),ConfidenceBand.MEDIUM)
class R:
 def __init__(self):self.p={};self.busy=[];self.items={}
 def preferences(self,a):return self.p.get(a,PlannerPreferences(a,daily_limit_minutes=60,preferred_start_hour=18,preferred_end_hour=21))
 def save_preferences(self,x):self.p[x.account_id]=x
 def busy_blocks(self,a,s,e):return tuple(x for x in self.busy if x.account_id==a and x.ends_at>s and x.starts_at<e)
 def save_busy(self,x):self.busy.append(x)
 def replace_planned_day(self,a,d,items):self.items[(a,d)]=list(items)
 def items_for_day(self,a,d):return tuple(self.items.get((a,d),()))
 def item(self,a,id):return next((x for xs in self.items.values() for x in xs if x.id==id and x.account_id==a),None)
 def save_item(self,x):
  for k,xs in self.items.items():
   for i,v in enumerate(xs):
    if v.id==x.id:xs[i]=x
class L:pass
def svc(r=None):return StudyPlannerService(r or R(),A(),L(),lambda:N)
def test_capacity_priority_and_overflow():
 s=svc();x=s.generate_day('u',date(2026,9,24));assert x.planned_minutes<=60;assert x.items[0].action=='error_repair';assert x.overflow_minutes>0
 assert all(i.ends_at>i.starts_at for i in x.items)
def test_busy_block_is_respected():
 r=R();s=svc(r);s.add_busy('u',datetime(2026,9,24,18,tzinfo=UTC),datetime(2026,9,24,19,tzinfo=UTC),'Cours')
 x=s.generate_day('u',date(2026,9,24));assert all(not(i.starts_at<datetime(2026,9,24,19,tzinfo=UTC) and i.ends_at>datetime(2026,9,24,18,tzinfo=UTC)) for i in x.items)
def test_optimistic_transition():
 r=R();s=svc(r);x=s.generate_day('u',date(2026,9,24));i=x.items[0];y=s.transition('u',i.id,'done',1);assert y.state==PlanItemState.DONE and y.row_version==2
 try:s.transition('u',i.id,'skipped',1);assert False
 except ValueError:pass
def test_preferences_guardrails():
 s=svc();p=s.update_preferences('u',daily_limit_minutes=90,row_version=1);assert p.daily_limit_minutes==90 and p.row_version==2
 try:s.update_preferences('u',daily_limit_minutes=600,row_version=2);assert False
 except ValueError:pass
def test_weekend_can_be_disabled():
 r=R();r.p['u']=PlannerPreferences('u',weekend_enabled=False);x=svc(r).generate_day('u',date(2026,9,26));assert not x.items and x.capacity_minutes==0

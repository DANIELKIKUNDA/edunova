from collections import Counter,defaultdict
from datetime import UTC
from app.modules.adaptive_learning.domain.model import *
STAGE={'not_started':0,'viewed':20,'studied':45,'practiced':65,'assessed':82,'mastered':100}

class AdaptiveLearningService:
 def __init__(self,learning,repo,now):self.learning=learning;self.repo=repo;self.now=now
 def profile(self,a):
  now=self.now(); ps=self.learning.all_progress(a); es=self.learning.unresolved_errors(a,500); cs=self.learning.all_review_cards(a,500)
  ec=Counter((x.course_id,x.chapter_id) for x in es); dc=Counter((x.course_id,x.chapter_id) for x in cs if x.due_at<=now)
  assessed=sum(x.assessment_attempts>0 for x in ps); confidence_evidence=len(ps)+assessed+len(es)+sum(x.repetitions>0 for x in cs); evidence=len(ps)
  weighted=[]
  for x in ps:
   assessment_quality=(x.accuracy*35 if x.total_answers else 0); assessment_weight=35 if x.total_answers else 0
   base=STAGE[x.stage.value]*.45+x.completion_ratio*20+assessment_quality
   denom=.45*100+20+assessment_weight
   weighted.append(min(100,base/(denom or 1)*100))
  mastery=sum(weighted)/len(weighted) if weighted else 0
  sessions=self.learning.recent_sessions(a,60); completed=[x for x in sessions if x.state.value=='completed']
  active_days=len({x.updated_at.date() for x in completed}); consistency=min(100,active_days*12+min(28,len(completed)*3))
  readiness=max(0,min(100,mastery*.72+consistency*.28-min(30,len(es)*4)-min(20,sum(dc.values())*2)))
  ds=[]; active=self.learning.active_session(a)
  if active:ds.append(AdaptiveDecision('resume',120,active.course_id,active.chapter_id,'Une session interrompue peut être reprise exactement où elle s’est arrêtée.',('session_open',),15,.99,'now','Préserver la continuité d’apprentissage'))
  gaps=[]
  for x in ps:
   key=(x.course_id,x.chapter_id); sev=0; ev=[]
   if ec[key]:sev+=min(45,ec[key]*15);ev.append(f'errors={ec[key]}')
   if x.total_answers and x.accuracy<.7:sev+=round((.7-x.accuracy)*50);ev.append(f'accuracy={x.accuracy:.2f}')
   if x.practice_attempts==0:sev+=15;ev.append('practice=0')
   if x.assessment_attempts==0:sev+=20;ev.append('assessment=0')
   if sev>=20:gaps.append(KnowledgeGap(x.course_id,x.chapter_id,min(100,sev),'Lacune à consolider',tuple(ev),'error_repair' if ec[key] else 'practice'))
   if ec[key]:ds.append(AdaptiveDecision('error_repair',110,*key,f'{ec[key]} erreur(s) non résolue(s) fragilisent ce chapitre.',(f'errors={ec[key]}',f'accuracy={x.accuracy:.2f}'),20,.95,'now','Réduire les erreurs récurrentes','error_due'))
   elif dc[key]:ds.append(AdaptiveDecision('spaced_review',95,*key,f'{dc[key]} flashcard(s) sont arrivées à échéance.',(f'due={dc[key]}',),12,.96,'today','Renforcer la rétention à long terme','spaced_repetition_due'))
   elif x.assessment_attempts==0 and x.stage.value in {'studied','practiced'}:ds.append(AdaptiveDecision('assess',80,*key,'Ce chapitre a été étudié mais pas encore évalué.',(f'stage={x.stage.value}',),15,.86,'soon','Mesurer les acquis'))
   elif x.practice_attempts==0 and x.stage.value in {'viewed','studied'}:ds.append(AdaptiveDecision('practice',70,*key,'La consultation seule ne prouve pas la maîtrise.',(f'stage={x.stage.value}',),20,.84,'soon','Transformer la lecture en pratique active'))
  exams=[]
  try: plans=self.learning.exam_plans(a)
  except AttributeError: plans=()
  bycourse=defaultdict(list)
  for x,w in zip(ps,weighted):bycourse[x.course_id].append(w)
  for p in plans:
   if p.state.value!='active' or p.exam_at<=now:continue
   days=max(1,(p.exam_at-now).days); scores=[sum(bycourse[c])/len(bycourse[c]) for c in p.course_ids if bycourse[c]]; er=sum(scores)/len(scores) if scores else 0
   risks=tuple(c for c in p.course_ids if not bycourse[c] or sum(bycourse[c])/len(bycourse[c])<65)
   exams.append(ExamReadiness(p.id,p.title,p.exam_at.isoformat(),days,round(er,1),p.daily_minutes,risks))
   if risks: ds.append(AdaptiveDecision('exam_focus',105,risks[0],None,f'{len(risks)} matière(s) nécessitent une consolidation avant « {p.title} ».',(f'days_remaining={days}',f'at_risk_courses={len(risks)}'),min(45,p.daily_minutes),.9 if scores else .65,'today','Améliorer la préparation à l’examen','exam_plan'))
  conf=confidence_for(confidence_evidence,assessed); out=IntelligenceProfile(round(mastery,1),round(readiness,1),round(consistency,1),risk_for(readiness,evidence),evidence,tuple(sorted(ds,key=lambda x:-x.priority)[:12]),conf,tuple(sorted(gaps,key=lambda x:-x.severity)[:12]),tuple(exams))
  self.repo.save(a,out,now); return out
 def history(self,a,limit=30):return self.repo.history(a,limit)

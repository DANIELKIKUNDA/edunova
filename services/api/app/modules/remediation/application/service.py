from __future__ import annotations
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4
from app.modules.remediation.domain.model import *

class RemediationService:
 def __init__(self,repo,learning,adaptive,now,audit=None): self.repo=repo;self.learning=learning;self.adaptive=adaptive;self.now=now;self.audit=audit
 def _emit(self,a,kind,path=None,mis=None,payload=None,mutation_id=None):
  if hasattr(self.repo,'save_event'):
   self.repo.save_event(RemediationEvent(uuid4().hex,a,path,mis,kind,self.now(),payload or {},mutation_id))
 def _root_cause(self,p,errors,accuracy):
  if p.total_answers<3:return RootCause.INSUFFICIENT_EVIDENCE
  if len(errors)>=3 and accuracy is not None and accuracy<65:return RootCause.MISCONCEPTION
  if p.practice_attempts==0:return RootCause.RETRIEVAL
  if accuracy is not None and accuracy<55:return RootCause.PROCEDURAL
  if p.assessment_attempts and accuracy is not None and accuracy<70:return RootCause.TRANSFER
  return RootCause.KNOWLEDGE_GAP
 def diagnose(self,a):
  now=self.now();progress=self.learning.all_progress(a);errors=self.learning.unresolved_errors(a,500);out=[]
  for p in progress:
   es=[e for e in errors if e.course_id==p.course_id and e.chapter_id==p.chapter_id];accuracy=round(p.accuracy*100) if p.total_answers else None
   severity=min(100,(len(es)*18)+(max(0,70-(accuracy or 70)))+(20 if p.assessment_attempts==0 else 0))
   if severity<20:continue
   bloom='apply' if p.practice_attempts==0 else 'analyze' if accuracy is not None and accuracy<60 else 'understand'
   ev=tuple(([f'errors={len(es)}'] if es else [])+([f'accuracy={accuracy}'] if accuracy is not None else [])+[f'assessments={p.assessment_attempts}',f'practice={p.practice_attempts}'])
   confidence=min(95,35+min(30,p.total_answers*3)+min(20,len(es)*5)+(10 if p.assessment_attempts else 0));concept=p.chapter_id or '__course__';cause=self._root_cause(p,es,accuracy)
   label='Hypothèse de misconception persistante' if cause==RootCause.MISCONCEPTION else 'Acquis à consolider';hyp=f'{cause.value}: {len(es)} erreur(s), précision {accuracy if accuracy is not None else "inconnue"}%.'
   old=self.repo.find_open(a,p.course_id,p.chapter_id,concept)
   x=replace(old,label=label,evidence=ev,bloom_gap=bloom,severity=severity,confidence=confidence,root_cause=cause,hypothesis=hyp,updated_at=now,row_version=old.row_version+1) if old else Misconception(uuid4().hex,a,p.course_id,p.chapter_id,concept,label,ev,bloom,severity,confidence,MisconceptionState.OPEN,now,now,root_cause=cause,hypothesis=hyp)
   self.repo.save_misconception(x);out.append(x)
  for x in out:self._emit(a,RemediationEventType.DIAGNOSED,mis=x.id,payload={'severity':x.severity,'confidence':x.confidence,'root_cause':x.root_cause.value})
  return tuple(sorted(out,key=lambda x:(-x.severity,-x.confidence)))
 def tutor_decision(self,a,misconception_id):
  m=self.repo.misconception(a,misconception_id)
  if not m:raise ValueError('misconception_not_found')
  mapping={RootCause.MISCONCEPTION:TutorIntervention.CONTRAST_CASES,RootCause.PROCEDURAL:TutorIntervention.WORKED_EXAMPLE,RootCause.TRANSFER:TutorIntervention.TRANSFER,RootCause.RETRIEVAL:TutorIntervention.RETRIEVAL,RootCause.KNOWLEDGE_GAP:TutorIntervention.CONCEPT_REBUILD,RootCause.CARELESSNESS:TutorIntervention.REFLECTION,RootCause.INSUFFICIENT_EVIDENCE:TutorIntervention.RETRIEVAL}
  level=1 if m.confidence<55 else 2 if m.severity<70 else 3;intervention=mapping[m.root_cause];r=(f'cause={m.root_cause.value}',f'severity={m.severity}',f'confidence={m.confidence}',f'bloom_gap={m.bloom_gap}')
  # Prefer a previously successful strategy for this learner/cause when enough longitudinal evidence exists.
  if hasattr(self.repo,'events'):
   hist=self.repo.events(a,200);scores={}
   for e in hist:
    if e.kind==RemediationEventType.PRACTICE_RECORDED and e.payload.get('root_cause')==m.root_cause.value:
     iv=e.payload.get('intervention'); ok=e.payload.get('success',False); scores.setdefault(iv,[0,0]);scores[iv][0]+=1;scores[iv][1]+=1 if ok else 0
   proven=[(ok/n,iv,n) for iv,(n,ok) in scores.items() if n>=3]
   if proven:
    rate,iv,n=max(proven)
    if rate>=.67: intervention=TutorIntervention(iv);r=r+(f'personal_history={n}',f'personal_success_rate={rate:.2f}')
  return TutorDecision(intervention,level,m.bloom_gap,r,3 if level==1 else 2,True)
 def create_path(self,a,misconception_id):
  m=self.repo.misconception(a,misconception_id)
  if not m:raise ValueError('misconception_not_found')
  existing=self.repo.active_path(a,misconception_id)
  if existing:return existing
  d=self.tutor_decision(a,m.id);src='Utiliser exclusivement le contenu validé et sa provenance.'
  steps=(RemediationStep(1,RemediationStepType.DIAGNOSE,'Comprendre mon raisonnement','Faire expliciter la démarche avant de corriger; distinguer erreur stable, oubli et manque de preuve.',5,m.bloom_gap,'L’étudiant peut expliquer où son raisonnement diverge.',TutorIntervention.REFLECTION),RemediationStep(2,RemediationStepType.EXPLAIN,'Reconstruire le modèle mental',f'Micro-leçon ciblée. {src}',8,'understand','Reformuler et prédire une conséquence.',d.intervention),RemediationStep(3,RemediationStepType.WORKED_EXAMPLE,'Comparer des raisonnements','Exemple expert + contre-exemple plausible; masquer progressivement les étapes.',8,'apply','Justifier chaque décision avant révélation.',TutorIntervention.FADING),RemediationStep(4,RemediationStepType.PRACTICE,'Pratique adaptative','Nouvel item; indices progressifs, jamais la réponse finale avant engagement.',10,'apply','≥70 % avec au plus un indice.',d.intervention),RemediationStep(5,RemediationStepType.TRANSFER,'Prouver le transfert','Contexte superficiellement différent, même principe profond; aucun item initial recopié.',10,'analyze','≥75 % sur situation nouvelle.',TutorIntervention.TRANSFER),RemediationStep(6,RemediationStepType.REASSESS,'Vérification indépendante','Items indépendants et sourcés; mesure sans aide.',8,m.bloom_gap,'≥75 % et gain suffisant.',TutorIntervention.RETRIEVAL))
  baseline=self._baseline(a,m.course_id,m.chapter_id);now=self.now();x=RemediationPath(uuid4().hex,a,m.id,m.course_id,m.chapter_id,steps,0,'active',baseline,None,now,now,difficulty_level=d.difficulty_level);self.repo.save_path(x);self._emit(a,RemediationEventType.PATH_CREATED,path=x.id,mis=m.id,payload={'baseline':baseline,'intervention':d.intervention.value});return x
 def _baseline(self,a,c,ch):
  p=self.learning.progress(a,c,ch);return round(p.accuracy*100) if p and p.total_answers else None
 def advance(self,a,path_id,expected_version):
  x=self.repo.path(a,path_id)
  if not x:raise ValueError('remediation_path_not_found')
  if x.row_version!=expected_version:raise ValueError('remediation_version_conflict')
  if x.status!='active':raise ValueError('remediation_path_closed')
  y=replace(x,current_step=min(len(x.steps)-1,x.current_step+1),updated_at=self.now(),row_version=x.row_version+1);self.repo.save_path(y);return y
 def record_practice(self,a,path_id,score,used_hints,expected_version,transfer=False,mutation_id=None):
  if not 0<=score<=100 or used_hints<0:raise ValueError('invalid_practice_result')
  x=self.repo.path(a,path_id)
  if not x:raise ValueError('remediation_path_not_found')
  if mutation_id and x.last_mutation_id==mutation_id:return x
  if x.row_version!=expected_version:raise ValueError('remediation_version_conflict')
  success=score>=75 and used_hints<=1;succ=x.consecutive_successes+1 if success else 0;fail=0 if success else x.consecutive_failures+1;level=x.difficulty_level
  if succ>=2:level=min(5,level+1)
  elif fail>=2:level=max(1,level-1)
  y=replace(x,difficulty_level=level,consecutive_successes=succ,consecutive_failures=fail,last_transfer_score=score if transfer else x.last_transfer_score,last_mutation_id=mutation_id,total_practice_attempts=x.total_practice_attempts+1,successful_practice_attempts=x.successful_practice_attempts+(1 if success else 0),updated_at=self.now(),row_version=x.row_version+1);self.repo.save_path(y);m=self.repo.misconception(a,x.misconception_id);d=self.tutor_decision(a,m.id) if m else None;self._emit(a,RemediationEventType.PRACTICE_RECORDED,path=x.id,mis=x.misconception_id,mutation_id=mutation_id,payload={'score':score,'success':success,'transfer':transfer,'hints':used_hints,'root_cause':m.root_cause.value if m else None,'intervention':d.intervention.value if d else None});return y
 def verify(self,a,path_id,score,expected_version):
  if not 0<=score<=100:raise ValueError('invalid_verification_score')
  x=self.repo.path(a,path_id)
  if not x or x.row_version!=expected_version:raise ValueError('remediation_version_conflict')
  base=x.baseline_score if x.baseline_score is not None else score;gain=score-base;transfer_ok=x.last_transfer_score is not None and x.last_transfer_score>=75;resolved=score>=75 and transfer_ok and (x.baseline_score is None or gain>=10 or base>=75);status='completed' if resolved else 'active';review=self.now()+timedelta(days=7) if resolved else None
  y=replace(x,verification_score=score,status=status,next_review_at=review,cumulative_gain=x.cumulative_gain+gain,updated_at=self.now(),row_version=x.row_version+1);self.repo.save_path(y);m=self.repo.misconception(a,x.misconception_id)
  if m:self.repo.save_misconception(replace(m,state=MisconceptionState.RESOLVED if resolved else MisconceptionState.IMPROVING,updated_at=self.now(),row_version=m.row_version+1))
  self._emit(a,RemediationEventType.VERIFIED,path=x.id,mis=x.misconception_id,payload={'baseline':base,'score':score,'gain':gain,'resolved':resolved,'transfer_verified':transfer_ok})
  return VerificationResult(x.id,base,score,gain,resolved,'spaced_review' if resolved else 'targeted_practice',transfer_ok,resolved)
 def retention_check(self,a,path_id,score,expected_version):
  x=self.repo.path(a,path_id)
  if not x or x.row_version!=expected_version:raise ValueError('remediation_version_conflict')
  if x.status!='completed':raise ValueError('retention_not_due')
  relapse=score<70;m=self.repo.misconception(a,x.misconception_id)
  if relapse and m:self.repo.save_misconception(replace(m,state=MisconceptionState.RELAPSED,relapse_count=m.relapse_count+1,updated_at=self.now(),row_version=m.row_version+1))
  self._emit(a,RemediationEventType.RELAPSED if relapse else RemediationEventType.RETENTION_CHECKED,path=x.id,mis=x.misconception_id,payload={'score':score,'retained':not relapse})
  y=replace(x,status='active' if relapse else 'retained',next_review_at=self.now()+timedelta(days=21) if not relapse else None,updated_at=self.now(),row_version=x.row_version+1);self.repo.save_path(y);return {'retained':not relapse,'next_action':'reopen_remediation' if relapse else 'spaced_review_21d'}
 def dashboard(self,a):
  items=self.repo.open_misconceptions(a,50);paths=self.repo.active_paths(a,20);events=self.repo.events(a,500) if hasattr(self.repo,'events') else ()
  verified=[e for e in events if e.kind==RemediationEventType.VERIFIED];gains=[e.payload.get('gain',0) for e in verified]
  return {'open_misconceptions':len(items),'high_severity':sum(x.severity>=60 for x in items),'active_paths':len(paths),'relapses':sum(x.state==MisconceptionState.RELAPSED for x in items),'priority':items[:5],'paths':paths,'longitudinal':{'verified_cycles':len(verified),'average_gain':round(sum(gains)/len(gains),1) if gains else None,'retention_checks':sum(e.kind==RemediationEventType.RETENTION_CHECKED for e in events),'relapse_events':sum(e.kind==RemediationEventType.RELAPSED for e in events)}}

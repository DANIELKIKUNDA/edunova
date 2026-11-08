from __future__ import annotations
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
from math import floor
import re
import unicodedata
import xml.etree.ElementTree as ET
from uuid import uuid4
from app.modules.assessment.domain.model import *
class AssessmentService:
 def __init__(self,repo,now,audit=None):self.repo=repo;self.now=now;self.audit=audit
 def evaluate_question_quality(self,kind,prompt,choices,correct,explanation,pages,bloom_level,learning_objective,cognitive_steps=(),distractor_rationales=(),clinical_vignette=False):
  kind=QuestionType(kind); bloom=BloomLevel(bloom_level); blocking=[]; warnings=[]; strengths=[]; score=100
  text=prompt.strip()
  if len(text)<20:blocking.append('stem_too_short');score-=25
  if not learning_objective.strip():blocking.append('learning_objective_missing');score-=20
  if not pages:blocking.append('source_pages_missing');score-=15
  if len(explanation.strip())<20:warnings.append('explanation_too_shallow');score-=10
  higher=bloom in {BloomLevel.APPLY,BloomLevel.ANALYZE,BloomLevel.EVALUATE,BloomLevel.CREATE}
  if higher and len(cognitive_steps)<2:warnings.append('higher_order_reasoning_steps_missing');score-=15
  if bloom==BloomLevel.CREATE and kind not in {QuestionType.SHORT,QuestionType.EXERCISE}:blocking.append('create_level_requires_constructed_response');score-=30
  if higher and len(text)<80:warnings.append('higher_order_stem_lacks_context');score-=10
  if clinical_vignette and len(text)<120:warnings.append('clinical_vignette_too_thin');score-=10
  if kind in {QuestionType.SINGLE,QuestionType.MULTIPLE}:
   if len(choices)<3:warnings.append('too_few_options');score-=10
   if len(set(x.strip().casefold() for x in choices))!=len(choices):blocking.append('duplicate_options');score-=20
   if higher and not distractor_rationales:warnings.append('higher_order_distractor_rationales_missing');score-=10
   if distractor_rationales and len(distractor_rationales)!=len(choices):warnings.append('distractor_rationale_coverage');score-=5
   if any(x.strip().casefold() in {'toutes les réponses','aucune réponse','all of the above','none of the above'} for x in choices):warnings.append('meta_option_discouraged');score-=5
  low=text.casefold()
  if any(x in low for x in ('toujours','jamais','évidemment')):warnings.append('absolute_cue_language');score-=5
  if higher:strengths.append('higher_order_cognition')
  if clinical_vignette:strengths.append('authentic_context')
  if len(explanation.strip())>=80:strengths.append('substantive_feedback')
  if pages:strengths.append('source_grounded')
  return QuestionQualityReport(max(0,min(100,score)),bloom.value,higher,tuple(blocking),tuple(warnings),tuple(strengths))
 def _fingerprint(self,text):
  x=unicodedata.normalize('NFKD',text.casefold());x=''.join(c for c in x if not unicodedata.combining(c));x=re.sub(r'[^a-z0-9]+',' ',x);return sha256(' '.join(x.split()).encode()).hexdigest()
 def infer_bloom(self,prompt):
  t=prompt.casefold()
  rules=((BloomLevel.CREATE,('concevoir','élaborer','construire','proposer un plan','design','create')),(BloomLevel.EVALUATE,('évaluer','justifier','critiquer','défendre','evaluate','justify')),(BloomLevel.ANALYZE,('analyser','comparer','différencier','interpréter','analyze','compare')),(BloomLevel.APPLY,('appliquer','calculer','résoudre','déterminer','prédire','apply','calculate')),(BloomLevel.UNDERSTAND,('expliquer','résumer','classer','illustrer','explain','summarize')))
  for level,verbs in rules:
   if any(v in t for v in verbs):return level,85
  return BloomLevel.REMEMBER,55
 def variant_specification(self,question_id,target_bloom=None,target_difficulty=None):
  q=self.repo.question(question_id)
  if not q:raise ValueError('question_not_found')
  bloom=BloomLevel(target_bloom) if target_bloom else q.bloom_level
  difficulty=max(1,min(5,int(target_difficulty or q.difficulty)))
  return VariantSpecification(q.id,bloom.value,difficulty,q.learning_objective,('scenario','surface_values','option_order'),('learning_objective','source_grounding','cognitive_demand','correct_principle'),('verbatim_copy','answer_leakage','unsupported_fact','difficulty_reduction'))
 def _save_origin(self,q,source_document_id,source_format,external_id,original_text,bloom,confidence):
  fp=self._fingerprint(original_text);dup=False
  if hasattr(self.repo,'origin_by_fingerprint'):dup=self.repo.origin_by_fingerprint(fp) is not None
  if dup:return None,True
  o=QuestionOrigin(uuid4().hex,q.id,source_document_id,ImportFormat(source_format),external_id,original_text,sha256(original_text.encode()).hexdigest(),fp,bloom,confidence,ReviewStatus.NEEDS_REVIEW)
  if hasattr(self.repo,'save_origin'):self.repo.save_origin(o)
  return o,False
 def import_gift(self,bank_id,course_id,source_document_id,text,chapter_id=None):
  ids=[];dups=reject=0;warnings=[]
  # Industrial subset: title optional, single/multiple choice and true/false. Unsupported blocks fail visibly.
  blocks=[b.strip() for b in re.split(r'\n\s*\n',text) if b.strip() and not b.lstrip().startswith('//')]
  for block in blocks:
   try:
    title=None;m=re.match(r'::([^:]+)::(.*)',block,re.S)
    if m:title,block=m.group(1).strip(),m.group(2).strip()
    mm=re.match(r'(.+?)\s*\{(.*)\}\s*$',block,re.S)
    if not mm:reject+=1;warnings.append('unsupported_gift_block');continue
    prompt,ans=mm.group(1).strip(),mm.group(2).strip();choices=[];correct=[]
    if ans.upper() in ('T','TRUE','F','FALSE'):
     kind=QuestionType.TRUE_FALSE;choices=['Vrai','Faux'];correct=['Vrai' if ans.upper() in ('T','TRUE') else 'Faux']
    else:
     tokens=re.findall(r'([~=])([^~=]+)',ans);choices=[v.strip() for _,v in tokens];correct=[v.strip() for sig,v in tokens if sig=='='];kind=QuestionType.MULTIPLE if len(correct)>1 else QuestionType.SINGLE
    if not correct:raise ValueError('gift_answer_missing')
    bloom,conf=self.infer_bloom(prompt);q=self.create_question(bank_id,course_id,chapter_id,kind,prompt,choices,correct,'Importé depuis questionnaire historique — explication à enrichir avant approbation.',(),block,False,1,max(1,min(5,1+list(BloomLevel).index(bloom)//2)),bloom,f'Évaluer: {prompt[:120]}',(),(),False)
    origin,dup=self._save_origin(q,source_document_id,ImportFormat.GIFT,title,block,bloom,conf)
    if dup:
     dups+=1
     # imported duplicate must not pollute the usable bank
     if hasattr(self.repo,'delete_question'):self.repo.delete_question(q.id)
    else:ids.append(q.id)
   except Exception as e:reject+=1;warnings.append(f'gift_rejected:{type(e).__name__}')
  return QuestionImportReport(source_document_id,'gift',len(ids),dups,reject,tuple(ids),tuple(warnings))
 def import_moodle_xml(self,bank_id,course_id,source_document_id,text,chapter_id=None):
  ids=[];dups=reject=0;warnings=[]
  try:root=ET.fromstring(text)
  except ET.ParseError:raise ValueError('invalid_moodle_xml')
  for node in root.findall('.//question'):
   typ=node.get('type','');
   if typ=='category':continue
   try:
    prompt=''.join(node.findtext('questiontext/text','')).strip();name=node.findtext('name/text')
    answers=node.findall('answer');choices=[];correct=[]
    for a in answers:
     value=(a.findtext('text') or '').strip();choices.append(value)
     if float(a.get('fraction','0'))>0:correct.append(value)
    if typ=='truefalse':kind=QuestionType.TRUE_FALSE
    elif typ=='multichoice':kind=QuestionType.MULTIPLE if len(correct)>1 else QuestionType.SINGLE
    elif typ in ('shortanswer','essay'):kind=QuestionType.SHORT if typ=='shortanswer' else QuestionType.EXERCISE
    else:reject+=1;warnings.append(f'unsupported_moodle_type:{typ}');continue
    if kind in {QuestionType.SHORT,QuestionType.EXERCISE} and not correct:correct=['manual_review_required']
    bloom,conf=self.infer_bloom(prompt);original=ET.tostring(node,encoding='unicode')
    q=self.create_question(bank_id,course_id,chapter_id,kind,prompt,choices,correct,'Importé depuis Moodle XML — correction éditoriale requise.',(),original,False,1,2,bloom,f'Évaluer: {prompt[:120]}')
    origin,dup=self._save_origin(q,source_document_id,ImportFormat.MOODLE_XML,name,original,bloom,conf)
    if dup:
     dups+=1
     if hasattr(self.repo,'delete_question'):self.repo.delete_question(q.id)
    else:ids.append(q.id)
   except Exception as e:reject+=1;warnings.append(f'moodle_rejected:{type(e).__name__}')
  return QuestionImportReport(source_document_id,'moodle_xml',len(ids),dups,reject,tuple(ids),tuple(warnings))
 def export_gift(self,question_ids):
  out=[]
  for qid in question_ids:
   q=self.repo.question(qid)
   if not q:continue
   if q.kind==QuestionType.TRUE_FALSE:body='TRUE' if q.correct and q.correct[0].casefold() in ('vrai','true') else 'FALSE'
   elif q.kind in {QuestionType.SINGLE,QuestionType.MULTIPLE}:body=' '.join(('=' if c in q.correct else '~')+c for c in q.choices)
   else:continue
   out.append(f'::{q.id}::{q.prompt} {{{body}}}')
  return '\n\n'.join(out)
 def export_moodle_xml(self,question_ids):
  root=ET.Element('quiz')
  for qid in question_ids:
   q=self.repo.question(qid)
   if not q:continue
   typ='truefalse' if q.kind==QuestionType.TRUE_FALSE else 'multichoice' if q.kind in {QuestionType.SINGLE,QuestionType.MULTIPLE} else 'shortanswer' if q.kind==QuestionType.SHORT else 'essay'
   n=ET.SubElement(root,'question',type=typ);name=ET.SubElement(n,'name');ET.SubElement(name,'text').text=q.id;qt=ET.SubElement(n,'questiontext',format='html');ET.SubElement(qt,'text').text=q.prompt
   for c in q.choices:
    a=ET.SubElement(n,'answer',fraction='100' if c in q.correct else '0');ET.SubElement(a,'text').text=c
  return ET.tostring(root,encoding='unicode')
 def create_question(self,bank_id,course_id,chapter_id,kind,prompt,choices,correct,explanation,pages,source_text,approved=True,points=1,difficulty=2,bloom_level=BloomLevel.UNDERSTAND,learning_objective='',cognitive_steps=(),distractor_rationales=(),clinical_vignette=False):
  if not prompt.strip() or not correct:raise ValueError('invalid_question')
  kind=QuestionType(kind)
  if kind in {QuestionType.SINGLE,QuestionType.MULTIPLE} and len(choices)<2:raise ValueError('choices_required')
  report=self.evaluate_question_quality(kind,prompt,choices,correct,explanation,pages,bloom_level,learning_objective,cognitive_steps,distractor_rationales,clinical_vignette)
  # Legacy/editorial drafts remain ingestible; approval for industrial profiles is enforced by blueprint quality gates.
  q=ExamQuestion(uuid4().hex,bank_id,course_id,chapter_id,kind,prompt.strip(),tuple(choices),tuple(correct),explanation.strip(),tuple(sorted(set(pages))),sha256(source_text.encode()).hexdigest(),difficulty,approved,points,BloomLevel(bloom_level),learning_objective.strip(),tuple(cognitive_steps),tuple(distractor_rationales),report.score,clinical_vignette);self.repo.save_question(q);return q
 def create_blueprint(self,title,course_id,duration_minutes,question_count,pass_percent=60,shuffle=True,bloom_distribution=None,min_quality_score=0):
  if not 5<=duration_minutes<=360 or not 1<=question_count<=200 or not 0<=pass_percent<=100:raise ValueError('invalid_blueprint')
  if not 0<=min_quality_score<=100:raise ValueError('invalid_quality_gate')
  dist=None
  if bloom_distribution:
   dist={BloomLevel(k).value:int(v) for k,v in bloom_distribution.items() if int(v)>0}
   if sum(dist.values())!=100:raise ValueError('bloom_distribution_must_equal_100')
  b=ExamBlueprint(uuid4().hex,title[:180],course_id,duration_minutes,question_count,pass_percent,shuffle,True,1,dist,min_quality_score);self.repo.save_blueprint(b);return b
 def _select_questions(self,b,questions):
  eligible=[q for q in questions if (q.approved or not b.approved_only) and q.quality_score>=b.min_quality_score]
  if not b.bloom_distribution:return sorted(eligible,key=lambda q:(q.difficulty,q.id))[:b.question_count]
  selected=[]; used=set(); levels=list(b.bloom_distribution.items())
  quotas={k:floor(b.question_count*v/100) for k,v in levels}
  remaining=b.question_count-sum(quotas.values())
  for k,_ in sorted(levels,key=lambda kv:kv[1],reverse=True):
   if remaining<=0:break
   quotas[k]+=1;remaining-=1
  for level,n in quotas.items():
   pool=sorted((q for q in eligible if q.bloom_level.value==level),key=lambda q:(-q.quality_score,-q.difficulty,q.id))
   if len(pool)<n:raise ValueError(f'insufficient_bloom_questions:{level}:{n}')
   for q in pool[:n]:selected.append(q);used.add(q.id)
  return selected
 def start(self,account_id,blueprint_id):
  b=self.repo.blueprint(blueprint_id)
  if not b:raise ValueError('blueprint_not_found')
  qs=self._select_questions(b,self.repo.questions_for_course(b.course_id))
  if len(qs)<b.question_count:raise ValueError('insufficient_approved_questions')
  now=self.now();a=ExamAttempt(uuid4().hex,account_id,b.id,tuple(q.id for q in qs),now,now+timedelta(minutes=b.duration_minutes));self.repo.save_attempt(a);return a
 def answer(self,account_id,attempt_id,question_id,values,marked,row_version):
  a=self.repo.attempt(attempt_id)
  if not a or a.account_id!=account_id:raise ValueError('attempt_not_found')
  if a.state!=AttemptState.ACTIVE:raise ValueError('attempt_closed')
  if a.row_version!=row_version:raise ValueError('assessment_version_conflict')
  if question_id not in a.question_ids:raise ValueError('question_not_in_attempt')
  answers={x.question_id:x for x in a.answers};answers[question_id]=AttemptAnswer(question_id,tuple(values),marked)
  x=replace(a,answers=tuple(answers[k] for k in a.question_ids if k in answers),row_version=a.row_version+1);self.repo.save_attempt(x);return x
 def submit(self,account_id,attempt_id,row_version):
  a=self.repo.attempt(attempt_id)
  if not a or a.account_id!=account_id:raise ValueError('attempt_not_found')
  if a.state!=AttemptState.ACTIVE:raise ValueError('attempt_closed')
  if a.row_version!=row_version:raise ValueError('assessment_version_conflict')
  answers={x.question_id:x for x in a.answers};results=[];earned=possible=0;chap={};bloom={}
  b=self.repo.blueprint(a.blueprint_id)
  if not b or not a.question_ids or len(a.question_ids)!=len(set(a.question_ids)):
   raise ValueError('assessment_invalid_grading_source')
  for qid in a.question_ids:
   q=self.repo.question(qid)
   if not q or q.course_id!=b.course_id or type(q.points) is not int or q.points<=0:
    raise ValueError('assessment_invalid_grading_source')
   possible+=q.points;got=set(answers.get(qid,AttemptAnswer(qid,())).values)==set(q.correct);e=q.points if got else 0;earned+=e
   key=q.chapter_id or 'course';chap[key]=chap.get(key,0)+(100 if got else 0);bloom.setdefault(q.bloom_level.value,[]).append(100 if got else 0);results.append(QuestionResult(q.id,e,q.points,got,q.explanation,q.source_pages,q.chapter_id,q.bloom_level.value,q.learning_objective))
  by_bloom={k:round(sum(v)/len(v)) for k,v in bloom.items()};pct=round(100*earned/possible) if possible else 0;res=ExamResult(a.id,earned,possible,pct,pct>=b.pass_percent,chap,tuple(results),by_bloom)
  x=replace(a,state=AttemptState.GRADED,submitted_at=self.now(),row_version=a.row_version+1)
  if hasattr(self.repo,'save_graded_attempt_result'):
   self.repo.save_graded_attempt_result(x,res)
  else:  # non-SQL adapters retain the existing repository protocol
   self.repo.save_attempt(x);self.repo.save_result(res)
  return res
 def resume(self,account_id,attempt_id):
  a=self.repo.attempt(attempt_id)
  if not a or a.account_id!=account_id:raise ValueError('attempt_not_found')
  return a

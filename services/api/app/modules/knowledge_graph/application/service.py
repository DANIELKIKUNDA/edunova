from __future__ import annotations
from dataclasses import replace
from hashlib import sha256
from uuid import uuid4
from app.modules.knowledge_graph.domain.model import *

class KnowledgeGraphService:
 def __init__(self,repo,now):self.repo=repo;self.now=now
 def create_node(self,tenant,kind,label,description='',course_id=None,source_revision_id=None,source_locator=None,provenance_sha256=None,origin=Origin.HUMAN):
  if origin!=Origin.HUMAN and not provenance_sha256: raise ValueError('provenance_required')
  x=KnowledgeNode(uuid4().hex,tenant,NodeKind(kind),label.strip(),description.strip(),course_id,source_revision_id,source_locator,provenance_sha256,GovernanceState.CANDIDATE,Origin(origin),1,self.now(),self.now());self.repo.save_node(x);return x
 def propose_relation(self,tenant,source_id,target_id,kind,rationale,confidence,actor,origin=Origin.HUMAN,source_revision_id=None,provenance_sha256=None):
  if source_id==target_id:raise ValueError('self_relation_forbidden')
  if not self.repo.node(tenant,source_id) or not self.repo.node(tenant,target_id):raise ValueError('node_not_found')
  if Origin(origin)!=Origin.HUMAN and not provenance_sha256:raise ValueError('provenance_required')
  if RelationKind(kind) in {RelationKind.PREREQUISITE_OF,RelationKind.DEPENDS_ON} and self._would_cycle(tenant,source_id,target_id):raise ValueError('dependency_cycle')
  x=KnowledgeRelation(uuid4().hex,tenant,source_id,target_id,RelationKind(kind),rationale.strip(),max(0,min(100,confidence)),GovernanceState.CANDIDATE,Origin(origin),source_revision_id,provenance_sha256,1,actor,None,self.now(),self.now());self.repo.save_relation(x);return x
 def validate_relation(self,tenant,id,reviewer):
  x=self.repo.relation(tenant,id)
  if not x:raise ValueError('relation_not_found')
  if x.origin==Origin.AI_PROPOSAL and reviewer==x.created_by:raise ValueError('independent_review_required')
  y=replace(x,state=GovernanceState.VALIDATED,validated_by=reviewer,version=x.version+1,updated_at=self.now());self.repo.save_relation(y);return y
 def publish_relation(self,tenant,id,actor,high_stakes=False):
  x=self.repo.relation(tenant,id)
  if not x or x.state!=GovernanceState.VALIDATED:raise ValueError('validated_relation_required')
  if high_stakes and (not x.provenance_sha256 or not x.validated_by):raise ValueError('high_stakes_provenance_and_review_required')
  y=replace(x,state=GovernanceState.PUBLISHED,version=x.version+1,updated_at=self.now());self.repo.save_relation(y);return y
 def prerequisites(self,tenant,concept_id,max_depth=5):return self._walk(tenant,concept_id,max_depth,reverse=True)
 def dependents(self,tenant,concept_id,max_depth=5):return self._walk(tenant,concept_id,max_depth,reverse=False)
 def _walk(self,tenant,start,max_depth,reverse):
  rels=[r for r in self.repo.relations(tenant) if r.state==GovernanceState.PUBLISHED and r.kind in {RelationKind.PREREQUISITE_OF,RelationKind.DEPENDS_ON}];q=[(start,(),(),0)];seen={start};out=[]
  while q:
   cur,np,rp,d=q.pop(0)
   if d>=max_depth:continue
   for r in rels:
    nxt=(r.source_id if r.target_id==cur else None) if reverse else (r.target_id if r.source_id==cur else None)
    if nxt and nxt not in seen:seen.add(nxt);path=np+(nxt,);kinds=rp+(r.kind.value,);out.append(LearningDependency(nxt,d+1,path,kinds));q.append((nxt,path,kinds,d+1))
  return tuple(out)
 def root_cause_candidates(self,tenant,concept_id,weak_concepts):
  weak=set(weak_concepts);deps=self.prerequisites(tenant,concept_id,8);rank=[]
  for d in deps:
   if d.concept_id in weak:rank.append({'concept_id':d.concept_id,'distance':d.distance,'score':max(10,100-d.distance*12),'reason':'published_prerequisite_and_observed_weakness'})
  return tuple(sorted(rank,key=lambda x:(-x['score'],x['distance'])))
 def assessment_context(self,tenant,concept_id):
  pre=self.prerequisites(tenant,concept_id,2);deps=self.dependents(tenant,concept_id,1)
  return {'target':concept_id,'prerequisites':[x.concept_id for x in pre],'transfer_targets':[x.concept_id for x in deps],'instruction':'Generate from validated source content; use graph only to select concepts, never as an unsourced answer key.'}
 def learning_sequence(self,tenant,concept_id):
  deps=list(self.prerequisites(tenant,concept_id,8));deps.sort(key=lambda x:-x.distance);return tuple([x.concept_id for x in deps]+[concept_id])
 def start_extraction(self,tenant,source_revision_id,source_sha256,course_id,actor,candidates):
  if len(source_sha256)!=64:raise ValueError('source_sha256_required')
  b=ExtractionBatch(uuid4().hex,tenant,source_revision_id,source_sha256,course_id,ExtractionState.DRAFT,actor,None,len(candidates),self.now(),self.now());self.repo.save_batch(b)
  out=[];seen=set()
  for raw in candidates:
   locator=str(raw.get('source_locator','')).strip();confidence=max(0,min(100,int(raw.get('confidence',0))));ctype=str(raw.get('candidate_type','node'))
   if not locator:raise ValueError('source_locator_required')
   key='|'.join([ctype,str(raw.get('label','')).strip().lower(),str(raw.get('source_label','')).strip().lower(),str(raw.get('target_label','')).strip().lower(),str(raw.get('kind','')).lower(),source_sha256,locator]);fp=sha256(key.encode()).hexdigest()
   if fp in seen:continue
   seen.add(fp);c=ExtractionCandidate(uuid4().hex,b.id,tenant,ctype,str(raw.get('label','')).strip(),raw.get('source_label'),raw.get('target_label'),str(raw.get('kind','concept')),str(raw.get('rationale','')).strip(),locator,confidence,fp,ExtractionState.DRAFT,None,None,self.now(),self.now());self.repo.save_candidate(c);out.append(c)
  return b,tuple(out)
 def submit_extraction_review(self,tenant,batch_id,actor):
  b=self.repo.batch(tenant,batch_id)
  if not b:raise ValueError('batch_not_found')
  y=replace(b,state=ExtractionState.IN_REVIEW,updated_at=self.now());self.repo.save_batch(y);return y
 def accept_candidate(self,tenant,candidate_id,reviewer,high_stakes=False):
  c=self.repo.candidate(tenant,candidate_id);b=self.repo.batch(tenant,c.batch_id) if c else None
  if not c or not b:raise ValueError('candidate_not_found')
  if b.state!=ExtractionState.IN_REVIEW:raise ValueError('batch_review_required')
  if reviewer==b.created_by:raise ValueError('independent_review_required')
  if high_stakes and c.confidence<70:raise ValueError('high_stakes_confidence_too_low')
  if c.candidate_type=='node':
   existing=self._find_node(tenant,c.label,b.course_id);nid=existing.id if existing else self.create_node(tenant,c.kind,c.label,course_id=b.course_id,source_revision_id=b.source_revision_id,source_locator=c.source_locator,provenance_sha256=b.source_sha256,origin=Origin.SOURCE_EXTRACTION).id
   y=replace(c,state=ExtractionState.ACCEPTED,created_node_id=nid,updated_at=self.now())
  elif c.candidate_type=='relation':
   a=self._find_node(tenant,c.source_label or '',b.course_id);z=self._find_node(tenant,c.target_label or '',b.course_id)
   if not a or not z:raise ValueError('relation_nodes_must_exist')
   r=self.propose_relation(tenant,a.id,z.id,c.kind,c.rationale,c.confidence,b.created_by,Origin.SOURCE_EXTRACTION,b.source_revision_id,b.source_sha256)
   y=replace(c,state=ExtractionState.ACCEPTED,created_relation_id=r.id,updated_at=self.now())
  else:raise ValueError('candidate_type_invalid')
  self.repo.save_candidate(y);return y
 def reject_candidate(self,tenant,candidate_id,reviewer):
  c=self.repo.candidate(tenant,candidate_id)
  if not c:raise ValueError('candidate_not_found')
  y=replace(c,state=ExtractionState.REJECTED,updated_at=self.now());self.repo.save_candidate(y);return y
 def graph_health(self,tenant):
  ns=self.repo.nodes(tenant);rs=self.repo.relations(tenant);published=[r for r in rs if r.state==GovernanceState.PUBLISHED];candidates=[r for r in rs if r.state==GovernanceState.CANDIDATE]
  orphan=[n.id for n in ns if n.kind in {NodeKind.CONCEPT,NodeKind.SUBCONCEPT} and not any(r.source_id==n.id or r.target_id==n.id for r in published)]
  return {'nodes':len(ns),'relations':len(rs),'published_relations':len(published),'candidate_relations':len(candidates),'orphan_concepts':orphan,'review_backlog':sum(1 for c in self.repo.all_candidates(tenant) if c.state in {ExtractionState.DRAFT,ExtractionState.IN_REVIEW})}

 def create_snapshot(self,tenant,actor,reason='manual'):
  import json
  nodes=sorted(self.repo.nodes(tenant),key=lambda x:x.id);rels=sorted((r for r in self.repo.relations(tenant) if r.state==GovernanceState.PUBLISHED),key=lambda x:x.id)
  canonical={'nodes':[{'id':n.id,'kind':n.kind.value,'label':n.label,'version':n.version,'state':n.state.value,'provenance':n.provenance_sha256} for n in nodes], 'relations':[{'id':r.id,'source':r.source_id,'target':r.target_id,'kind':r.kind.value,'version':r.version,'confidence':r.confidence,'provenance':r.provenance_sha256} for r in rels]}
  digest=sha256(json.dumps(canonical,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();prev=self.repo.latest_snapshot(tenant);seq=(prev.sequence+1) if prev else 1
  if prev and prev.content_sha256==digest:return prev
  if prev:self.repo.save_snapshot(replace(prev,state=SnapshotState.SUPERSEDED))
  x=GraphSnapshot(uuid4().hex,tenant,seq,digest,len(nodes),len(rels),reason.strip() or 'manual',actor,SnapshotState.ACTIVE,self.now());self.repo.save_snapshot(x);return x
 def impact_analysis(self,tenant,relation_id,max_depth=8):
  r=self.repo.relation(tenant,relation_id)
  if not r:raise ValueError('relation_not_found')
  if r.kind not in {RelationKind.PREREQUISITE_OF,RelationKind.DEPENDS_ON}:return ()
  snap=self.repo.latest_snapshot(tenant);out=[];seen=set()
  for d in (LearningDependency(r.target_id,0,(r.target_id,),()),)+self.dependents(tenant,r.target_id,max_depth):
   if d.concept_id in seen:continue
   seen.add(d.concept_id);path=(r.source_id,r.target_id)+d.path if d.distance else (r.source_id,r.target_id)
   x=GraphImpact(uuid4().hex,tenant,r.id,'dependency_change',d.concept_id,d.distance,path,snap.id if snap else None,self.now());self.repo.save_impact(x);out.append(x)
  return tuple(out)
 def retire_relation(self,tenant,id,actor,expected_version=None):
  x=self.repo.relation(tenant,id)
  if not x:raise ValueError('relation_not_found')
  if expected_version is not None and x.version!=expected_version:raise ValueError('graph_version_conflict')
  impacts=self.impact_analysis(tenant,id) if x.state==GovernanceState.PUBLISHED else ()
  y=replace(x,state=GovernanceState.RETIRED,version=x.version+1,updated_at=self.now());self.repo.save_relation(y);return y,impacts
 def prerequisite_plan(self,tenant,concept_id,mastery):
  mastery={str(k):float(v) for k,v in mastery.items()};seq=self.learning_sequence(tenant,concept_id);items=[]
  for pos,cid in enumerate(seq):
   score=max(0.0,min(1.0,mastery.get(cid,0.0)));items.append({'concept_id':cid,'order':pos+1,'mastery':score,'action':'review' if score<0.7 else 'verify','reason':'published_dependency_order'})
  return tuple(items)
 def _find_node(self,tenant,label,course_id):
  norm=label.strip().casefold();return next((n for n in self.repo.nodes(tenant) if n.label.casefold()==norm and (not course_id or n.course_id==course_id)),None)
 def _would_cycle(self,tenant,source,target):
  rels=[r for r in self.repo.relations(tenant) if r.state in {GovernanceState.VALIDATED,GovernanceState.PUBLISHED} and r.kind in {RelationKind.PREREQUISITE_OF,RelationKind.DEPENDS_ON}];adj={}
  for r in rels:adj.setdefault(r.source_id,[]).append(r.target_id)
  q=[target];seen=set()
  while q:
   x=q.pop()
   if x==source:return True
   if x in seen:continue
   seen.add(x);q.extend(adj.get(x,()))
  return False

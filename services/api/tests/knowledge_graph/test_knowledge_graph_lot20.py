from datetime import UTC,datetime
import pytest
from app.modules.knowledge_graph.application.service import KnowledgeGraphService
from app.modules.knowledge_graph.domain.model import *
class Repo:
 def __init__(self):self.ns={};self.rs={}
 def save_node(self,x):self.ns[x.id]=x
 def node(self,t,id):
  x=self.ns.get(id);return x if x and x.tenant_id==t else None
 def save_relation(self,x):self.rs[x.id]=x
 def relation(self,t,id):
  x=self.rs.get(id);return x if x and x.tenant_id==t else None
 def relations(self,t):return tuple(x for x in self.rs.values() if x.tenant_id==t)
def svc():return KnowledgeGraphService(Repo(),lambda:datetime(2026,9,24,tzinfo=UTC))
def nodes(s):
 a=s.create_node('t','concept','Gradient ionique');b=s.create_node('t','concept','Potentiel membranaire');c=s.create_node('t','concept','Potentiel action');return a,b,c
def publish(s,a,b,actor='u'):
 r=s.propose_relation('t',a.id,b.id,'prerequisite_of','prérequis conceptuel',95,actor);r=s.validate_relation('t',r.id,'reviewer');return s.publish_relation('t',r.id,'publisher')
def test_ai_node_requires_provenance():
 s=svc()
 with pytest.raises(ValueError,match='provenance_required'):s.create_node('t','concept','x',origin='ai_proposal')
def test_self_relation_forbidden():
 s=svc();a=s.create_node('t','concept','x')
 with pytest.raises(ValueError,match='self_relation_forbidden'):s.propose_relation('t',a.id,a.id,'prerequisite_of','x',80,'u')
def test_ai_relation_independent_review():
 s=svc();a,b,_=nodes(s);r=s.propose_relation('t',a.id,b.id,'prerequisite_of','x',80,'u','ai_proposal',provenance_sha256='a'*64)
 with pytest.raises(ValueError,match='independent_review_required'):s.validate_relation('t',r.id,'u')
def test_high_stakes_requires_provenance():
 s=svc();a,b,_=nodes(s);r=s.propose_relation('t',a.id,b.id,'prerequisite_of','x',80,'u');r=s.validate_relation('t',r.id,'r')
 with pytest.raises(ValueError,match='high_stakes'):s.publish_relation('t',r.id,'p',True)
def test_transitive_prerequisites_and_root_cause():
 s=svc();a,b,c=nodes(s);publish(s,a,b);publish(s,b,c);d=s.prerequisites('t',c.id);assert [x.concept_id for x in d]==[b.id,a.id];rank=s.root_cause_candidates('t',c.id,[a.id]);assert rank[0]['concept_id']==a.id and rank[0]['distance']==2
def test_cycle_rejected_after_validated_edges():
 s=svc();a,b,c=nodes(s);publish(s,a,b);publish(s,b,c)
 with pytest.raises(ValueError,match='dependency_cycle'):s.propose_relation('t',c.id,a.id,'prerequisite_of','bad',80,'u')
def test_candidate_edges_not_used_for_learning_decisions():
 s=svc();a,b,_=nodes(s);s.propose_relation('t',a.id,b.id,'prerequisite_of','candidate',90,'u');assert s.prerequisites('t',b.id)==()
def test_assessment_context_never_treats_graph_as_answer_key():
 s=svc();a,b,c=nodes(s);publish(s,a,b);publish(s,b,c);x=s.assessment_context('t',b.id);assert a.id in x['prerequisites'] and c.id in x['transfer_targets'] and 'never as an unsourced answer key' in x['instruction']

def _upgrade_repo(s):
 r=s.repo;r.bs={};r.cs={};r.nodes=lambda t:tuple(x for x in r.ns.values() if x.tenant_id==t);r.save_batch=lambda x:r.bs.__setitem__(x.id,x);r.batch=lambda t,id:(r.bs.get(id) if r.bs.get(id) and r.bs[id].tenant_id==t else None);r.save_candidate=lambda x:r.cs.__setitem__(x.id,x);r.candidate=lambda t,id:(r.cs.get(id) if r.cs.get(id) and r.cs[id].tenant_id==t else None);r.all_candidates=lambda t:tuple(x for x in r.cs.values() if x.tenant_id==t);return s

def test_extraction_requires_exact_source_sha():
 s=_upgrade_repo(svc())
 with pytest.raises(ValueError,match='source_sha256_required'):s.start_extraction('t','rev','bad','c','author',[])

def test_extraction_deduplicates_same_candidate_within_batch():
 s=_upgrade_repo(svc());raw={'candidate_type':'node','label':'Gradient ionique','kind':'concept','source_locator':'p.12','confidence':91};b,items=s.start_extraction('t','rev','a'*64,'c','author',[raw,raw]);assert len(items)==1 and b.candidate_count==2

def test_extraction_candidate_requires_locator():
 s=_upgrade_repo(svc())
 with pytest.raises(ValueError,match='source_locator_required'):s.start_extraction('t','rev','a'*64,'c','author',[{'candidate_type':'node','label':'x'}])

def test_extraction_requires_independent_reviewer():
 s=_upgrade_repo(svc());b,items=s.start_extraction('t','rev','a'*64,'c','author',[{'candidate_type':'node','label':'x','kind':'concept','source_locator':'p.1','confidence':90}]);s.submit_extraction_review('t',b.id,'author')
 with pytest.raises(ValueError,match='independent_review_required'):s.accept_candidate('t',items[0].id,'author')

def test_accept_node_preserves_provenance_and_locator():
 s=_upgrade_repo(svc());b,items=s.start_extraction('t','rev','a'*64,'c','author',[{'candidate_type':'node','label':'Gradient','kind':'concept','source_locator':'p.4','confidence':88}]);s.submit_extraction_review('t',b.id,'author');x=s.accept_candidate('t',items[0].id,'reviewer');n=s.repo.node('t',x.created_node_id);assert n.provenance_sha256=='a'*64 and n.source_locator=='p.4' and n.origin==Origin.SOURCE_EXTRACTION

def test_high_stakes_low_confidence_candidate_blocked():
 s=_upgrade_repo(svc());b,items=s.start_extraction('t','rev','a'*64,'c','author',[{'candidate_type':'node','label':'x','kind':'concept','source_locator':'p.1','confidence':55}]);s.submit_extraction_review('t',b.id,'author')
 with pytest.raises(ValueError,match='high_stakes_confidence_too_low'):s.accept_candidate('t',items[0].id,'reviewer',True)

def test_relation_candidate_requires_existing_nodes():
 s=_upgrade_repo(svc());b,items=s.start_extraction('t','rev','a'*64,'c','author',[{'candidate_type':'relation','source_label':'A','target_label':'B','kind':'prerequisite_of','source_locator':'p.2','confidence':90}]);s.submit_extraction_review('t',b.id,'author')
 with pytest.raises(ValueError,match='relation_nodes_must_exist'):s.accept_candidate('t',items[0].id,'reviewer')

def test_learning_sequence_orders_deep_prerequisites_first():
 s=_upgrade_repo(svc());a,b,c=nodes(s);publish(s,a,b);publish(s,b,c);assert s.learning_sequence('t',c.id)==(a.id,b.id,c.id)

def test_graph_health_surfaces_orphans_and_review_backlog():
 s=_upgrade_repo(svc());a=s.create_node('t','concept','orphan');s.start_extraction('t','rev','a'*64,'c','author',[{'candidate_type':'node','label':'x','kind':'concept','source_locator':'p.1','confidence':80}]);h=s.graph_health('t');assert a.id in h['orphan_concepts'] and h['review_backlog']==1

def _upgrade_closure_repo(s):
 s=_upgrade_repo(s);r=s.repo;r.snaps={};r.imps={}
 r.save_snapshot=lambda x:r.snaps.__setitem__(x.id,x)
 r.latest_snapshot=lambda t:max((x for x in r.snaps.values() if x.tenant_id==t),key=lambda x:x.sequence,default=None)
 r.save_impact=lambda x:r.imps.__setitem__(x.id,x)
 r.impacts=lambda t:tuple(x for x in r.imps.values() if x.tenant_id==t)
 return s

def test_snapshot_is_deterministic_and_deduplicated():
 s=_upgrade_closure_repo(svc());a,b,c=nodes(s);publish(s,a,b);x=s.create_snapshot('t','u','release');y=s.create_snapshot('t','u','same graph');assert x.id==y.id and len(x.content_sha256)==64 and x.relation_count==1

def test_snapshot_changes_after_published_graph_change():
 s=_upgrade_closure_repo(svc());a,b,c=nodes(s);publish(s,a,b);x=s.create_snapshot('t','u');publish(s,b,c);y=s.create_snapshot('t','u');assert y.sequence==2 and y.content_sha256!=x.content_sha256 and s.repo.snaps[x.id].state==SnapshotState.SUPERSEDED

def test_impact_analysis_finds_direct_and_downstream_dependents():
 s=_upgrade_closure_repo(svc());a,b,c=nodes(s);r1=publish(s,a,b);publish(s,b,c);s.create_snapshot('t','u');items=s.impact_analysis('t',r1.id);assert {x.affected_concept_id for x in items}=={b.id,c.id} and all(x.snapshot_id for x in items)

def test_retire_relation_records_impact_and_uses_optimistic_version():
 s=_upgrade_closure_repo(svc());a,b,c=nodes(s);r=publish(s,a,b);s.create_snapshot('t','u')
 with pytest.raises(ValueError,match='graph_version_conflict'):s.retire_relation('t',r.id,'u',999)
 y,imp=s.retire_relation('t',r.id,'u',r.version);assert y.state==GovernanceState.RETIRED and imp and s.prerequisites('t',b.id)==()

def test_prerequisite_plan_orders_graph_and_uses_mastery_threshold():
 s=_upgrade_closure_repo(svc());a,b,c=nodes(s);publish(s,a,b);publish(s,b,c);plan=s.prerequisite_plan('t',c.id,{a.id:.9,b.id:.4});assert [x['concept_id'] for x in plan]==[a.id,b.id,c.id] and [x['action'] for x in plan]==['verify','review','review']

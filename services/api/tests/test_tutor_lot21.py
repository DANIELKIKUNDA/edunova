from datetime import UTC,datetime
import pytest
from app.modules.tutor.application.service import TutorService
from app.modules.tutor.domain.model import TutorEvidence,TutorMove
class Repo:
 def __init__(self):self.s={};self.t=[]
 def save_session(self,x):self.s[x.id]=x
 def session(self,a,i):x=self.s.get(i);return x if x and x.account_id==a else None
 def save_turn(self,x):self.t.append(x)
 def turn_by_mutation(self,a,m):return next((x for x in self.t if x.account_id==a and x.mutation_id==m),None)
 def turns(self,a,sid,limit=50):return tuple(x for x in self.t if x.account_id==a and x.session_id==sid)
def svc():return TutorService(Repo(),lambda:datetime(2026,9,25,tzinfo=UTC))
def test_socratic_default():
 s=svc();x=s.start('a',target_concept_id='c');t=s.decide(x,'Pourquoi ?');assert t.decision.move==TutorMove.SOCRATIC and t.decision.bloom_target=='analyze'
def test_explicit_answer_explains_then_checks():
 s=svc();x=s.start('a','course','c');t=s.decide(x,'Explique',source_count=1,wants_answer=True);assert t.decision.move==TutorMove.EXPLAIN and t.decision.requires_sources
def test_high_stakes_abstains_without_source():
 s=svc();x=s.start('a','med','c','medicine',True);t=s.decide(x,'Explique',wants_answer=True);assert t.decision.move==TutorMove.ABSTAIN
def test_weak_prerequisite_wins():
 s=svc();x=s.start('a',target_concept_id='action');t=s.decide(x,'Aide',evidence=(TutorEvidence('gradient',.3,1),),prerequisites=('gradient',));assert t.decision.move==TutorMove.PREREQUISITE and t.decision.target_concept_id=='gradient'
def test_repeated_error_routes_remediation():
 s=svc();x=s.start('a',target_concept_id='c');t=s.decide(x,'Aide',evidence=(TutorEvidence('c',.5,3,'apply'),));assert t.decision.move==TutorMove.REMEDIATE
def test_progressive_hint_after_first_turn():
 s=svc();x=s.start('a',target_concept_id='c');s.decide(x,'Q1');x=s.repo.session('a',x.id);t=s.decide(x,'Q2');assert t.decision.move==TutorMove.HINT and t.decision.hint_level==1
def test_mutation_id_idempotent():
 s=svc();x=s.start('a');a=s.decide(x,'Q1',mutation_id='m1');x=s.repo.session('a',x.id);b=s.decide(x,'Q1',mutation_id='m1');assert a.id==b.id
def test_close_optimistic_lock():
 s=svc();x=s.start('a');
 with pytest.raises(ValueError,match='conflict'):s.close('a',x.id,99)

from datetime import UTC,datetime
import pytest
from app.modules.remediation.application.service import RemediationService
from app.modules.learning_experience.domain.model import LearningProgress,MasteryStage,ErrorItem
N=datetime(2026,9,24,tzinfo=UTC)
class Learning:
 def __init__(self,acc=5,total=10,errors=2):self.p=LearningProgress('u','med','cardio',MasteryStage.PRACTICED,.8,2,1,acc,total,N);self.es=[ErrorItem(str(i),'u','med','cardio','assessment','q','Erreur','Réponse',1,False,N,N,N) for i in range(errors)]
 def all_progress(self,a):return (self.p,)
 def unresolved_errors(self,a,n):return tuple(self.es)
 def progress(self,a,c,ch):return self.p
class Repo:
 def __init__(self):self.ms={};self.ps={};self.ev=[]
 def find_open(self,a,c,ch,concept):return next((x for x in self.ms.values() if x.account_id==a and x.course_id==c and x.chapter_id==ch and x.state.value!='resolved'),None)
 def save_misconception(self,x):self.ms[x.id]=x
 def misconception(self,a,id):return self.ms.get(id)
 def open_misconceptions(self,a,n):return tuple(sorted((x for x in self.ms.values() if x.state.value!='resolved'),key=lambda x:-x.severity))
 def active_path(self,a,m):return next((x for x in self.ps.values() if x.misconception_id==m and x.status=='active'),None)
 def save_path(self,x):self.ps[x.id]=x
 def path(self,a,id):return self.ps.get(id)
 def active_paths(self,a,n):return tuple(x for x in self.ps.values() if x.status=='active')
 def save_event(self,e):self.ev.append(e)
 def events(self,a,n=100):return tuple(reversed(self.ev[-n:]))
def svc(acc=5,total=10,errors=2):return RemediationService(Repo(),Learning(acc,total,errors),None,lambda:N)
def test_diagnosis_uses_evidence_and_bloom_gap():
 s=svc();x=s.diagnose('u')[0];assert x.severity>=50 and x.confidence>=50 and 'accuracy=50' in x.evidence and x.bloom_gap=='analyze'
def test_diagnosis_does_not_invent_when_no_gap():assert svc(10,10,0).diagnose('u')==()
def test_path_is_six_stage_learning_loop_not_just_explanation():
 s=svc();m=s.diagnose('u')[0];p=s.create_path('u',m.id);assert [x.kind.value for x in p.steps]==['diagnose','explain','worked_example','practice','transfer','reassess'];assert p.steps[-1].success_criterion
def test_path_creation_idempotent():
 s=svc();m=s.diagnose('u')[0];assert s.create_path('u',m.id).id==s.create_path('u',m.id).id
def test_optimistic_locking():
 s=svc();p=s.create_path('u',s.diagnose('u')[0].id)
 with pytest.raises(ValueError,match='version_conflict'):s.advance('u',p.id,99)
def test_verification_requires_real_threshold_and_gain():
 s=svc();p=s.create_path('u',s.diagnose('u')[0].id);r=s.verify('u',p.id,74,p.row_version);assert not r.resolved and r.next_action=='targeted_practice'
def test_success_closes_misconception_and_schedules_review():
 s=svc();m=s.diagnose('u')[0];p=s.create_path('u',m.id);p=s.record_practice('u',p.id,80,0,p.row_version,True);r=s.verify('u',p.id,82,p.row_version);assert r.resolved and r.gain==32 and s.repo.ms[m.id].state.value=='resolved' and r.next_action=='spaced_review'
def test_invalid_score_rejected():
 s=svc();p=s.create_path('u',s.diagnose('u')[0].id)
 with pytest.raises(ValueError,match='invalid_verification_score'):s.verify('u',p.id,101,p.row_version)
def test_dashboard_prioritizes_severity():
 s=svc();s.diagnose('u');d=s.dashboard('u');assert d['open_misconceptions']==1 and d['priority'][0].severity>=20

def test_tutor_decision_is_explainable_and_root_cause_aware():
 s=svc();m=s.diagnose('u')[0];d=s.tutor_decision('u',m.id);assert d.rationale and d.require_transfer and d.intervention.value in {'contrast_cases','worked_example','transfer','retrieval','concept_rebuild','reflection'}
def test_low_evidence_diagnosis_is_marked_insufficient():
 s=svc(1,2,1);m=s.diagnose('u')[0];assert m.root_cause.value=='insufficient_evidence' and m.confidence<80
def test_mastery_cannot_be_claimed_without_transfer():
 s=svc();p=s.create_path('u',s.diagnose('u')[0].id);r=s.verify('u',p.id,90,p.row_version);assert not r.resolved and not r.transfer_verified
def test_adaptive_difficulty_rises_after_two_independent_successes():
 s=svc();p=s.create_path('u',s.diagnose('u')[0].id);p=s.record_practice('u',p.id,80,0,p.row_version);p=s.record_practice('u',p.id,85,1,p.row_version);assert p.difficulty_level==3
def test_hints_prevent_false_success_signal():
 s=svc();p=s.create_path('u',s.diagnose('u')[0].id);p=s.record_practice('u',p.id,95,3,p.row_version);assert p.consecutive_successes==0 and p.consecutive_failures==1
def test_retention_failure_reopens_and_marks_relapse():
 s=svc();m=s.diagnose('u')[0];p=s.create_path('u',m.id);p=s.record_practice('u',p.id,85,0,p.row_version,True);s.verify('u',p.id,85,p.row_version);closed=s.repo.ps[p.id];r=s.retention_check('u',p.id,60,closed.row_version);assert not r['retained'] and s.repo.ms[m.id].state.value=='relapsed'

def test_offline_practice_mutation_is_idempotent():
 s=svc();p=s.create_path('u',s.diagnose('u')[0].id);a=s.record_practice('u',p.id,82,0,p.row_version,False,'device-1:42');b=s.record_practice('u',p.id,82,0,p.row_version,False,'device-1:42');assert a.row_version==b.row_version and b.total_practice_attempts==1

def test_longitudinal_dashboard_exposes_learning_gain():
 s=svc();m=s.diagnose('u')[0];p=s.create_path('u',m.id);p=s.record_practice('u',p.id,85,0,p.row_version,True,'m1');s.verify('u',p.id,85,p.row_version);d=s.dashboard('u');assert d['longitudinal']['verified_cycles']==1 and d['longitudinal']['average_gain']==35.0

def test_remediation_emits_auditable_learning_events():
 s=svc();m=s.diagnose('u')[0];p=s.create_path('u',m.id);p=s.record_practice('u',p.id,80,0,p.row_version,False,'m2');k=[e.kind.value for e in s.repo.ev];assert 'diagnosed' in k and 'path_created' in k and 'practice_recorded' in k

def test_verification_accumulates_gain_for_longitudinal_metrics():
 s=svc();m=s.diagnose('u')[0];p=s.create_path('u',m.id);p=s.record_practice('u',p.id,85,0,p.row_version,True,'m3');s.verify('u',p.id,90,p.row_version);assert s.repo.ps[p.id].cumulative_gain==40

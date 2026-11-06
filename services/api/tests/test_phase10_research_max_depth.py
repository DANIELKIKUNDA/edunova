from datetime import UTC,datetime
from types import SimpleNamespace as O
from unittest.mock import Mock
import pytest
from app.modules.research.application.service import ResearchService
from app.modules.research.domain.model import *
from app.modules.campus.domain.model import CampusRole,MembershipState
from app.modules.student_records.domain.model import StudentState,RegistrationState
NOW=lambda:datetime(2026,10,9,tzinfo=UTC)
def fx():
 repo=Mock();campus=Mock();students=Mock(); students.get.return_value=O(id='s',institution_id='u',account_id='student',state=StudentState.ACTIVE);students.registrations.return_value=[O(id='reg',institution_id='u',state=RegistrationState.ENROLLED)]
 def mem(i,a):return O(state=MembershipState.ACTIVE,role=CampusRole.STUDENT if a=='student' else CampusRole.RECTOR)
 campus.membership.side_effect=mem;return ResearchService(repo,campus,students,NOW),repo,campus,students
def project(s,r):
 x=s.create('rector','u','s','reg','memoire','Analyse des systèmes universitaires','supervisor');r.get.return_value=x;return x
def test_research_project_requires_active_registration_and_valid_supervisor():
 s,r,c,st=fx();x=project(s,r);assert x.state==ResearchState.PROPOSED
 st.registrations.return_value=[]
 with pytest.raises(ValueError,match='active_registration'):s.create('rector','u','s','reg','tfc','Sujet valide ici','supervisor')
def test_revision_is_student_only_versioned_and_reviewed():
 s,r,_,_=fx();x=project(s,r);x=__import__('dataclasses').replace(x,state=ResearchState.IN_PROGRESS);r.get.return_value=x;r.revisions.return_value=[]
 rv=s.submit_revision('student','u',x.id,'doc://v1','a'*64,'Version 1');assert rv.number==1
 r.revisions.return_value=[rv]
 with pytest.raises(ValueError,match='pending_review'):s.submit_revision('student','u',x.id,'doc://v2','b'*64)
 q=s.review_revision('supervisor','u',x.id,rv.id,'changes_requested','Corriger chapitre 2');assert q.state==RevisionState.CHANGES_REQUESTED

def test_ready_for_defense_requires_approved_latest_revision():
 s,r,_,_=fx();x=project(s,r);x=__import__('dataclasses').replace(x,state=ResearchState.IN_PROGRESS);r.get.return_value=x;r.revisions.return_value=[]
 with pytest.raises(ValueError,match='approved_revision'):s.transition('rector','u',x.id,'ready_for_defense',1,'Prêt')
 rv=ResearchRevision('rv',x.id,1,'doc','a'*64,RevisionState.APPROVED,'',None,NOW(),NOW());r.revisions.return_value=[rv]
 y=s.transition('rector','u',x.id,'ready_for_defense',1,'Validé');assert y.state==ResearchState.READY_FOR_DEFENSE

def test_defense_separation_and_minutes_integrity():
 s,r,_,_=fx();x=project(s,r);x=__import__('dataclasses').replace(x,state=ResearchState.READY_FOR_DEFENSE);r.get.return_value=x;r.get_defense.return_value=None
 with pytest.raises(ValueError,match='separation'):s.schedule_defense('rector','u',x.id,NOW(),'Salle A','chair','chair')
 d=s.schedule_defense('rector','u',x.id,NOW(),'Salle A','chair','secretary');r.get_defense.return_value=d
 out=s.record_defense('rector','u',x.id,'passed',82.5,'Procès-verbal officiel');assert len(out.minutes_sha256)==64 and out.decision=='passed'

def test_cross_tenant_and_student_cannot_administer_research():
 s,r,_,st=fx()
 with pytest.raises(PermissionError):s.create('student','u','s','reg','tfc','Sujet valide ici','supervisor')
 st.get.return_value=O(institution_id='other',state=StudentState.ACTIVE)
 with pytest.raises(ValueError,match='scope_mismatch'):s.create('rector','u','s','reg','tfc','Sujet valide ici','supervisor')

from datetime import datetime,UTC
from types import SimpleNamespace as O
from unittest.mock import Mock
import pytest
from app.modules.jury.application.service import JuryService
from app.modules.jury.domain.model import JuryMember,JuryMemberRole,JuryVoteChoice,JuryState
from app.modules.campus.domain.model import CampusRole,MembershipState
NOW=lambda:datetime(2026,10,8,tzinfo=UTC)
def svc():
 r=Mock();c=Mock();s=Mock();a=Mock(); c.membership.return_value=O(role=CampusRole.RECTOR,state=MembershipState.ACTIVE); c.cohort.return_value=O(program_unit_id='p'); a.binding_for_cohort.return_value=O(curriculum_id='cur'); a.curriculum.return_value=O(effective_academic_year_id='y',program_unit_id='p',state=O(value='published')); r.members.return_value=(); r.outcomes.return_value=(); r.minutes.return_value=None
 x=JuryService(r,c,s,NOW,academic=a); j=x.create('rector','u','co','y','cur','Ordinaire',30,2); r.get.return_value=j; return x,r,c,j
def test_commission_requires_single_president_and_active_member():
 x,r,c,j=svc(); x.add_member('rector','u',j.id,'rector','president'); r.members.return_value=(JuryMember('m',j.id,'rector',JuryMemberRole.PRESIDENT,True,NOW()),)
 with pytest.raises(ValueError,match='president_already'): x.add_member('rector','u',j.id,'other','president')
def test_non_member_cannot_vote():
 x,r,c,j=svc(); r.outcome.return_value=O(id='o')
 with pytest.raises(PermissionError,match='voting_member'): x.vote('rector','u',j.id,'student','approve','ok')
def test_duplicate_vote_rejected():
 x,r,c,j=svc(); m=JuryMember('m',j.id,'rector',JuryMemberRole.PRESIDENT,True,NOW()); r.members.return_value=(m,); r.outcome.return_value=O(id='o'); r.votes.return_value=(O(account_id='rector'),)
 with pytest.raises(ValueError,match='already_cast'): x.vote('rector','u',j.id,'student','approve','ok')
def test_lock_requires_quorum():
 x,r,c,j=svc(); r.outcomes.return_value=(O(student_id='student',evidence_hash='x'),); r.members.return_value=(JuryMember('m',j.id,'rector',JuryMemberRole.PRESIDENT,True,NOW()),)
 with pytest.raises(ValueError,match='quorum_not_reached'): x.lock('rector','u',j.id,1)
def test_publication_requires_minutes():
 x,r,c,j=svc(); locked=O(**{**j.__dict__,'state':JuryState.LOCKED,'row_version':2}); r.get.return_value=locked
 with pytest.raises(ValueError,match='minutes_required'): x.publish('rector','u',j.id,2)
def test_lock_rejects_majority_rejection_even_with_quorum():
 x,r,c,j=svc(); m1=JuryMember('m1',j.id,'rector',JuryMemberRole.PRESIDENT,True,NOW()); m2=JuryMember('m2',j.id,'other',JuryMemberRole.MEMBER,True,NOW()); r.members.return_value=(m1,m2); r.outcomes.return_value=(O(student_id='student',evidence_hash='x'),); r.votes.return_value=(O(account_id='rector',choice=JuryVoteChoice.REJECT),O(account_id='other',choice=JuryVoteChoice.REJECT))
 with pytest.raises(ValueError,match='quorum_not_reached'): x.lock('rector','u',j.id,1)

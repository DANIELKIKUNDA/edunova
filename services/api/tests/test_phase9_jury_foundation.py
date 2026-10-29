from datetime import datetime, UTC
from types import SimpleNamespace as Obj
from unittest.mock import Mock
import pytest
from app.modules.jury.application.service import JuryService
from app.modules.jury.domain.model import JuryState, JuryDecision, JuryMember, JuryMemberRole, JuryVote, JuryVoteChoice
from app.modules.campus.domain.model import CampusRole, MembershipState
from app.modules.student_records.domain.model import StudentState, RegistrationState, CourseRegistrationState

NOW=lambda:datetime(2026,10,8,tzinfo=UTC)

def fixture(role=CampusRole.RECTOR, state=CourseRegistrationState.VALIDATED, credits=30):
    repo=Mock();campus=Mock();students=Mock();academic=Mock()
    campus.membership.return_value=Obj(role=role,state=MembershipState.ACTIVE)
    campus.cohort.return_value=Obj(program_unit_id='program')
    academic.binding_for_cohort.return_value=Obj(curriculum_id='curriculum')
    academic.curriculum.return_value=Obj(effective_academic_year_id='year',program_unit_id='program',state=Obj(value='published'))
    students.get.return_value=Obj(id='student',institution_id='uni',cohort_id='cohort',curriculum_id='curriculum',state=StudentState.ACTIVE)
    students.registrations.return_value=[Obj(id='reg',academic_year_id='year',cohort_id='cohort',curriculum_id='curriculum',state=RegistrationState.ENROLLED)]
    students.course_registrations.return_value=[Obj(id='course1',registration_id='reg',curriculum_course_id='ecue',credits=credits,state=state)]
    repo.outcome.return_value=None
    repo.members.return_value=(JuryMember('m','session','rector',JuryMemberRole.PRESIDENT,True,NOW()),)
    repo.votes.return_value=(JuryVote('v','session','student','rector',JuryVoteChoice.APPROVE,'ok',NOW()),)
    svc=JuryService(repo,campus,students,NOW,academic=academic)
    return svc,repo,students,academic

def session(svc,repo):
    x=svc.create('rector','uni','cohort','year','curriculum','Session ordinaire',30)
    repo.get.return_value=x
    return x

def test_jury_uses_only_canonical_validated_credits():
    svc,repo,_,_=fixture()
    x=session(svc,repo)
    outcome=svc.evaluate('rector','uni',x.id,'student','Résultats officiels vérifiés')
    assert outcome.decision==JuryDecision.PASS
    assert outcome.credits_earned==30
    assert len(outcome.evidence_hash)==64

def test_jury_pending_ecue_never_passes():
    svc,repo,_,_=fixture(state=CourseRegistrationState.ENROLLED)
    x=session(svc,repo)
    assert svc.evaluate('rector','uni',x.id,'student','Évaluation incomplète').decision==JuryDecision.DEFERRED

def test_jury_failed_ecue_requires_retake():
    svc,repo,_,_=fixture(state=CourseRegistrationState.FAILED)
    x=session(svc,repo)
    assert svc.evaluate('rector','uni',x.id,'student','Crédits insuffisants').decision==JuryDecision.RETAKE

def test_jury_teacher_cannot_create_session():
    svc,_,_,_=fixture(role=CampusRole.TEACHER)
    with pytest.raises(PermissionError,match='jury_authorized'):
        svc.create('teacher','uni','cohort','year','curriculum','Session',30)

def test_jury_cross_tenant_student_rejected():
    svc,repo,students,_=fixture()
    x=session(svc,repo)
    students.get.return_value=Obj(institution_id='another',cohort_id='cohort',curriculum_id='curriculum',state=StudentState.ACTIVE)
    with pytest.raises(ValueError,match='jury_student_scope_mismatch'):
        svc.evaluate('rector','uni',x.id,'student','Motif')

def test_jury_wrong_curriculum_binding_rejected():
    svc,_,_,academic=fixture()
    academic.binding_for_cohort.return_value=Obj(curriculum_id='another')
    with pytest.raises(ValueError,match='jury_curriculum_scope_mismatch'):
        svc.create('rector','uni','cohort','year','curriculum','Session',30)

def test_jury_lock_rejects_changed_academic_evidence():
    svc,repo,students,_=fixture()
    x=session(svc,repo)
    outcome=svc.evaluate('rector','uni',x.id,'student','Validé')
    repo.outcomes.return_value=(outcome,)
    students.course_registrations.return_value=[Obj(id='course1',registration_id='reg',curriculum_course_id='ecue',credits=30,state=CourseRegistrationState.FAILED)]
    with pytest.raises(ValueError,match='jury_outcome_stale_academic_evidence'):
        svc.lock('rector','uni',x.id,1)

def test_jury_lock_publish_version_and_transitions():
    svc,repo,_,_=fixture()
    x=session(svc,repo)
    outcome=svc.evaluate('rector','uni',x.id,'student','Vérifié')
    repo.outcomes.return_value=(outcome,)
    locked=svc.lock('rector','uni',x.id,1)
    assert locked.state==JuryState.LOCKED
    repo.get.return_value=locked
    with pytest.raises(ValueError,match='jury_concurrent_modification'):
        svc.publish('rector','uni',x.id,1)
    published=svc.publish('rector','uni',x.id,2)
    assert published.state==JuryState.PUBLISHED
    repo.get.return_value=published
    with pytest.raises(ValueError,match='jury_session_locked'):
        svc.evaluate('rector','uni',x.id,'student','Interdit')

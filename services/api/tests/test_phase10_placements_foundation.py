from datetime import UTC,datetime
from types import SimpleNamespace as Obj
from unittest.mock import Mock
import pytest
from app.modules.placements.application.service import PlacementService
from app.modules.placements.domain.model import PlacementState
from app.modules.campus.domain.model import CampusRole,MembershipState
from app.modules.student_records.domain.model import StudentState,RegistrationState
NOW=lambda:datetime(2026,10,8,tzinfo=UTC)
def fixture():
    repo=Mock();campus=Mock();students=Mock()
    def membership(institution,actor):
        if institution!='uni':return None
        return Obj(state=MembershipState.ACTIVE,role=CampusRole.STUDENT if actor=='student-account' else CampusRole.RECTOR)
    campus.membership.side_effect=membership
    students.get.return_value=Obj(id='student',institution_id='uni',account_id='student-account',state=StudentState.ACTIVE)
    students.registrations.return_value=[Obj(id='reg',institution_id='uni',state=RegistrationState.ENROLLED)]
    service=PlacementService(repo,campus,students,NOW)
    return service,repo,campus,students
def create(svc,repo):
    x=svc.create('rector','uni','student','reg','Hôpital central','supervisor','2026-10-01','2026-12-01')
    repo.get.return_value=x
    return x
def test_placement_create_requires_enrolled_student_and_supervisor():
    svc,repo,_,students=fixture();x=create(svc,repo)
    assert x.state==PlacementState.PROPOSED and x.version==1
    students.registrations.return_value=[]
    with pytest.raises(ValueError,match='active_registration'):
        svc.create('rector','uni','student','reg','Hôpital','supervisor','2026-10-01','2026-12-01')
def test_placement_rejects_cross_tenant_and_student_creation():
    svc,_,_,students=fixture()
    with pytest.raises(PermissionError):
        svc.create('student-account','uni','student','reg','Hôpital','supervisor','2026-10-01','2026-12-01')
    students.get.return_value=Obj(institution_id='other',state=StudentState.ACTIVE)
    with pytest.raises(ValueError,match='scope_mismatch'):
        svc.create('rector','uni','student','reg','Hôpital','supervisor','2026-10-01','2026-12-01')
def test_placement_transitions_and_optimistic_lock():
    svc,repo,_,_=fixture();x=create(svc,repo)
    with pytest.raises(ValueError,match='reason_required'):svc.transition('rector','uni',x.id,'approved',1,' ')
    with pytest.raises(ValueError,match='concurrent'):svc.transition('rector','uni',x.id,'approved',0,'Vérifié')
    with pytest.raises(ValueError,match='invalid_transition'):svc.transition('rector','uni',x.id,'completed',1,'Vérifié')
    approved=svc.transition('rector','uni',x.id,'approved',1,'Convention signée')
    assert approved.version==2
    repo.get.return_value=approved
    active=svc.transition('rector','uni',x.id,'active',2,'Début')
    assert active.state==PlacementState.ACTIVE
def test_placement_log_only_student_during_active_period():
    svc,repo,_,_=fixture();x=create(svc,repo)
    with pytest.raises(ValueError,match='not_active'):svc.log('student-account','uni',x.id,'2026-10-09','Visite clinique')
    repo.get.return_value=Obj(**{**x.__dict__,'state':PlacementState.ACTIVE})
    with pytest.raises(PermissionError,match='student_log_only'):svc.log('rector','uni',x.id,'2026-10-09','Visite clinique')
    with pytest.raises(ValueError,match='outside_dates'):svc.log('student-account','uni',x.id,'2027-01-09','Visite clinique')
    y=svc.log('student-account','uni',x.id,'2026-10-09','Visite clinique')
    assert y.description=='Visite clinique'
def test_placement_invalid_dates_and_inactive_supervisor():
    svc,_,campus,_=fixture()
    with pytest.raises(ValueError,match='dates_invalid'):
        svc.create('rector','uni','student','reg','Hôpital','supervisor','2026-12-01','2026-10-01')
    campus.membership.side_effect=lambda i,a:Obj(state=MembershipState.ACTIVE,role=CampusRole.STUDENT) if a=='supervisor' else Obj(state=MembershipState.ACTIVE,role=CampusRole.RECTOR)
    with pytest.raises(ValueError,match='supervisor_invalid'):
        svc.create('rector','uni','student','reg','Hôpital','supervisor','2026-10-01','2026-12-01')

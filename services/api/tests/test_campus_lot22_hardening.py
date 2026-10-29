from datetime import UTC,date,datetime
import pytest
from app.modules.campus.application.service import CampusService
from app.modules.campus.domain.model import *
from test_campus_lot22 import Repo

def svc(): return CampusService(Repo(),lambda:datetime(2026,9,25,tzinfo=UTC))

def bootstrap_scoped_admin():
 s=svc(); i=s.create_institution('owner',name='Université',slug='uni')
 f1=s.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Médecine',code='MED')
 f2=s.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Droit',code='LAW')
 s.invite_member('owner',i.id,account_id='fa',role=CampusRole.FACULTY_ADMIN,unit_id=f1.id);s.accept_invitation('fa',i.id)
 return s,i,f1,f2

def test_admin_cannot_create_or_invite_owner():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni');s.invite_member('owner',i.id,account_id='admin',role=CampusRole.ADMIN);s.accept_invitation('admin',i.id)
 with pytest.raises(PermissionError,match='role_escalation'): s.invite_member('admin',i.id,account_id='x',role=CampusRole.OWNER)

def test_rector_cannot_create_owner():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni');s.invite_member('owner',i.id,account_id='rector',role=CampusRole.RECTOR);s.accept_invitation('rector',i.id)
 with pytest.raises(PermissionError,match='role_escalation'): s.invite_member('rector',i.id,account_id='x',role=CampusRole.OWNER)

def test_faculty_admin_is_confined_to_own_subtree():
 s,i,f1,f2=bootstrap_scoped_admin()
 d=s.add_unit('fa',i.id,kind=UnitKind.DEPARTMENT,name='Sciences',code='SCI',parent_id=f1.id)
 assert d.parent_id==f1.id
 with pytest.raises(PermissionError,match='scope_forbidden'): s.add_unit('fa',i.id,kind=UnitKind.DEPARTMENT,name='Privé',code='PRV',parent_id=f2.id)
 with pytest.raises(PermissionError,match='scope_forbidden'): s.invite_member('fa',i.id,account_id='stu',role=CampusRole.STUDENT,unit_id=f2.id)

def test_faculty_admin_requires_scope():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni')
 with pytest.raises(ValueError,match='faculty_admin_scope_required'): s.invite_member('owner',i.id,account_id='fa',role=CampusRole.FACULTY_ADMIN)

def test_period_kind_hierarchy_is_enforced():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni');y=s.add_period('owner',i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2026',starts_on=date(2026,10,1),ends_on=date(2027,7,31))
 sem=s.add_period('owner',i.id,kind=PeriodKind.SEMESTER,name='S1',starts_on=date(2026,10,1),ends_on=date(2027,2,1),parent_id=y.id)
 with pytest.raises(ValueError,match='invalid_period_hierarchy'): s.add_period('owner',i.id,kind=PeriodKind.SEMESTER,name='Bad',starts_on=date(2026,11,1),ends_on=date(2026,12,1),parent_id=sem.id)

def test_child_period_requires_parent_and_year_is_root():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni')
 with pytest.raises(ValueError,match='period_parent_required'): s.add_period('owner',i.id,kind=PeriodKind.SEMESTER,name='S1',starts_on=date(2026,10,1),ends_on=date(2027,2,1))

def test_suspended_institution_blocks_mutations_but_owner_can_read():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni');i=s.update_institution('owner',i.id,i.row_version,state=InstitutionState.SUSPENDED)
 assert s.institution('owner',i.id).state==InstitutionState.SUSPENDED
 with pytest.raises(PermissionError,match='institution_not_writable'): s.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Médecine',code='MED')

def test_member_role_change_has_privilege_guards_and_locking():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni');s.invite_member('owner',i.id,account_id='u',role=CampusRole.STUDENT);s.accept_invitation('u',i.id);m=s.repo.membership(i.id,'u')
 changed=s.set_member_role('owner',i.id,'u',CampusRole.TEACHER,m.row_version);assert changed.role==CampusRole.TEACHER
 with pytest.raises(ValueError,match='concurrent'):s.set_member_role('owner',i.id,'u',CampusRole.STUDENT,m.row_version)

def test_non_owner_cannot_promote_to_rector_or_admin_peer():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni');s.invite_member('owner',i.id,account_id='admin',role=CampusRole.ADMIN);s.accept_invitation('admin',i.id);s.invite_member('owner',i.id,account_id='u',role=CampusRole.STUDENT);s.accept_invitation('u',i.id);m=s.repo.membership(i.id,'u')
 with pytest.raises(PermissionError,match='role_escalation'):s.set_member_role('admin',i.id,'u',CampusRole.RECTOR,m.row_version)

def test_scoped_member_listing_does_not_leak_other_faculty():
 s,i,f1,f2=bootstrap_scoped_admin();s.invite_member('owner',i.id,account_id='medstu',role=CampusRole.STUDENT,unit_id=f1.id);s.invite_member('owner',i.id,account_id='lawstu',role=CampusRole.STUDENT,unit_id=f2.id)
 ids={m.account_id for m in s.list_members('fa',i.id)}
 assert 'medstu' in ids and 'lawstu' not in ids and 'fa' in ids

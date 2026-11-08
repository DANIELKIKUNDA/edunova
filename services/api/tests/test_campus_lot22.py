from datetime import UTC,date,datetime
import pytest
from app.modules.campus.application.service import CampusService
from app.modules.campus.domain.model import *
class Repo:
 def __init__(self):self.i={};self.u={};self.p={};self.m={};self.c={};self.e={}
 def institution(self,i):return self.i.get(i)
 def institution_by_slug(self,s):return next((x for x in self.i.values() if x.slug==s),None)
 def save_institution(self,x,expected_version=None):
  old=self.i.get(x.id)
  if old and expected_version is not None and old.row_version!=expected_version:raise ValueError('campus_concurrent_modification')
  self.i[x.id]=x
 def membership(self,i,a):return self.m.get((i,a))
 def save_membership(self,x,expected_version=None):
  old=self.m.get((x.institution_id,x.account_id))
  if old and expected_version is not None and old.row_version!=expected_version:raise ValueError('campus_concurrent_modification')
  self.m[(x.institution_id,x.account_id)]=x
 def institutions_for_account(self,a):return tuple((self.i[i],m) for (i,aa),m in self.m.items() if aa==a and m.state in {MembershipState.ACTIVE,MembershipState.INVITED})
 def unit(self,i,id):
  x=self.u.get(id);return x if x and x.institution_id==i else None
 def unit_by_code(self,i,code):return next((x for x in self.u.values() if x.institution_id==i and x.code==code.upper()),None)
 def save_unit(self,x):self.u[x.id]=x
 def period(self,i,id):
  x=self.p.get(id);return x if x and x.institution_id==i else None
 def save_period(self,x):self.p[x.id]=x
 def cohort(self,i,id):
  x=self.c.get(id);return x if x and x.institution_id==i else None
 def save_cohort(self,x):self.c[x.id]=x
 def enrollment(self,c,a):return self.e.get((c,a))
 def save_enrollment(self,x):self.e[(x.cohort_id,x.student_account_id)]=x
 def list_units(self,i):return tuple(x for x in self.u.values() if x.institution_id==i)
 def list_members(self,i):return tuple(x for (ii,_),x in self.m.items() if ii==i)
 def overview(self,i):return {'institution_id':i}
def svc():return CampusService(Repo(),lambda:datetime(2026,9,25,tzinfo=UTC))
def test_create_institution_bootstraps_owner():
 s=svc();i=s.create_institution('a',name='Université Test',slug='Universite Test');m=s.repo.membership(i.id,'a');assert i.slug=='universite-test' and m.role==CampusRole.OWNER and m.state==MembershipState.ACTIVE
def test_cross_tenant_isolation():
 s=svc();a=s.create_institution('a',name='A University',slug='a-university');b=s.create_institution('b',name='B University',slug='b-university')
 with pytest.raises(PermissionError,match='membership_required'):s.institution('a',b.id)
 with pytest.raises(PermissionError):s.add_unit('a',b.id,kind=UnitKind.FACULTY,name='Medicine',code='MED')
def test_hierarchy_and_duplicate_code():
 s=svc();i=s.create_institution('a',name='Université',slug='uni');f=s.add_unit('a',i.id,kind=UnitKind.FACULTY,name='Médecine',code='MED');d=s.add_unit('a',i.id,kind=UnitKind.DEPARTMENT,name='Sciences',code='SCI',parent_id=f.id);s.add_unit('a',i.id,kind=UnitKind.PROGRAM,name='Médecine',code='MD',parent_id=d.id)
 with pytest.raises(ValueError,match='code_exists'):s.add_unit('a',i.id,kind=UnitKind.FACULTY,name='X',code='MED')
def test_invalid_hierarchy_rejected():
 s=svc();i=s.create_institution('a',name='Université',slug='uni');p=s.add_unit('a',i.id,kind=UnitKind.PROGRAM,name='Droit',code='DRT')
 with pytest.raises(ValueError,match='invalid_unit_hierarchy'):s.add_unit('a',i.id,kind=UnitKind.FACULTY,name='Bad',code='BAD',parent_id=p.id)
def test_invitation_acceptance_and_role_escalation_guard():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni');f=s.add_unit('owner',i.id,kind=UnitKind.FACULTY,name='Médecine',code='MED');s.invite_member('owner',i.id,account_id='fa',role=CampusRole.FACULTY_ADMIN,unit_id=f.id);s.accept_invitation('fa',i.id)
 with pytest.raises(PermissionError,match='role_escalation'):s.invite_member('fa',i.id,account_id='admin',role=CampusRole.ADMIN)
 s.invite_member('fa',i.id,account_id='student',role=CampusRole.STUDENT,unit_id=f.id);assert s.repo.membership(i.id,'student').state==MembershipState.INVITED
def test_period_must_fit_parent():
 s=svc();i=s.create_institution('a',name='Université',slug='uni');y=s.add_period('a',i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2026-2027',starts_on=date(2026,10,1),ends_on=date(2027,7,31))
 with pytest.raises(ValueError,match='outside_parent'):s.add_period('a',i.id,kind=PeriodKind.SEMESTER,name='S1',starts_on=date(2026,9,1),ends_on=date(2027,1,31),parent_id=y.id)
def test_student_enrollment_requires_active_student():
 s=svc();i=s.create_institution('a',name='Université',slug='uni');p=s.add_unit('a',i.id,kind=UnitKind.PROGRAM,name='Informatique',code='INFO');y=s.add_period('a',i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2026',starts_on=date(2026,10,1),ends_on=date(2027,7,1));c=s.create_cohort('a',i.id,program_unit_id=p.id,academic_period_id=y.id,name='L1 Info',level='L1');s.invite_member('a',i.id,account_id='stu',role=CampusRole.STUDENT)
 with pytest.raises(ValueError,match='active_student'):s.enroll('a',i.id,cohort_id=c.id,student_account_id='stu')
 s.accept_invitation('stu',i.id);e=s.enroll('a',i.id,cohort_id=c.id,student_account_id='stu');assert e.active
def test_owner_cannot_be_revoked():
 s=svc();i=s.create_institution('a',name='Université',slug='uni');m=s.repo.membership(i.id,'a')
 with pytest.raises(ValueError,match='owner_cannot'):s.set_member_state('a',i.id,'a',MembershipState.REVOKED,m.row_version)
def test_optimistic_lock():
 s=svc();i=s.create_institution('a',name='Université',slug='uni')
 with pytest.raises(ValueError,match='concurrent'):s.update_institution('a',i.id,99,name='New')
def test_personal_identity_is_not_owned_by_tenant():
 s=svc();i=s.create_institution('owner',name='Université',slug='uni');s.invite_member('owner',i.id,account_id='stu',role=CampusRole.STUDENT);s.accept_invitation('stu',i.id);m=s.repo.membership(i.id,'stu');s.set_member_state('owner',i.id,'stu',MembershipState.REVOKED,m.row_version)
 assert s.repo.membership(i.id,'stu').state==MembershipState.REVOKED
 # Campus only changes membership; the account itself is deliberately outside this bounded context.
 assert not hasattr(s.repo,'accounts')

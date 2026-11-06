from datetime import UTC,datetime,timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.shared.infrastructure.database import Base
from app.modules.commerce.infrastructure.sqlalchemy_repo import SqlAlchemyCommercialRepository
from app.modules.commerce.application.commercial_service import CommercialService
from app.modules.campus.domain.model import Membership,CampusRole,MembershipState

class Campus:
 def __init__(self,role=CampusRole.OWNER,students=10):self.role=role;self.students=students
 def membership(self,i,a):return Membership('m',i,a,self.role,MembershipState.ACTIVE,None,None,None,1,NOW,NOW)
 def overview(self,i):return {'students_active':self.students}
NOW=datetime(2026,9,26,tzinfo=UTC)
def setup(role=CampusRole.OWNER,students=10):
 e=create_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool);Base.metadata.create_all(e); sf=sessionmaker(e,expire_on_commit=False); repo=SqlAlchemyCommercialRepository(sf); return CommercialService(repo,Campus(role,students),lambda:NOW),repo

def test_campus_license_seats_and_grace():
 s,r=setup(students=99); x=s.create_license(institution_id='u',actor_id='a',plan_code='campus-annual',seats=100,price_cdf=0)
 z=s.license_status('u');assert z['permitted'] and z['seat_overage']==0 and x.grace_until>x.ends_at

def test_campus_license_overage_blocks():
 s,r=setup(students=101);s.create_license(institution_id='u',actor_id='a',plan_code='campus-annual',seats=100,price_cdf=0);assert not s.license_status('u')['permitted']

def test_teacher_cannot_administer_commerce():
 s,r=setup(role=CampusRole.TEACHER)
 with pytest.raises(PermissionError):s.create_license(institution_id='u',actor_id='a',plan_code='x',seats=1,price_cdf=1)

def test_revenue_share_is_integer_and_reconcilable():
 s,r=setup();p=s.create_partner(actor_id='a',institution_id='u',name='Partner',share_bps=2500);s.create_share_rule(actor_id='a',institution_id='u',partner_id=p.id,share_bps=2500,product_code='premium-30d')
 x=s.record_revenue_share(institution_id='u',account_id='student',product_code='premium-30d',reference_id='pay-1',gross_cdf=3000)
 assert x['partner_cdf']==750 and x['platform_cdf']==2250
 z=s.settle_partner(actor_id='a',institution_id='u',partner_id=p.id,period_start=NOW-timedelta(days=1),period_end=NOW+timedelta(days=1));assert z.gross_cdf==3000 and z.partner_cdf==750 and z.platform_cdf==2250

def test_share_rule_validation():
 s,r=setup();p=s.create_partner(actor_id='a',institution_id='u',name='Partner',share_bps=1000)
 with pytest.raises(ValueError):s.create_share_rule(actor_id='a',institution_id='u',partner_id=p.id,share_bps=10001)

def test_revenue_share_duplicate_is_idempotent():
 s,r=setup();p=s.create_partner(actor_id='a',institution_id='u',name='Partner',share_bps=2500);s.create_share_rule(actor_id='a',institution_id='u',partner_id=p.id,share_bps=2500,product_code='premium-30d')
 a=s.record_revenue_share(institution_id='u',account_id='student',product_code='premium-30d',reference_id='pay-idem',gross_cdf=3000)
 b=s.record_revenue_share(institution_id='u',account_id='student',product_code='premium-30d',reference_id='pay-idem',gross_cdf=3000)
 assert not a['duplicate'] and b['duplicate']
 z=s.settle_partner(actor_id='a',institution_id='u',partner_id=p.id,period_start=NOW-timedelta(days=1),period_end=NOW+timedelta(days=1));assert z.gross_cdf==3000 and z.partner_cdf==750

def test_refund_compensates_revenue_without_rewriting_history():
 s,r=setup();p=s.create_partner(actor_id='a',institution_id='u',name='Partner',share_bps=2500);s.create_share_rule(actor_id='a',institution_id='u',partner_id=p.id,share_bps=2500,product_code='premium-30d')
 s.record_revenue_share(institution_id='u',account_id='student',product_code='premium-30d',reference_id='pay-r',gross_cdf=3000)
 s.record_refund(institution_id='u',account_id='student',product_code='premium-30d',reference_id='refund-r',original_reference_id='pay-r',gross_cdf=1000)
 z=s.settle_partner(actor_id='a',institution_id='u',partner_id=p.id,period_start=NOW-timedelta(days=1),period_end=NOW+timedelta(days=1));assert z.gross_cdf==2000 and z.partner_cdf==500 and z.platform_cdf==1500

def test_settlement_period_is_idempotent_and_requires_close_before_paid():
 s,r=setup();p=s.create_partner(actor_id='a',institution_id='u',name='Partner',share_bps=1000);s.create_share_rule(actor_id='a',institution_id='u',partner_id=p.id,share_bps=1000)
 s.record_revenue_share(institution_id='u',account_id='x',product_code='x',reference_id='p1',gross_cdf=1000)
 a=s.settle_partner(actor_id='a',institution_id='u',partner_id=p.id,period_start=NOW-timedelta(days=1),period_end=NOW+timedelta(days=1));b=s.settle_partner(actor_id='a',institution_id='u',partner_id=p.id,period_start=NOW-timedelta(days=1),period_end=NOW+timedelta(days=1));assert a.id==b.id
 with pytest.raises(ValueError):s.mark_settlement_paid(actor_id='a',institution_id='u',settlement_id=a.id)
 c=s.close_settlement(actor_id='a',institution_id='u',settlement_id=a.id);assert c.status=='closed'
 d=s.mark_settlement_paid(actor_id='a',institution_id='u',settlement_id=a.id);assert d.status=='paid'
 e=s.mark_settlement_paid(actor_id='a',institution_id='u',settlement_id=a.id);assert e.status=='paid'

def test_license_effective_grace_expiry_and_suspend():
 clock={'now':NOW}
 e=create_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool);Base.metadata.create_all(e);sf=sessionmaker(e,expire_on_commit=False);repo=SqlAlchemyCommercialRepository(sf);svc=CommercialService(repo,Campus(students=1),lambda:clock['now'])
 lic=svc.create_license(institution_id='u',actor_id='a',plan_code='campus',seats=2,price_cdf=0,duration_days=1,grace_days=2)
 clock['now']=NOW+timedelta(days=1,hours=1);assert svc.license_status('u')['effective_state']=='grace' and svc.license_status('u')['permitted']
 clock['now']=NOW+timedelta(days=3,hours=1);assert svc.license_status('u')['effective_state']=='expired' and not svc.license_status('u')['permitted']
 clock['now']=NOW;s=svc.suspend_license(institution_id='u',actor_id='a');assert s.state.value=='suspended' and not svc.license_status('u')['permitted']

def test_provider_reconciliation_detects_missing_unknown_and_amount_mismatch():
 s,r=setup();z=s.reconcile_provider(provider='momo',expected_payments=[{'reference':'a','amount_cdf':100},{'reference':'b','amount_cdf':200},{'reference':'c','amount_cdf':300}],provider_records=[{'reference':'a','amount_cdf':100},{'reference':'b','amount_cdf':250},{'reference':'x','amount_cdf':1}])
 assert not z.clean and z.matched_count==1 and z.missing_provider_refs==('c',) and z.amount_mismatch_refs==('b',) and z.unknown_provider_refs==('x',)

from datetime import UTC,datetime,timedelta
from app.modules.identity.application.service import IdentityService,RegisterInput
from app.modules.identity.infrastructure.memory import InMemoryAccountRepository,InMemorySessionRepository
from app.modules.identity.infrastructure.security import Argon2PasswordHasher,JwtTokenIssuer
from app.modules.trust_governance.application.service import TrustGovernanceService
from app.modules.trust_governance.domain.model import PrivacyRequestKind
class Clock:
 def __init__(self): self.t=datetime(2026,9,26,8,0,tzinfo=UTC)
 def __call__(self): return self.t
class Repo:
 def __init__(self): self.cons=[]; self.req=[]; self.ledger=[]
 def save_consent(self,x): self.cons.append(x)
 def list_consents(self,a): return [x for x in self.cons if x.account_id==a]
 def save_privacy_request(self,x): self.req.append(x)
 def last_ledger_hash(self): return self.ledger[-1].event_hash if self.ledger else None
 def save_ledger(self,x): self.ledger.append(x)
 def list_ledger(self): return self.ledger

def test_trusted_device_session_has_no_arbitrary_expiry_and_rotates_securely():
 c=Clock(); a=InMemoryAccountRepository(); s=InMemorySessionRepository(); svc=IdentityService(accounts=a,sessions=s,hasher=Argon2PasswordHasher(),tokens=JwtTokenIssuer(secret='z'*64),now=c)
 account,t=svc.register(RegisterInput(display_name='Daniel',password='StrongPass123',email='d@example.com',device_name='Android'))
 live=[x for x in s.items.values() if x.account_id==account.id and x.revoked_at is None]; assert len(live)==1 and live[0].expires_at is None
 c.t += timedelta(days=400); t2=svc.refresh(t.refresh_token,'Android'); assert t2.refresh_token != t.refresh_token
 assert len([x for x in s.items.values() if x.account_id==account.id and x.revoked_at is None])==1

def test_explicit_logout_still_ends_persistent_session():
 c=Clock(); a=InMemoryAccountRepository(); s=InMemorySessionRepository(); svc=IdentityService(accounts=a,sessions=s,hasher=Argon2PasswordHasher(),tokens=JwtTokenIssuer(secret='y'*64),now=c)
 _,t=svc.register(RegisterInput(display_name='D',password='StrongPass123',email='logout@example.com')); svc.logout(t.refresh_token)
 assert not any(x.revoked_at is None for x in s.items.values())

def test_personal_space_is_never_institutional_data():
 g=TrustGovernanceService(Repo(),Clock())
 for typ in ['tutor_conversation','private_document','personal_study_activity','personal_note']:
  assert not g.institutional_access_allowed(resource_type=typ,institutional_context=True)
 assert g.institutional_access_allowed(resource_type='official_grade',institutional_context=True)

def test_versioned_consent_withdrawal_is_historical_not_destructive():
 r=Repo(); g=TrustGovernanceService(r,Clock()); g.record_consent(account_id='a',purpose='external_ai',policy_version='2026-09',granted=True); g.record_consent(account_id='a',purpose='external_ai',policy_version='2026-09',granted=False)
 h=g.consent_history('a'); assert [x.state.value for x in h]==['granted','withdrawn']; assert g.verify_ledger()

def test_privacy_request_is_audited_in_hash_chain():
 r=Repo(); g=TrustGovernanceService(r,Clock()); q=g.request_privacy_action(account_id='a',kind=PrivacyRequestKind.EXPORT); assert q.state.value=='requested'; assert len(r.ledger)==1 and g.verify_ledger()
 r.ledger[0]=type(r.ledger[0])(**{**r.ledger[0].__dict__,'action':'tampered'}); assert not g.verify_ledger()

def test_external_ai_requires_current_explicit_consent():
 r=Repo(); g=TrustGovernanceService(r,Clock()); assert not g.external_ai_allowed('a')
 g.record_consent(account_id='a',purpose='external_ai',policy_version='v1',granted=True); assert g.external_ai_allowed('a')
 g.record_consent(account_id='a',purpose='external_ai',policy_version='v1',granted=False); assert not g.external_ai_allowed('a')

def test_institution_cannot_set_retention_for_personal_space():
 r=Repo(); r.save_retention=lambda x: None; g=TrustGovernanceService(r,Clock())
 import pytest
 with pytest.raises(PermissionError,match='personal_space'): g.set_retention_policy(actor_id='admin',institution_id='u',data_class='private_document',retention_days=30,policy_version='v1')
 x=g.set_retention_policy(actor_id='admin',institution_id='u',data_class='attendance',retention_days=365,policy_version='v1'); assert x.retention_days==365 and g.verify_ledger()

def test_totp_mfa_secret_is_encrypted_at_rest_and_verifiable():
 from app.modules.trust_governance.infrastructure.mfa import MfaVault,totp
 r=Repo(); r.mfa=None; r.save_mfa=lambda x:setattr(r,'mfa',x); r.get_mfa=lambda a:r.mfa if r.mfa and r.mfa.account_id==a else None
 g=TrustGovernanceService(r,Clock(),MfaVault('k'*40)); secret=g.begin_mfa_enrollment('a'); assert secret not in r.mfa.encrypted_secret
 code=totp(secret,at=1000000); g.confirm_mfa('a',code,at=1000000); assert g.mfa_enabled('a') and g.verify_mfa('a',code,at=1000000)

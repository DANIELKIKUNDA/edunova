from __future__ import annotations
from datetime import datetime
from uuid import uuid4
import hashlib, json
from app.modules.trust_governance.domain.model import *

PERSONAL_ONLY={'tutor_conversation','private_document','personal_study_activity','personal_note'}

class TrustGovernanceService:
    def __init__(self, repo, now, mfa_vault=None): self.repo=repo; self.now=now; self.mfa_vault=mfa_vault
    def record_consent(self, *, account_id:str,purpose:str,policy_version:str,granted:bool,source='user'):
        if not purpose.strip() or not policy_version.strip(): raise ValueError('purpose_and_policy_version_required')
        item=ConsentRecord(str(uuid4()),account_id,purpose.strip(),policy_version.strip(),ConsentState.GRANTED if granted else ConsentState.WITHDRAWN,self.now(),source)
        self.repo.save_consent(item); self._ledger(account_id,'privacy.consent.recorded','consent',item.id,{'purpose':item.purpose,'state':item.state.value,'policy_version':item.policy_version}); return item
    def consent_history(self, account_id): return self.repo.list_consents(account_id)
    def request_privacy_action(self, *, account_id:str,kind:PrivacyRequestKind):
        item=PrivacyRequest(str(uuid4()),account_id,kind,PrivacyRequestState.REQUESTED,self.now()); self.repo.save_privacy_request(item); self._ledger(account_id,'privacy.request.created','privacy_request',item.id,{'kind':kind.value}); return item
    def institutional_access_allowed(self, *, resource_type:str, institutional_context:bool)->bool:
        return institutional_context and resource_type not in PERSONAL_ONLY
    def assert_institutional_access(self, *, resource_type:str, institutional_context:bool):
        if not self.institutional_access_allowed(resource_type=resource_type,institutional_context=institutional_context): raise PermissionError('personal_space_isolation')


    def begin_mfa_enrollment(self,account_id:str):
        if self.mfa_vault is None: raise ValueError('mfa_not_configured')
        from app.modules.trust_governance.infrastructure.mfa import new_totp_secret
        secret=new_totp_secret(); x=MfaCredential(account_id,self.mfa_vault.encrypt(secret),False,self.now(),None); self.repo.save_mfa(x); self._ledger(account_id,'security.mfa.enrollment_started','account',account_id,{}); return secret
    def confirm_mfa(self,account_id:str,code:str,at:int|None=None):
        from dataclasses import replace
        from app.modules.trust_governance.infrastructure.mfa import verify_totp
        x=self.repo.get_mfa(account_id)
        if not x or self.mfa_vault is None or not verify_totp(self.mfa_vault.decrypt(x.encrypted_secret),code,at): raise ValueError('invalid_mfa_code')
        y=replace(x,enabled=True,verified_at=self.now()); self.repo.save_mfa(y); self._ledger(account_id,'security.mfa.enabled','account',account_id,{}); return y
    def verify_mfa(self,account_id:str,code:str,at:int|None=None)->bool:
        from app.modules.trust_governance.infrastructure.mfa import verify_totp
        x=self.repo.get_mfa(account_id); return bool(x and x.enabled and self.mfa_vault and verify_totp(self.mfa_vault.decrypt(x.encrypted_secret),code,at))
    def mfa_enabled(self,account_id:str)->bool:
        x=self.repo.get_mfa(account_id); return bool(x and x.enabled)
    def set_retention_policy(self, *, actor_id:str,institution_id:str,data_class:str,retention_days:int,policy_version:str):
        if retention_days < 1 or retention_days > 3650: raise ValueError('retention_days_out_of_range')
        if data_class in PERSONAL_ONLY: raise PermissionError('institution_cannot_govern_personal_space_retention')
        x=RetentionPolicy(str(uuid4()),institution_id,data_class,retention_days,policy_version,self.now(),actor_id); self.repo.save_retention(x); self._ledger(actor_id,'governance.retention.updated','retention_policy',x.id,{'institution_id':institution_id,'data_class':data_class,'days':retention_days,'policy_version':policy_version}); return x
    def latest_consent(self, account_id:str,purpose:str):
        items=[x for x in self.repo.list_consents(account_id) if x.purpose==purpose]
        return items[-1] if items else None
    def external_ai_allowed(self, account_id:str)->bool:
        x=self.latest_consent(account_id,'external_ai'); return bool(x and x.state==ConsentState.GRANTED)
    def _ledger(self,actor,action,typ,rid,meta):
        prev=self.repo.last_ledger_hash() or 'GENESIS'; at=self.now(); payload=json.dumps({'actor':actor,'action':action,'type':typ,'id':rid,'at':at.isoformat(),'previous':prev,'metadata':meta},sort_keys=True,separators=(',',':'))
        digest=hashlib.sha256(payload.encode()).hexdigest(); self.repo.save_ledger(SecurityLedgerEvent(str(uuid4()),actor,action,typ,rid,at,prev,digest,json.dumps(meta,sort_keys=True)))
    def verify_ledger(self):
        prev='GENESIS'
        for e in self.repo.list_ledger():
            if e.previous_hash != prev: return False
            meta=json.loads(e.metadata_json); payload=json.dumps({'actor':e.actor_id,'action':e.action,'type':e.resource_type,'id':e.resource_id,'at':e.occurred_at.isoformat(),'previous':e.previous_hash,'metadata':meta},sort_keys=True,separators=(',',':'))
            if hashlib.sha256(payload.encode()).hexdigest()!=e.event_hash: return False
            prev=e.event_hash
        return True

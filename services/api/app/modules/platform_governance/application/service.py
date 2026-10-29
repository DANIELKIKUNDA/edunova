from __future__ import annotations
from dataclasses import replace
from app.modules.platform_governance.domain.model import PlatformMembership,PlatformRole
class PlatformGovernanceService:
 def __init__(self,repo,now,audit=None):self.repo=repo;self.now=now;self.audit=audit
 def membership(self,account_id):return self.repo.get(account_id)
 def require(self,account_id,permission):
  m=self.repo.get(account_id)
  if not m or not m.active or permission not in m.permissions:raise PermissionError('platform_permission_denied')
  return m
 def grant(self,actor_id,target_id,role,expected_version=None):
  actor=self.require(actor_id,'platform.roles.manage'); now=self.now(); old=self.repo.get(target_id)
  if role==PlatformRole.OWNER and actor.role!=PlatformRole.OWNER:raise PermissionError('owner_role_requires_owner')
  if old and old.role==PlatformRole.OWNER and actor.role!=PlatformRole.OWNER:raise PermissionError('owner_membership_requires_owner')
  if old:
   if expected_version is None:raise ValueError('expected_version_required')
   if old.active and old.role==PlatformRole.OWNER and role!=PlatformRole.OWNER and actor_id==target_id:raise ValueError('owner_cannot_self_demote')
   if old.active and old.role==PlatformRole.OWNER and role!=PlatformRole.OWNER and self.repo.count_by_role().get(PlatformRole.OWNER.value,0)<=1:raise ValueError('last_owner_must_remain')
   x=replace(old,role=role,active=True,row_version=old.row_version+1,granted_by=actor_id,updated_at=now);self.repo.save(x,expected_version)
  else:
   if expected_version is not None:raise ValueError('unexpected_version')
   x=PlatformMembership(target_id,role,True,1,actor_id,now,now);self.repo.save(x)
  if self.audit:self.audit.write(actor_id=actor_id,action='platform.role.granted',entity_type='platform_membership',entity_id=target_id,metadata={'role':role.value})
  return x
 def deactivate(self,actor_id,target_id,expected_version):
  actor=self.require(actor_id,'platform.roles.manage'); old=self.repo.get(target_id)
  if old and old.role==PlatformRole.OWNER and actor.role!=PlatformRole.OWNER:raise PermissionError('owner_membership_requires_owner')
  if not old:raise ValueError('platform_membership_not_found')
  if old.role==PlatformRole.OWNER and actor_id==target_id:raise ValueError('owner_cannot_self_deactivate')
  if old.active and old.role==PlatformRole.OWNER and self.repo.count_by_role().get(PlatformRole.OWNER.value,0)<=1:raise ValueError('last_owner_must_remain')
  x=replace(old,active=False,row_version=old.row_version+1,updated_at=self.now());self.repo.save(x,expected_version)
  if self.audit:self.audit.write(actor_id=actor_id,action='platform.role.deactivated',entity_type='platform_membership',entity_id=target_id)
  return x
 def bootstrap_owner(self,account_id):
  if self.repo.get(account_id):return self.repo.get(account_id)
  now=self.now();x=PlatformMembership(account_id,PlatformRole.OWNER,True,1,account_id,now,now);self.repo.save(x);return x
 def dashboard(self,account_id):
  m=self.repo.get(account_id)
  if not m or not m.active:raise PermissionError('platform_permission_denied')
  return {'role':m.role.value,'permissions':sorted(m.permissions),'sections':self._sections(m.role)}
 def _sections(self,r):
  return {
   PlatformRole.OWNER:['universities','users','premium','revenue','growth','platform_health','security_alerts'],
   PlatformRole.PLATFORM_ADMIN:['institutions','accounts','configuration','operations','incidents'],
   PlatformRole.FINANCE_COMMERCIAL:['payments','premium','campus_licenses','revenue','settlements','reconciliation'],
   PlatformRole.CONTENT_EDITORIAL:['drafts','reviews','publications','sources','ocr','editorial_backlog'],
   PlatformRole.SUPPORT_OPERATOR:['tickets','service_status','diagnostics','incidents','escalations'],
   PlatformRole.SECURITY_AUDIT:['risky_sessions','security_events','audit_ledger','mfa','revocations','alerts'],
   PlatformRole.READ_ONLY_ANALYST:['global_kpis','cohorts','trends','usage','reports'],
  }[r]

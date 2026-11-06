from __future__ import annotations
import json,hashlib
from dataclasses import replace
from datetime import UTC,datetime
from uuid import uuid4
from app.modules.editorial.domain.model import EditorialRole,EditorialState
from app.modules.publication.domain.model import PublicationRelease,ReleaseState,RolloutMode,CatalogSnapshot
class PublicationService:
 def __init__(self,repo,editorial_repo,library_repo,audit=None,now=lambda:datetime.now(UTC)): self.repo=repo; self.editorial_repo=editorial_repo; self.library_repo=library_repo; self.audit=audit; self.now=now
 def _actor(self,id):
  m=self.editorial_repo.get_member(id)
  if not m or not m.active or m.role not in {EditorialRole.OWNER,EditorialRole.PUBLISHER}: raise PermissionError('publisher_role_required')
  return m
 def preflight(self,actor_id,item_id,revision_id):
  self._actor(actor_id); i=self.editorial_repo.get_item(item_id); r=self.editorial_repo.get_revision(revision_id)
  checks=[]
  checks.append(('item_exists',bool(i)))
  checks.append(('revision_matches',bool(r and r.item_id==item_id)))
  checks.append(('editorial_published',bool(i and i.state==EditorialState.PUBLISHED)))
  checks.append(('published_revision_matches',bool(i and i.published_revision_id==revision_id)))
  checks.append(('rights_clear',bool(i and i.rights_status.value in {'authorized','public_domain','internal_only'})))
  checks.append(('academic_context',bool(i and i.faculty_domain and i.program and i.level)))
  return {'passed':all(x[1] for x in checks),'checks':[{'code':c,'passed':p} for c,p in checks]}
 def create(self,*,actor_id,item_id,revision_id,version_label,placement,audience=None,rollout_mode=RolloutMode.ALL,rollout_percentage=100,premium_required=True,offline_allowed=True,scheduled_at=None):
  self._actor(actor_id); pf=self.preflight(actor_id,item_id,revision_id)
  if not pf['passed']: raise ValueError('publication_preflight_failed')
  required=('faculty_domain','program','level')
  if not isinstance(placement,dict) or any(not str(placement.get(k,'')).strip() for k in required): raise ValueError('invalid_academic_placement')
  if not 1<=rollout_percentage<=100: raise ValueError('invalid_rollout_percentage')
  if rollout_mode==RolloutMode.ALL and rollout_percentage!=100: raise ValueError('all_rollout_requires_100_percent')
  if rollout_mode==RolloutMode.AUDIENCE and not audience: raise ValueError('audience_rollout_requires_audience')
  if scheduled_at is not None and scheduled_at<=self.now(): raise ValueError('scheduled_at_must_be_future')
  now=self.now(); state=ReleaseState.SCHEDULED if scheduled_at else ReleaseState.DRAFT
  r=PublicationRelease(str(uuid4()),item_id,revision_id,state,version_label,json.dumps(placement,sort_keys=True),json.dumps(audience or {},sort_keys=True),rollout_mode,rollout_percentage,premium_required,offline_allowed,scheduled_at,None,None,actor_id,now,1)
  self.repo.save(r); self._audit(actor_id,'publication.release.created',r.id,{'state':r.state.value}); return r
 def publish(self,actor_id,release_id,expected_version=None):
  self._actor(actor_id); r=self.repo.get(release_id)
  if not r: raise ValueError('release_not_found')
  if expected_version is not None and r.row_version!=expected_version: raise ValueError('concurrent_modification')
  if r.state not in {ReleaseState.DRAFT,ReleaseState.SCHEDULED}: raise ValueError('invalid_release_state')
  # Re-run governance at the irreversible boundary: rights/state may have changed since draft creation.
  pf=self.preflight(actor_id,r.editorial_item_id,r.editorial_revision_id)
  if not pf['passed']: raise ValueError('publication_preflight_failed_at_publish')
  manifest={'release_id':r.id,'editorial_item_id':r.editorial_item_id,'editorial_revision_id':r.editorial_revision_id,'version_label':r.version_label,'placement':json.loads(r.placement_json),'audience':json.loads(r.audience_json),'rollout':{'mode':r.rollout_mode.value,'percentage':r.rollout_percentage},'premium_required':r.premium_required,'offline_allowed':r.offline_allowed}
  canonical=json.dumps(manifest,sort_keys=True,separators=(',',':')); sha=hashlib.sha256(canonical.encode()).hexdigest(); now=self.now()
  out=replace(r,state=ReleaseState.PUBLISHED,published_at=now,row_version=r.row_version+1); self.repo.save(out); self.repo.save_snapshot(CatalogSnapshot(str(uuid4()),r.id,sha,canonical,now)); self._audit(actor_id,'publication.release.published',r.id,{'manifest_sha256':sha}); return out
 def verify_snapshot(self,actor_id,release_id):
  self._actor(actor_id); x=self.repo.snapshot(release_id)
  if not x: raise ValueError('snapshot_not_found')
  actual=hashlib.sha256(x.manifest_json.encode()).hexdigest()
  return {'release_id':release_id,'expected_sha256':x.manifest_sha256,'actual_sha256':actual,'integrity_ok':actual==x.manifest_sha256}
 def withdraw(self,actor_id,release_id,expected_version=None):
  self._actor(actor_id); r=self.repo.get(release_id)
  if not r: raise ValueError('release_not_found')
  if expected_version is not None and r.row_version!=expected_version: raise ValueError('concurrent_modification')
  if r.state!=ReleaseState.PUBLISHED: raise ValueError('release_not_published')
  out=replace(r,state=ReleaseState.WITHDRAWN,withdrawn_at=self.now(),row_version=r.row_version+1); self.repo.save(out); self._audit(actor_id,'publication.release.withdrawn',r.id,{}); return out
 def process_due(self,actor_id):
  self._actor(actor_id); return tuple(self.publish(actor_id,x.id,x.row_version) for x in self.repo.due(self.now()))
 def _audit(self,a,action,id,meta):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type='publication_release',entity_id=id,metadata=meta)

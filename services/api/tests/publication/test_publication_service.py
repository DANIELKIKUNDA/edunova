from datetime import UTC,datetime,timedelta
import json
from app.modules.publication.application.service import PublicationService
from app.modules.publication.domain.model import RolloutMode,ReleaseState
from app.modules.editorial.domain.model import EditorialMember,EditorialRole,EditorialState,RightsStatus
class Obj:
 def __init__(self,**kw): self.__dict__.update(kw)
class E:
 def get_member(self,id): return EditorialMember(id,EditorialRole.PUBLISHER,True)
 def get_item(self,id): return Obj(id=id,state=EditorialState.PUBLISHED,published_revision_id='rev',rights_status=RightsStatus.AUTHORIZED,faculty_domain='Médecine',program='Médecine',level='BAC1')
 def get_revision(self,id): return Obj(id=id,item_id='item')
class R:
 def __init__(self): self.x={};self.snaps={}
 def save(self,x): self.x[x.id]=x
 def get(self,id): return self.x.get(id)
 def save_snapshot(self,x): self.snaps[x.release_id]=x
 def snapshot(self,id): return self.snaps.get(id)
 def due(self,now,limit=100): return tuple(x for x in self.x.values() if x.state==ReleaseState.SCHEDULED and x.scheduled_at<=now)
class A:
 def write(self,**kw): pass
def svc(): return PublicationService(R(),E(),None,A(),now=lambda:datetime(2026,9,24,tzinfo=UTC))
def test_preflight_and_immutable_snapshot():
 s=svc(); assert s.preflight('pub','item','rev')['passed']; r=s.create(actor_id='pub',item_id='item',revision_id='rev',version_label='2026.1',placement={'faculty_domain':'Médecine','program':'Médecine','level':'BAC1'},rollout_mode=RolloutMode.PERCENTAGE,rollout_percentage=10); assert r.state==ReleaseState.DRAFT; p=s.publish('pub',r.id,r.row_version); assert p.state==ReleaseState.PUBLISHED; snap=s.repo.snapshot(r.id); assert len(snap.manifest_sha256)==64 and json.loads(snap.manifest_json)['rollout']['percentage']==10
def test_scheduled_release_and_withdrawal():
 s=svc(); r=s.create(actor_id='pub',item_id='item',revision_id='rev',version_label='2026.1',placement={'faculty_domain':'Médecine','program':'Médecine','level':'BAC1'},scheduled_at=datetime(2026,9,25,tzinfo=UTC)); s.now=lambda:datetime(2026,9,26,tzinfo=UTC); done=s.process_due('pub'); assert done[0].state==ReleaseState.PUBLISHED; w=s.withdraw('pub',r.id,done[0].row_version); assert w.state==ReleaseState.WITHDRAWN
def test_preflight_rejects_unpublished():
 e=E(); e.get_item=lambda id: Obj(id=id,state=EditorialState.APPROVED,published_revision_id=None,rights_status=RightsStatus.AUTHORIZED,faculty_domain='X',program='Y',level='L1'); s=PublicationService(R(),e,None); assert not s.preflight('pub','item','rev')['passed']


def test_publish_rechecks_governance_and_snapshot_integrity():
 s=svc(); r=s.create(actor_id='pub',item_id='item',revision_id='rev',version_label='2026.2',placement={'faculty_domain':'Médecine','program':'Médecine','level':'BAC1'}); p=s.publish('pub',r.id,r.row_version); v=s.verify_snapshot('pub',p.id); assert v['integrity_ok'] and v['actual_sha256']==v['expected_sha256']

def test_release_contract_rejects_unsafe_distribution():
 s=svc()
 import pytest
 with pytest.raises(ValueError,match='invalid_academic_placement'): s.create(actor_id='pub',item_id='item',revision_id='rev',version_label='x',placement={'program':'Médecine'})
 with pytest.raises(ValueError,match='all_rollout_requires_100_percent'): s.create(actor_id='pub',item_id='item',revision_id='rev',version_label='x',placement={'faculty_domain':'F','program':'P','level':'L'},rollout_percentage=10)
 with pytest.raises(ValueError,match='audience_rollout_requires_audience'): s.create(actor_id='pub',item_id='item',revision_id='rev',version_label='x',placement={'faculty_domain':'F','program':'P','level':'L'},rollout_mode=RolloutMode.AUDIENCE)

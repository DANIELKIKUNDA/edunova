from pathlib import Path
import re
from app.modules.trust_governance.application.service import TrustGovernanceService
from app.modules.pilot_readiness.application.service import PilotReadinessService

ROOT=Path(__file__).resolve().parents[3]
def test_migrations_are_contiguous_and_reach_recovered_baseline():
 nums=sorted(int(p.name[:4]) for p in (ROOT/'services/api/migrations').glob('[0-9][0-9][0-9][0-9]_*.sql'))
 assert nums==list(range(nums[0],nums[-1]+1)) and nums[-1]>=53

def test_no_unresolved_todo_fixme_in_runtime_python():
 bad=[]
 for p in (ROOT/'services/api/app').rglob('*.py'):
  t=p.read_text(errors='ignore')
  if re.search(r'\b(TODO|FIXME|NotImplementedError)\b',t): bad.append(str(p))
 assert bad==[]

def test_personal_space_never_becomes_institutional():
 svc=TrustGovernanceService(None, lambda: None)
 for r in ('tutor_conversation','private_document','personal_study_activity','personal_note'):
  assert not svc.institutional_access_allowed(resource_type=r,institutional_context=True)

def test_pilot_invite_replay_is_rejected():
 s=PilotReadinessService(); token=s.create_invitation('inst','STUDENT'); s.consume_invitation(token)
 try: s.consume_invitation(token); assert False
 except ValueError: pass

def test_release_artifacts_exist():
 for rel in ('.github/workflows/ci.yml','.github/workflows/release.yml','docker-compose.production.yml','scripts/backup_postgres.sh','scripts/restore_postgres.sh','scripts/backup_object_storage.sh','scripts/restore_object_storage.sh'):
  assert (ROOT/rel).exists(), rel

def test_pwa_offline_contract_exists():
 assert (ROOT/'apps/mobile/web/manifest.json').exists(); assert (ROOT/'apps/mobile/web/sw.js').exists(); assert (ROOT/'apps/mobile/web/offline.html').exists()

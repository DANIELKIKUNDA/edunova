"""Static wiring sanity for Phase16 (NOT Dart/Flutter compilation)."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
G = ROOT / 'apps/mobile/lib/src/features/campus_services/infrastructure/campus_services_gateway.dart'
ROUTER = ROOT / 'apps/mobile/lib/src/app/router.dart'
CI = ROOT / '.github/workflows/ci.yml'
SERVICES = ROOT / 'services/api/app/modules/campus_services'
checks = {
    'alumni service': (SERVICES / 'application/alumni_service.py').exists(),
    'alumni SQL repository': (SERVICES / 'infrastructure/alumni_repo.py').exists(),
    'academic allocation repository': 'assign_calendar_resource' in (SERVICES / 'infrastructure/sqlalchemy_repo.py').read_text(),
    'teaching session allocation repository': 'assign_teaching_room' in (SERVICES / 'infrastructure/sqlalchemy_repo.py').read_text(),
    'alumni Flutter page': (ROOT / 'apps/mobile/lib/src/features/campus_services/presentation/campus_alumni_page.dart').exists(),
    'academic room Flutter page': (ROOT / 'apps/mobile/lib/src/features/campus_services/presentation/campus_academic_resources_page.dart').exists(),
    'Flutter alumni route': '/campus/alumni/:institutionId' in ROUTER.read_text(),
    'Flutter academic route': '/campus/academic-rooms/:institutionId' in ROUTER.read_text(),
    'gateway alumni endpoint': 'alumniDecide' in G.read_text(),
    'gateway teaching endpoint': 'assignTeachingRoom' in G.read_text(),
    'gateway no-cache semantics': "'Cache-Control': 'no-store'" in G.read_text(),
    'Flutter test source': (ROOT / 'apps/mobile/test/campus_academic_alumni_gateway_test.dart').exists(),
    'CI Flutter analyze': 'flutter analyze --no-pub' in CI.read_text(),
    'CI Flutter tests': 'flutter test --no-pub' in CI.read_text(),
    'CI Phase16 specific test': 'campus_academic_alumni_gateway_test.dart' in CI.read_text(),
    'SQL migration 0093': (ROOT / 'services/api/migrations/0093_campus_academic_resource_allocations_v0_51_8.sql').exists(),
    'SQL migration 0094': (ROOT / 'services/api/migrations/0094_campus_alumni_v0_51_8.sql').exists(),
    'SQL migration 0095': (ROOT / 'services/api/migrations/0095_campus_teaching_room_allocations_v0_51_8.sql').exists(),
}
for label, success in checks.items():
    print(('PASS' if success else 'FAIL') + ' : ' + label)
print(f'{sum(checks.values())}/{len(checks)} contrôles statiques réussis.')
if not all(checks.values()):
    raise SystemExit(1)

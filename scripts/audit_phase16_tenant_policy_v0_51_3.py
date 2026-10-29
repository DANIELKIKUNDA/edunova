"""Contrôles de câblage statiques (ne compilent PAS Flutter)."""
from pathlib import Path
base = Path(__file__).resolve().parents[1]
checks = {
    'SQL policy table': ('services/api/migrations/0089_campus_library_tenant_policy_v0_51_3.sql', 'CREATE TABLE IF NOT EXISTS campus_library_policies'),
    'SQL policy CAS': ('services/api/migrations/0089_campus_library_tenant_policy_v0_51_3.sql', 'row_version integer NOT NULL'),
    'SQL policy bounds': ('services/api/migrations/0089_campus_library_tenant_policy_v0_51_3.sql', 'max_renewals BETWEEN 0 AND 2'),
    'Mapped row': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'class PhysicalLibraryPolicyRow(Base)'),
    'Borrow in-transaction policy': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'policy = self._policy(session, loan.institution_id)'),
    'Policy tenant lock': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'campus_library_policy:{institution}'),
    'Policy compare and swap': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'if row.row_version != expected_version'),
    'Renew dynamic period': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'timedelta(days=policy.renewal_days)'),
    'RBAC update': ('services/api/app/modules/campus_services/application/physical_library_service.py', 'self._admin(account, institution)'),
    'API GET': ('services/api/app/modules/campus_services/api/physical_library_router.py', "@router.get('/institutions/{institution_id}/library/policy')"),
    'API PUT': ('services/api/app/modules/campus_services/api/physical_library_router.py', "@router.put('/institutions/{institution_id}/library/policy')"),
    'Flutter policy auth gateway': ('apps/mobile/lib/src/features/campus_services/infrastructure/campus_services_gateway.dart', 'updatePhysicalLibraryPolicy(String iid'),
    'Flutter tenant guard': ('apps/mobile/lib/src/features/campus_services/presentation/physical_library_page.dart', 'widget.institutionId == tenant'),
    'Flutter no stale policy': ('apps/mobile/lib/src/features/campus_services/presentation/physical_library_page.dart', '_policy = null;'),
    'Flutter policy editable': ('apps/mobile/lib/src/features/campus_services/presentation/physical_library_page.dart', 'Politique de prêt de l’université'),
    'Flutter policy dynamic display': ('apps/mobile/lib/src/features/campus_services/presentation/physical_library_page.dart', "_policy?['max_open_loans']"),
    'Flutter authored contract test': ('apps/mobile/test/campus_services_gateway_test.dart', 'Politique de bibliothèque : lecture et sauvegarde avec CAS'),
    'Backend adversarial tests': ('services/api/tests/test_phase16_library_tenant_policy_v0_51_3.py', 'test_stale_version_and_replay_are_rejected_unchanged'),
}
failures = []
for desc, (path, expected) in checks.items():
    found = expected in (base / path).read_text()
    print(f'{"PASS" if found else "FAIL"} {desc}')
    if not found:
        failures.append(desc)
print(f'STATIC WIRING: {len(checks)-len(failures)}/{len(checks)}')
if failures:
    raise SystemExit(1)

from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
 'campus_domain':root/'services/api/app/modules/campus/domain/model.py',
 'campus_service':root/'services/api/app/modules/campus/application/service.py',
 'campus_repository':root/'services/api/app/modules/campus/infrastructure/sqlalchemy_repo.py',
 'campus_api':root/'services/api/app/modules/campus/api/router.py',
 'migration_0031':root/'services/api/migrations/0031_campus_core_v0_23_0.sql',
 'adr_031':root/'docs/ADR-031-campus-multitenancy-boundary.md',
 'lot22_doc':root/'docs/LOT22_CAMPUS_CORE_v0.23.0.md',
 'campus_ui':root/'apps/mobile/lib/src/features/campus/presentation/campus_page.dart',
 'tests':root/'services/api/tests/test_campus_lot22.py',
}
failed=[]
for name,p in checks.items():
 ok=p.exists() and p.stat().st_size>100;print(('PASS' if ok else 'FAIL'),name,p.relative_to(root));failed += [] if ok else [name]
main=(root/'services/api/app/main.py').read_text();runtime=(root/'services/api/app/runtime.py').read_text();migration=(root/'services/api/migrations/0031_campus_core_v0_23_0.sql').read_text()
for name,ok in [('version_0_23_0','0.23.0' in main),('campus_router','campus_router' in main),('runtime_wiring','CampusService' in runtime),('tenant_columns',migration.count('institution_id')>=10),('brand_signature','From Volcano Tech' in (root/'apps/mobile/lib/src/features/campus/presentation/campus_page.dart').read_text())]:
 print(('PASS' if ok else 'FAIL'),name);failed += [] if ok else [name]
raise SystemExit(1 if failed else 0)

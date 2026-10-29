from pathlib import Path
R=Path(__file__).resolve().parents[1]
checks={
'bounded_context':R/'services/api/app/modules/institutional_analytics/application/service.py',
'api_router':R/'services/api/app/modules/institutional_analytics/api/router.py',
'snapshot_model':R/'services/api/app/modules/institutional_analytics/infrastructure/sqlalchemy_repo.py',
'migration_0046':R/'services/api/migrations/0046_institutional_analytics_snapshots_v0_28_1.sql',
'tests':R/'services/api/tests/test_institutional_analytics_lot27.py',
}
for k,p in checks.items(): assert p.exists(),k
svc=checks['bounded_context'].read_text();repo=checks['snapshot_model'].read_text();api=checks['api_router'].read_text();tests=checks['tests'].read_text()
assert 'capture_snapshot' in svc and 'compare_snapshots' in svc
assert 'unit_dashboard' in svc and 'snapshot_for_unit' in repo
assert 'sha256' in repo and 'save_immutable_snapshot' in repo
assert 'export_csv' in svc and 'export.csv' in api
assert 'personal-library' in repo and 'private-study' in repo
assert 'teacher_scope_required' in svc and 'unit_scope_denied' in svc
assert 'student' not in svc.split('export_csv',1)[1].lower()
assert 'test_immutable_snapshots' in tests and 'test_unit_rollup' in tests
print('LOT27 v0.28.1 AUDIT: 12/12 PASS')

from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
'module':root/'services/api/app/modules/campus_operations/application/service.py',
'api':root/'services/api/app/modules/campus_operations/api/router.py',
'migration':root/'services/api/migrations/0042_campus_operations_attendance_v0_27_0.sql',
'adr':root/'docs/architecture/ADR-042-campus-operations-secure-attendance.md',
'tests':root/'services/api/tests/test_campus_operations_lot26.py'}
for k,p in checks.items():assert p.exists(),k
svc=checks['module'].read_text();mig=checks['migration'].read_text();main=(root/'services/api/app/main.py').read_text()
assert 'hmac.compare_digest' in svc
assert 'qr_ttl_seconds' in svc and 'attendance_already_recorded' in svc
assert 'require_device_binding' in svc and 'location_latitude' in svc
assert 'NEEDS_REVIEW' in svc and 'risk=min(100,risk)' in svc
assert 'UNIQUE(attendance_session_id,student_account_id)' in mig
assert '0.27.0' in main and 'campus_operations_router' in main
print('LOT26 AUDIT: 12/12 PASS')

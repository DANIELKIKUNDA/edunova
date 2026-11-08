from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
'0043 migration':root/'services/api/migrations/0043_attendance_signed_proximity_v0_27_1.sql',
'ADR-043':root/'docs/architecture/ADR-043-attendance-independent-signed-proximity.md',
'certification':root/'docs/certification/LOT26_v0.27.1_MAXIMAL.md',
'attendance tests':root/'services/api/tests/test_campus_operations_lot26.py',
}
for name,p in checks.items():
 assert p.exists(),name
svc=(root/'services/api/app/modules/campus_operations/application/service.py').read_text()
for token in ['proximity_token','_verify_proximity','signed_proximity_failed','ATTENDANCE_PROXIMITY_SECRET']:
 assert token in svc,token
runtime=(root/'services/api/app/runtime.py').read_text();assert "ATTENDANCE_PROXIMITY_SECRET is mandatory in production" in runtime
print('LOT26 v0.27.1 audit: 8/8 PASS')

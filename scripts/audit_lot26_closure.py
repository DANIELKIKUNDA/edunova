from historical_audit_contracts import release_at_least
from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'migration_0044':(r/'services/api/migrations/0044_campus_operations_complete_v0_27_2.sql').exists(),
'adr_044':(r/'docs/architecture/ADR-044-campus-operations-complete.md').exists(),
'announcements':'create_announcement' in (r/'services/api/app/modules/campus_operations/application/service.py').read_text(),
'absence_workflow':'decide_absence' in (r/'services/api/app/modules/campus_operations/application/service.py').read_text(),
'calendar':'create_event' in (r/'services/api/app/modules/campus_operations/application/service.py').read_text(),
'operations_dashboard':'operations_dashboard' in (r/'services/api/app/modules/campus_operations/application/service.py').read_text(),
'auto_absent':'auto_absent_on_close' in (r/'services/api/app/modules/campus_operations/application/service.py').read_text(),
'notifications':'NotificationIntent' in (r/'services/api/app/modules/campus_operations/application/service.py').read_text(),
'api_routes':'absence-requests' in (r/'services/api/app/modules/campus_operations/api/router.py').read_text(),
'version_api':release_at_least(r, 'api', '0.27.2'),
'version_mobile':release_at_least(r, 'mobile', '0.27.2+56'),
'version_admin':release_at_least(r, 'admin', '0.27.2+56'),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
raise SystemExit(0 if all(checks.values()) else 1)

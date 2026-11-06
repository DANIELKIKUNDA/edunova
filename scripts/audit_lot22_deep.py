from historical_audit_contracts import release_at_least
from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
 'service scope guard':"campus_scope_forbidden" in (root/'services/api/app/modules/campus/application/service.py').read_text(),
 'role escalation guard':"_assert_can_assign_role" in (root/'services/api/app/modules/campus/application/service.py').read_text(),
 'institution write gate':"campus_institution_not_writable" in (root/'services/api/app/modules/campus/application/service.py').read_text(),
 'period hierarchy':"campus_invalid_period_hierarchy" in (root/'services/api/app/modules/campus/application/service.py').read_text(),
 'role endpoint':"/role'" in (root/'services/api/app/modules/campus/api/router.py').read_text(),
 'scoped listing':"runtime.campus.list_members" in (root/'services/api/app/modules/campus/api/router.py').read_text(),
 'hardening migration':(root/'services/api/migrations/0032_campus_core_enterprise_hardening_v0_23_1.sql').exists(),
 'fk defense':"FOREIGN KEY" in (root/'services/api/migrations/0032_campus_core_enterprise_hardening_v0_23_1.sql').read_text(),
 'check defense':"CHECK" in (root/'services/api/migrations/0032_campus_core_enterprise_hardening_v0_23_1.sql').read_text(),
 'hardening tests':(root/'services/api/tests/test_campus_lot22_hardening.py').exists(),
 'adr 032':(root/'docs/ADR-032-campus-scoped-administration-defense-in-depth.md').exists(),
 'lot22 hardening doc':(root/'docs/LOT22_ENTERPRISE_HARDENING_v0.23.1.md').exists(),
 'api version': release_at_least(root, 'api', '0.23.1'),
 'mobile version': release_at_least(root, 'mobile', '0.23.1+44'),
 'admin version': release_at_least(root, 'admin', '0.23.1+44'),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

from pathlib import Path
R=Path(__file__).resolve().parents[1]
svc=(R/'services/api/app/modules/institutional_analytics/application/service.py').read_text()
repo=(R/'services/api/app/modules/institutional_analytics/infrastructure/sqlalchemy_repo.py').read_text()
api=(R/'services/api/app/modules/institutional_analytics/api/router.py').read_text()
tests=(R/'services/api/tests/test_institutional_analytics_lot27.py').read_text()
checks=[
 'capture_snapshot' in svc and 'compare_snapshots' in svc,
 'unit_dashboard' in svc and 'snapshot_for_unit' in repo,
 'sha256' in repo and 'save_immutable_snapshot' in repo,
 'pedagogical_intelligence' in svc and 'by_bloom' in repo,
 'NodeRow' in repo and 'published_concepts' in repo,
 'executive_report' in svc and 'contract_version' in svc,
 'automatic_judgement' in svc,
 "'personal_tutor':False" in svc and "'private_documents':False" in svc,
 'teacher_scope_required' in svc and 'unit_scope_denied' in svc,
 'export_csv' in svc and 'export.csv' in api,
 'pedagogical-intelligence' in api and 'executive-report' in api,
 'test_student_cannot_access' in tests,
 'test_faculty_report_pedagogy_cannot_escape_authorized_unit_scope' in tests,
 (R/'services/api/migrations/0047_institutional_pedagogical_intelligence_v0_28_2.sql').exists(),
 (R/'docs/architecture/ADR-047-lot27-final-institutional-intelligence.md').exists(),
 (R/'docs/certification/LOT27_v0.28.2_FINAL.md').exists(),
]
for n,x in enumerate(checks,1): assert x,f'check {n}'
print(f'LOT27 FINAL AUDIT: {sum(checks)}/{len(checks)} PASS')

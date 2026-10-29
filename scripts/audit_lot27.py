from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
'bounded_context':root/'services/api/app/modules/institutional_analytics/application/service.py',
'read_model':root/'services/api/app/modules/institutional_analytics/infrastructure/sqlalchemy_repo.py',
'api':root/'services/api/app/modules/institutional_analytics/api/router.py',
'migration_0045':root/'services/api/migrations/0045_institutional_analytics_v0_28_0.sql',
'adr_045':root/'docs/architecture/ADR-045-institutional-analytics.md',
'tests':root/'services/api/tests/test_institutional_analytics_lot27.py',
}
for k,p in checks.items():assert p.exists(),k
repo=checks['read_model'].read_text();service=checks['bounded_context'].read_text()
for forbidden in ('app.modules.tutor','app.modules.library','app.modules.study_orchestration','TutorRow','KnowledgeChunkRow'):
 assert forbidden not in repo,f'privacy_boundary:{forbidden}'
for required in ('attendance_rate','submission_rate','pass_rate','completion_rate','syllabus_coverage_rate'):
 assert required in repo,required
assert 'teacher_scope_required' in service and 'CampusRole.STUDENT' not in service
print('LOT27 BASELINE AUDIT: 10/10 PASS')

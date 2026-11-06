from pathlib import Path
p=Path(__file__).resolve().parents[1]
checks={
'migration':(p/'services/api/migrations/0023_question_intelligence_factory_v0_19_3.sql').exists(),
'origin_model':'QuestionOrigin' in (p/'services/api/app/modules/assessment/domain/model.py').read_text(),
'gift':'import_gift' in (p/'services/api/app/modules/assessment/application/service.py').read_text(),
'moodle':'import_moodle_xml' in (p/'services/api/app/modules/assessment/application/service.py').read_text(),
'dedupe':'duplicate_fingerprint' in (p/'services/api/app/modules/assessment/infrastructure/sqlalchemy_repo.py').read_text(),
'bloom':'infer_bloom' in (p/'services/api/app/modules/assessment/application/service.py').read_text(),
'variant_contract':'verbatim_copy' in (p/'services/api/app/modules/assessment/application/service.py').read_text(),
'api':'question-factory/import' in (p/'services/api/app/modules/assessment/api/router.py').read_text(),
'studio':(p/'apps/admin/lib/src/features/editorial/question_factory_page.dart').exists(),
'adr':(p/'docs/architecture/ADR-023-question-intelligence-factory.md').exists(),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
assert all(checks.values());print(f'{sum(checks.values())}/{len(checks)} PASS')

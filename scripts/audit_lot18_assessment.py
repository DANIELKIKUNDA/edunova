from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={'domain':r/'services/api/app/modules/assessment/domain/model.py','service':r/'services/api/app/modules/assessment/application/service.py','repo':r/'services/api/app/modules/assessment/infrastructure/sqlalchemy_repo.py','api':r/'services/api/app/modules/assessment/api/router.py','migration20':r/'services/api/migrations/0020_assessment_exam_engine_v0_19_0.sql','migration21':r/'services/api/migrations/0021_assessment_hardening_v0_19_1.sql','ui':r/'apps/mobile/lib/src/features/assessment/presentation/exam_simulator_page.dart','adr':r/'docs/architecture/ADR-021-assessment-exam-simulation.md','tests':r/'services/api/tests/test_assessment_lot18.py'}
for k,p in checks.items():assert p.exists(),k
s=(checks['service']).read_text();assert 'approved_only' in s and 'assessment_version_conflict' in s and 'source_pages' in s
ui=checks['ui'].read_text();assert 'Examen blanc' in ui and 'À revoir' in ui and 'From Volcano Tech' in ui
print(f'{len(checks)+3}/{len(checks)+3} PASS')

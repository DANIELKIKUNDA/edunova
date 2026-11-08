from historical_audit_contracts import release_at_least
from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'api 0.16.1':release_at_least(r, 'api', '0.16.1'),
'mobile 0.16.1+26':release_at_least(r, 'mobile', '0.16.1+26'),
'admin 0.16.1+26':release_at_least(r, 'admin', '0.16.1+26'),
'migration 0015':(r/'services/api/migrations/0015_learning_experience_hardening_v0_16_1.sql').exists(),
'exam plans':'create_exam_plan' in (r/'services/api/app/modules/learning_experience/application/service.py').read_text(),
'error review':'review_error' in (r/'services/api/app/modules/learning_experience/application/service.py').read_text(),
'recommendations':'def recommendations' in (r/'services/api/app/modules/learning_experience/application/service.py').read_text(),
'constraints':'ck_learning_mastery_stage' in (r/'services/api/migrations/0015_learning_experience_hardening_v0_16_1.sql').read_text(),
'exam UI':all(token in (r/'apps/mobile/lib/src/features/study_workspace/presentation/study_workspace_page.dart').read_text() for token in ['Exam Mode', "Text('Configurer')", 'onPressed:onTap', '_ExamCard']),
'mastery UI':'Progression de maîtrise' in (r/'apps/mobile/lib/src/features/study_workspace/presentation/study_workspace_page.dart').read_text(),
'machine gate':(r/'docs/LOT15_MACHINE_CERTIFICATION_v0.16.1.md').exists(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'api 0.16.1':'version="0.16.1"' in (r/'services/api/app/main.py').read_text(),
'mobile 0.16.1+26':'version: 0.16.1+26' in (r/'apps/mobile/pubspec.yaml').read_text(),
'admin 0.16.1+26':'version: 0.16.1+26' in (r/'apps/admin/pubspec.yaml').read_text(),
'migration 0015':(r/'services/api/migrations/0015_learning_experience_hardening_v0_16_1.sql').exists(),
'exam plans':'create_exam_plan' in (r/'services/api/app/modules/learning_experience/application/service.py').read_text(),
'error review':'review_error' in (r/'services/api/app/modules/learning_experience/application/service.py').read_text(),
'recommendations':'def recommendations' in (r/'services/api/app/modules/learning_experience/application/service.py').read_text(),
'constraints':'ck_learning_mastery_stage' in (r/'services/api/migrations/0015_learning_experience_hardening_v0_16_1.sql').read_text(),
'exam UI':'Configurer Exam Mode' in (r/'apps/mobile/lib/src/features/study_workspace/presentation/study_workspace_page.dart').read_text(),
'mastery UI':'Progression de maîtrise' in (r/'apps/mobile/lib/src/features/study_workspace/presentation/study_workspace_page.dart').read_text(),
'machine gate':(r/'docs/LOT15_MACHINE_CERTIFICATION_v0.16.1.md').exists(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

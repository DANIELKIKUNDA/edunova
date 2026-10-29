from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
'api_0_16':'version="0.16.0"' in (root/'services/api/app/main.py').read_text(),
'migration_0014':(root/'services/api/migrations/0014_learning_experience_v0_16_0.sql').exists(),
'hex_domain':(root/'services/api/app/modules/learning_experience/domain/model.py').exists(),
'hex_service':(root/'services/api/app/modules/learning_experience/application/service.py').exists(),
'hex_repo':(root/'services/api/app/modules/learning_experience/infrastructure/sqlalchemy_repo.py').exists(),
'api_router':(root/'services/api/app/modules/learning_experience/api/router.py').exists(),
'study_modes':'EXAM' in (root/'services/api/app/modules/learning_experience/domain/model.py').read_text(),
'mastery_semantics':'MASTERED' in (root/'services/api/app/modules/learning_experience/domain/model.py').read_text(),
'spaced_repetition':'next_spaced_review' in (root/'services/api/app/modules/learning_experience/domain/model.py').read_text(),
'error_bank':'learning_error_bank' in (root/'services/api/migrations/0014_learning_experience_v0_16_0.sql').read_text(),
'one_open_session':'ux_learning_one_open_session' in (root/'services/api/migrations/0014_learning_experience_v0_16_0.sql').read_text(),
'optimistic_lock':'expected_version' in (root/'services/api/app/modules/learning_experience/application/service.py').read_text(),
'home_resume':"'/home'" in (root/'services/api/app/modules/learning_experience/api/router.py').read_text(),
'workspace_ui':(root/'apps/mobile/lib/src/features/study_workspace/presentation/study_workspace_page.dart').exists(),
'responsive_ui':'width>=900' in (root/'apps/mobile/lib/src/features/study_workspace/presentation/study_workspace_page.dart').read_text(),
'focus_mode':'Mode concentration' in (root/'apps/mobile/lib/src/features/study_workspace/presentation/study_workspace_page.dart').read_text(),
'offline_affordance':'Hors connexion' in (root/'apps/mobile/lib/src/features/study_workspace/presentation/study_workspace_page.dart').read_text(),
'mobile_version':'version: 0.16.0+25' in (root/'apps/mobile/pubspec.yaml').read_text(),
'tests':(root/'services/api/tests/test_learning_experience_lot15.py').exists(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

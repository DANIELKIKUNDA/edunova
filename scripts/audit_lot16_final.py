from historical_audit_contracts import release_at_least
from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'v0.17.1 API':release_at_least(r, 'api', '0.17.1'),
'adaptive v2':'adaptive-v2' in (r/'services/api/app/modules/adaptive_learning/domain/model.py').read_text(),
'confidence band':'ConfidenceBand' in (r/'services/api/app/modules/adaptive_learning/domain/model.py').read_text(),
'knowledge gaps':'KnowledgeGap' in (r/'services/api/app/modules/adaptive_learning/domain/model.py').read_text(),
'exam readiness':'ExamReadiness' in (r/'services/api/app/modules/adaptive_learning/domain/model.py').read_text(),
'exam focus':'exam_focus' in (r/'services/api/app/modules/adaptive_learning/application/service.py').read_text(),
'evidence':'evidence' in (r/'services/api/app/modules/adaptive_learning/application/service.py').read_text(),
'history endpoint':"'/history'" in (r/'services/api/app/modules/adaptive_learning/api/router.py').read_text(),
'history repo':'def history' in (r/'services/api/app/modules/adaptive_learning/infrastructure/sqlalchemy_repo.py').read_text(),
'migration 0017':(r/'services/api/migrations/0017_adaptive_learning_hardening_v0_17_1.sql').exists(),
'mobile 0.17.1':release_at_least(r, 'mobile', '0.17.1+29'),
'admin 0.17.1':release_at_least(r, 'admin', '0.17.1+29'),
'premium metrics':'Confiance' in (r/'apps/mobile/lib/src/features/adaptive_learning/presentation/adaptive_learning_page.dart').read_text(),
'exam UI':'Examen en vue' in (r/'apps/mobile/lib/src/features/adaptive_learning/presentation/adaptive_learning_page.dart').read_text(),
'gaps UI':'Lacunes' in (r/'apps/mobile/lib/src/features/adaptive_learning/presentation/adaptive_learning_page.dart').read_text(),
'explainability UI':'Pourquoi cette recommandation' in (r/'apps/mobile/lib/src/features/adaptive_learning/presentation/adaptive_learning_page.dart').read_text(),
'Volcano Tech':'From Volcano Tech' in (r/'apps/mobile/lib/src/features/adaptive_learning/presentation/adaptive_learning_page.dart').read_text(),
'final tests':(r/'services/api/tests/test_adaptive_learning_final.py').exists(),
'final docs':(r/'docs/LOT16_FINAL_v0.17.1.md').exists(),
'no mastery certainty':'pas une prédiction' in (r/'apps/mobile/lib/src/features/adaptive_learning/presentation/adaptive_learning_page.dart').read_text(),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

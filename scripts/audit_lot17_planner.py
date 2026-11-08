from historical_audit_contracts import release_at_least
from pathlib import Path
R=Path(__file__).resolve().parents[1]
checks={
'api_0_18':release_at_least(R, 'api', '0.18.1'),
'router': '/v1/study-planner' in (R/'services/api/app/main.py').read_text(),
'bounded_context':(R/'services/api/app/modules/study_orchestration/application/service.py').exists(),
'migration_0018':(R/'services/api/migrations/0018_adaptive_study_planner_v0_18_0.sql').exists(),
'preferences':'daily_limit_minutes' in (R/'services/api/app/modules/study_orchestration/domain/model.py').read_text(),
'busy_blocks':'BusyBlock' in (R/'services/api/app/modules/study_orchestration/domain/model.py').read_text(),
'capacity_guard':'capacity' in (R/'services/api/app/modules/study_orchestration/application/service.py').read_text(),
'overflow':'overflow=' in (R/'services/api/app/modules/study_orchestration/application/service.py').read_text(),
'priority':'candidates.sort' in (R/'services/api/app/modules/study_orchestration/application/service.py').read_text(),
'optimistic_lock':'planner_version_conflict' in (R/'services/api/app/modules/study_orchestration/application/service.py').read_text(),
'replan':'replan_from_today' in (R/'services/api/app/modules/study_orchestration/application/service.py').read_text(),
'weekend':'weekend_enabled' in (R/'services/api/app/modules/study_orchestration/application/service.py').read_text(),
'ui_route':"/study-planner" in (R/'apps/mobile/lib/src/app/router.dart').read_text(),
'ui_day_week':'Vue semaine' in (R/'apps/mobile/lib/src/features/study_planner/presentation/adaptive_study_planner_page.dart').read_text(),
'ui_explain':'Pourquoi ce plan ?' in (R/'apps/mobile/lib/src/features/study_planner/presentation/adaptive_study_planner_page.dart').read_text(),
'ui_offline':'hors connexion' in (R/'apps/mobile/lib/src/features/study_planner/presentation/adaptive_study_planner_page.dart').read_text(),
'ui_non_punitive':'Une journée manquée' in (R/'apps/mobile/lib/src/features/study_planner/presentation/adaptive_study_planner_page.dart').read_text(),
'brand':'From Volcano Tech' in (R/'apps/mobile/lib/src/features/study_planner/presentation/adaptive_study_planner_page.dart').read_text(),
'lot17_tests':(R/'services/api/tests/test_study_orchestration_lot17.py').exists(),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

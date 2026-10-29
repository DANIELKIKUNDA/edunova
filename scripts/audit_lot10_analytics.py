from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
checks={
  'route': "path: '/analytics'" in (ROOT/'apps/mobile/lib/src/app/router.dart').read_text(),
  'home_integration': 'class _ProgressInsightCard' in (ROOT/'apps/mobile/lib/src/features/home/presentation/home_page.dart').read_text(),
  'drift_v16': 'int get schemaVersion => 16;' in (ROOT/'apps/mobile/lib/src/core/database/app_database.dart').read_text(),
  'snapshots': 'LocalAnalyticsCourseSnapshots' in (ROOT/'apps/mobile/lib/src/core/database/app_database.dart').read_text(),
  'feedback': 'LocalAnalyticsRecommendationFeedback' in (ROOT/'apps/mobile/lib/src/core/database/app_database.dart').read_text(),
  'local_engine': 'class LocalAnalyticsEngine' in (ROOT/'apps/mobile/lib/src/features/analytics/application/analytics_engine.dart').read_text(),
  'privacy_adr': (ROOT/'docs/ADR-0012-local-first-learning-analytics.md').exists(),
  'backend_engine': 'class AnalyticsEngine' in (ROOT/'services/api/app/modules/analytics/domain/engine.py').read_text(),
  'disclaimer': 'ne prédisent pas ta note' in (ROOT/'services/api/app/modules/analytics/domain/engine.py').read_text(),
  'evidence': 'AnalyticsEvidence' in (ROOT/'services/api/app/modules/analytics/domain/model.py').read_text(),
}
for name,ok in checks.items(): print(f'{name}: {"PASS" if ok else "FAIL"}')
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('failed: '+','.join(failed))
print(f'LOT10 static audit: {len(checks)}/{len(checks)} PASS')

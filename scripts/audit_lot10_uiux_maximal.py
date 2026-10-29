from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
page=(ROOT/'apps/mobile/lib/src/features/analytics/presentation/analytics_page.dart').read_text()
home=(ROOT/'apps/mobile/lib/src/features/home/presentation/home_page.dart').read_text()
domain=(ROOT/'apps/mobile/lib/src/features/analytics/domain/analytics.dart').read_text()
repo=(ROOT/'apps/mobile/lib/src/features/analytics/infrastructure/drift_analytics_repository.dart').read_text()
engine=(ROOT/'apps/mobile/lib/src/features/analytics/application/analytics_engine.dart').read_text()
providers=(ROOT/'apps/mobile/lib/src/core/di/providers.dart').read_text()
router=(ROOT/'apps/mobile/lib/src/app/router.dart').read_text()
pubspec=(ROOT/'apps/mobile/pubspec.yaml').read_text()
checks={
  'version_mobile_0111': 'version: 0.11.1+15' in pubspec,
  'analytics_route': "path: '/analytics'" in router,
  'page_body_constrained': 'EduNovaPageBody' in page,
  'responsive_desktop_split': 'constraints.maxWidth >= 980' in page,
  'responsive_metrics': 'c.maxWidth >= 940 ? 4' in page,
  'activity_14d_domain': 'class DailyLearningPoint' in domain and 'activity14d' in domain,
  'activity_14d_repo': 'activity14d.add(DailyLearningPoint' in repo,
  'activity_timeline_ui': "Ton rythme sur 14 jours" in page,
  'evidence_banner': 'class _EvidenceBanner' in page,
  'evidence_gauge': 'class _EvidenceGauge' in page,
  'updated_at_visible': 'mis à jour il y a' in page,
  'semantic_hero': 'Semantics(' in page and 'Analyse $updated' in page,
  'semantic_metrics': "label: '$label, $value, $caption'" in page,
  'semantic_chart': 'questions quiz' in page and 'flashcards' in page,
  'recommendation_priority': 'Priorité haute' in page and 'À faire bientôt' in page,
  'recommendation_explanation': 'Pourquoi :' in page,
  'recommendation_snooze': 'Me le rappeler demain' in page,
  'recommendation_start_not_false_completed': 'RecommendationFeedbackState.completed' not in page,
  'course_drilldown': 'class _CourseDetailSheet' in page,
  'course_four_dimensions': all(x in page for x in ['Cours couvert','Maîtrise quiz','Flashcards','Erreurs récupérées']),
  'readiness_disclaimer': 'ne prédit ni ta note ni ta réussite' in page,
  'methodology_expandable': 'Comment EduNova calcule ces tendances ?' in page,
  'methodology_local_first': 'sans IA payante' in page and 'Calcul local-first' in page,
  'empty_state_analytics': 'La tendance apparaîtra bientôt' in page,
  'loading_skeleton': 'class _AnalyticsLoading' in page,
  'error_state': 'Impossible de calculer ta progression' in page,
  'refresh_indicator': 'RefreshIndicator' in page,
  'home_progress_card': 'class _ProgressInsightCard' in home,
  'home_uses_analytics_provider': 'ref.watch(analyticsReportProvider)' in home,
  'home_no_static_progress_cta': 'Voir ma progression' not in home,
  'course_titles_in_deeplinks': 'Uri.encodeComponent(c.title)' in engine,
  'course_insight_dimensions_domain': all(x in domain for x in ['coverage','quizMastery','flashcardMastery','weaknessRecovery']),
  'course_insight_context': all(x in domain for x in ['openErrors','overdueFlashcards','daysToNextAssessment','studyMinutes7d']),
  'generated_at_report': 'required this.generatedAt' in domain,
  'local_engine_no_ai': 'class LocalAnalyticsEngine' in engine,
  'provider_local_engine': 'analyticsEngineProvider' in providers,
  'max_recommendations_5': 'if(selected.length==5)break' in engine,
  'recommendation_diversity': '(count[k]??0)>=2' in engine,
  'limited_evidence_caution': 'AnalyticsEvidence.limited' in engine,
  'no_grade_prediction_engine': 'ne prédisent pas ta note' in engine,
  'dark_theme_friendly': 'Theme.of(context).colorScheme' in page,
  'no_hardcoded_demo_course': all(x not in page for x in ['Biochimie — 48','Physiologie — 61']),
  'touch_target_buttons': 'FilledButton.icon' in page,
  'bottom_sheet_safe_area': 'useSafeArea: true' in page,
  'course_action_plan': "context.push('/revision')" in page,
  'status_pills': 'StatusPill' in page,
  'progress_ring': 'ProgressRing' in page,
  'chart_accessible_labels': 'Semantics(' in page and 'minutes étudiées' in page,
  'responsive_readability': 'maxWidth >= 980' in page,
  'privacy_statement': 'tes documents personnels ne sont pas envoyés' in page,
  'snapshot_persistence': 'LocalAnalyticsCourseSnapshots' in (ROOT/'apps/mobile/lib/src/core/database/app_database.dart').read_text(),
  'feedback_persistence': 'LocalAnalyticsRecommendationFeedback' in (ROOT/'apps/mobile/lib/src/core/database/app_database.dart').read_text(),
}
for name,ok in checks.items():
    print(f'{name}: {"PASS" if ok else "FAIL"}')
failed=[k for k,v in checks.items() if not v]
if failed:
    raise SystemExit('failed: '+','.join(failed))
print(f'LOT10 UI/UX maximal static audit: {len(checks)}/{len(checks)} PASS')

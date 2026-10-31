import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../../../core/theme/tokens.dart';
import '../../../shared/presentation/widgets/premium_surface.dart';
import '../../../shared/presentation/widgets/progress_ring.dart';
import '../domain/analytics.dart';

class AnalyticsPage extends ConsumerWidget {
  const AnalyticsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final reportAsync = ref.watch(analyticsReportProvider);
    final feedback = ref.watch(analyticsFeedbackProvider).valueOrNull ?? const <RecommendationFeedback>[];
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ma progression'),
        actions: [
          IconButton(
            tooltip: 'Actualiser les analyses',
            onPressed: () {
              ref.invalidate(analyticsSnapshotProvider);
              ref.invalidate(analyticsReportProvider);
            },
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: reportAsync.when(
        loading: () => const _AnalyticsLoading(),
        error: (_, __) => EduNovaPageBody(
          child: EmptyStateCard(
            icon: Icons.error_outline_rounded,
            title: 'Impossible de calculer ta progression',
            message: 'Tes données restent sur cet appareil. Réessaie dans un instant.',
            action: FilledButton(
              onPressed: () => ref.invalidate(analyticsReportProvider),
              child: const Text('Réessayer'),
            ),
          ),
        ),
        data: (report) => RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(analyticsSnapshotProvider);
            ref.invalidate(analyticsReportProvider);
            await ref.read(analyticsReportProvider.future);
          },
          child: _AnalyticsBody(
            report: report,
            feedback: feedback,
            onFeedback: (f) async {
              await ref.read(analyticsRepositoryProvider).saveFeedback(f);
              ref.invalidate(analyticsFeedbackProvider);
            },
          ),
        ),
      ),
    );
  }
}

class _AnalyticsLoading extends StatelessWidget {
  const _AnalyticsLoading();
  @override
  Widget build(BuildContext context) {
    return EduNovaPageBody(
      child: Column(children: [
        const SkeletonLine(height: 176),
        const SizedBox(height: 14),
        LayoutBuilder(builder: (_, c) {
          final columns = c.maxWidth >= 900 ? 4 : c.maxWidth >= 560 ? 2 : 1;
          return GridView.count(
            crossAxisCount: columns,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 10,
            crossAxisSpacing: 10,
            childAspectRatio: columns == 1 ? 3.2 : 2.0,
            children: List.generate(4, (_) => const PremiumPanel(child: SkeletonLine(height: 54))),
          );
        }),
        const SizedBox(height: 14),
        const PremiumPanel(child: Column(children: [SkeletonLine(height: 18), SizedBox(height: 18), SkeletonLine(height: 112)])),
      ]),
    );
  }
}

class _AnalyticsBody extends StatelessWidget {
  const _AnalyticsBody({required this.report, required this.feedback, required this.onFeedback});
  final AnalyticsReport report;
  final List<RecommendationFeedback> feedback;
  final Future<void> Function(RecommendationFeedback) onFeedback;

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final hidden = <String, RecommendationFeedback>{
      for (final f in feedback)
        if (f.state != RecommendationFeedbackState.snoozed || (f.snoozedUntil?.isAfter(now) ?? false)) f.recommendationId: f,
    };
    final recommendations = report.recommendations.where((r) => !hidden.containsKey(r.id)).toList();

    return EduNovaPageBody(
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 52),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        _MomentumHero(report: report),
        const SizedBox(height: 12),
        _EvidenceBanner(evidence: report.evidence),
        const SizedBox(height: 16),
        _MetricsGrid(report: report),
        const SizedBox(height: 18),
        _ActivityTimeline(points: report.activity14d, studyTrend: report.studyTime),
        const SizedBox(height: 24),
        LayoutBuilder(builder: (context, constraints) {
          if (constraints.maxWidth >= 980) {
            return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(
                flex: 6,
                child: _RecommendationsSection(
                  recommendations: recommendations,
                  onFeedback: onFeedback,
                ),
              ),
              const SizedBox(width: 18),
              Expanded(flex: 5, child: _CourseInsightsSection(courses: report.courseInsights)),
            ]);
          }
          return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            _RecommendationsSection(recommendations: recommendations, onFeedback: onFeedback),
            const SizedBox(height: 26),
            _CourseInsightsSection(courses: report.courseInsights),
          ]);
        }),
        const SizedBox(height: 22),
        _MethodologyCard(report: report),
      ]),
    );
  }
}

class _MomentumHero extends StatelessWidget {
  const _MomentumHero({required this.report});
  final AnalyticsReport report;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (icon, title, subtitle) = switch (report.momentum) {
      AnalyticsTrend.improving => (Icons.trending_up_rounded, 'Ton rythme progresse', 'Tes signaux récents vont dans le bon sens.'),
      AnalyticsTrend.declining => (Icons.tune_rounded, 'Ton rythme mérite un ajustement', 'EduNova te propose des actions plus réalistes et ciblées.'),
      AnalyticsTrend.stable => (Icons.horizontal_rule_rounded, 'Ton rythme est stable', 'Continue régulièrement et consolide les points les moins maîtrisés.'),
    };
    final updated = _relativeUpdateLabel(report.generatedAt, DateTime.now());

    return Semantics(
      container: true,
      label: '$title. $subtitle. Analyse $updated.',
      child: Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: [scheme.primary, Color.lerp(scheme.primary, EduNovaColors.secondary, .46)!]),
          borderRadius: BorderRadius.circular(EduNovaRadius.xl),
          boxShadow: [BoxShadow(color: scheme.primary.withValues(alpha: .18), blurRadius: 30, offset: const Offset(0, 13))],
        ),
        child: LayoutBuilder(builder: (context, c) {
          final compact = c.maxWidth < 520;
          final content = Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Container(
                width: 58,
                height: 58,
                decoration: BoxDecoration(color: scheme.onPrimary.withValues(alpha: .14), shape: BoxShape.circle),
                child: Icon(icon, color: scheme.onPrimary, size: 31),
              ),
              const SizedBox(width: 14),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(title, style: TextStyle(color: scheme.onPrimary, fontSize: 22, height: 1.12, fontWeight: FontWeight.w900)),
                const SizedBox(height: 5),
                Text(subtitle, style: TextStyle(color: scheme.onPrimary.withValues(alpha: .9), height: 1.35)),
              ])),
            ]),
            const SizedBox(height: 18),
            Wrap(spacing: 8, runSpacing: 8, children: [
              _HeroPill(icon: Icons.local_fire_department_outlined, label: '${report.streakDays} j de série'),
              _HeroPill(icon: Icons.event_available_outlined, label: '${report.activeDays7d}/7 jours actifs'),
              if (report.recommendations.isNotEmpty) _HeroPill(icon: Icons.bolt_rounded, label: '${report.recommendedMinutes} min recommandées'),
              _HeroPill(icon: Icons.update_rounded, label: updated),
            ]),
          ]);
          return compact ? content : Row(children: [Expanded(child: content), const SizedBox(width: 20), _EvidenceGauge(evidence: report.evidence)]);
        }),
      ),
    );
  }

  static String _relativeUpdateLabel(DateTime generatedAt, DateTime now) {
    final minutes = now.difference(generatedAt).inMinutes.abs();
    if (minutes <= 1) return 'mis à jour maintenant';
    if (minutes < 60) return 'mis à jour il y a $minutes min';
    final hours = minutes ~/ 60;
    return 'mis à jour il y a $hours h';
  }
}

class _HeroPill extends StatelessWidget {
  const _HeroPill({required this.icon, required this.label});
  final IconData icon;
  final String label;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(color: scheme.onPrimary.withValues(alpha: .12), borderRadius: BorderRadius.circular(EduNovaRadius.pill)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 15, color: scheme.onPrimary), const SizedBox(width: 6), Text(label, style: TextStyle(color: scheme.onPrimary, fontSize: 12, fontWeight: FontWeight.w800))]),
    );
  }
}

class _EvidenceGauge extends StatelessWidget {
  const _EvidenceGauge({required this.evidence});
  final AnalyticsEvidence evidence;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (value, label) = switch (evidence) {
      AnalyticsEvidence.strong => (.95, 'Données solides'),
      AnalyticsEvidence.moderate => (.62, 'Données modérées'),
      AnalyticsEvidence.limited => (.30, 'Données limitées'),
    };
    return Container(
      width: 128,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: scheme.onPrimary.withValues(alpha: .10), borderRadius: BorderRadius.circular(EduNovaRadius.lg)),
      child: Column(children: [
        SizedBox(width: 58, height: 58, child: CircularProgressIndicator(value: value, strokeWidth: 6, strokeCap: StrokeCap.round, backgroundColor: scheme.onPrimary.withValues(alpha: .16), color: scheme.onPrimary)),
        const SizedBox(height: 9),
        Text(label, textAlign: TextAlign.center, style: TextStyle(color: scheme.onPrimary, fontSize: 11, fontWeight: FontWeight.w900)),
      ]),
    );
  }
}

class _EvidenceBanner extends StatelessWidget {
  const _EvidenceBanner({required this.evidence});
  final AnalyticsEvidence evidence;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (icon, title, body) = switch (evidence) {
      AnalyticsEvidence.strong => (Icons.verified_outlined, 'Analyse bien étayée', 'Tu as suffisamment d’activité récente pour lire les tendances avec confiance.'),
      AnalyticsEvidence.moderate => (Icons.insights_outlined, 'Analyse en consolidation', 'Les tendances sont utiles, mais elles gagneront en précision avec quelques jours supplémentaires.'),
      AnalyticsEvidence.limited => (Icons.science_outlined, 'Encore peu de données', 'EduNova reste volontairement prudente et évite les conclusions fortes pour le moment.'),
    };
    return PremiumPanel(
      padding: const EdgeInsets.all(12),
      child: Row(children: [
        Container(width: 38, height: 38, decoration: BoxDecoration(color: scheme.primaryContainer, shape: BoxShape.circle), child: Icon(icon, color: scheme.primary, size: 20)),
        const SizedBox(width: 10),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontWeight: FontWeight.w900)), const SizedBox(height: 2), Text(body, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5, height: 1.3))])),
      ]),
    );
  }
}

class _MetricsGrid extends StatelessWidget {
  const _MetricsGrid({required this.report});
  final AnalyticsReport report;
  @override
  Widget build(BuildContext context) {
    final cards = <Widget>[
      _MetricCard(icon: Icons.timer_outlined, label: 'Étude · 7 jours', value: '${report.studyTime.current.round()} min', caption: _deltaLabel(report.studyTime.delta, 'min'), trend: report.studyTime.direction),
      _MetricCard(icon: Icons.calendar_view_week_rounded, label: 'Jours actifs', value: '${report.activeDays7d} / 7', caption: 'Série actuelle : ${report.streakDays} j', trend: report.activeDays7d >= 5 ? AnalyticsTrend.improving : AnalyticsTrend.stable),
      _MetricCard(icon: Icons.fact_check_outlined, label: 'Planning réalisé', value: report.planAdherence7d == null ? '—' : '${(report.planAdherence7d! * 100).round()} %', caption: report.planAdherence7d == null ? 'Pas encore de planning mesurable' : 'Mesure le temps réellement suivi', trend: report.planAdherence7d == null ? AnalyticsTrend.stable : report.planAdherence7d! >= .7 ? AnalyticsTrend.improving : report.planAdherence7d! < .5 ? AnalyticsTrend.declining : AnalyticsTrend.stable),
      if (report.quizAccuracy != null) _MetricCard(icon: Icons.quiz_outlined, label: 'Quiz · 7 jours', value: '${(report.quizAccuracy!.current * 100).round()} %', caption: _deltaLabel(report.quizAccuracy!.delta * 100, 'pts'), trend: report.quizAccuracy!.direction),
    ];
    return LayoutBuilder(builder: (_, c) {
      final columns = c.maxWidth >= 940 ? 4 : c.maxWidth >= 560 ? 2 : 1;
      return GridView.count(
        crossAxisCount: columns,
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        mainAxisSpacing: 10,
        crossAxisSpacing: 10,
        childAspectRatio: columns == 1 ? 3.15 : columns == 2 ? 2.25 : 1.75,
        children: cards,
      );
    });
  }

  static String _deltaLabel(double delta, String unit) {
    if (delta.abs() < .5) return 'stable vs semaine précédente';
    final sign = delta > 0 ? '+' : '';
    return '$sign${delta.round()} $unit vs semaine précédente';
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.icon, required this.label, required this.value, required this.caption, required this.trend});
  final IconData icon;
  final String label, value, caption;
  final AnalyticsTrend trend;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final trendIcon = trend == AnalyticsTrend.improving ? Icons.north_east_rounded : trend == AnalyticsTrend.declining ? Icons.south_east_rounded : Icons.east_rounded;
    final trendColor = trend == AnalyticsTrend.declining ? EduNovaColors.accent : trend == AnalyticsTrend.improving ? EduNovaColors.success : scheme.onSurfaceVariant;
    return Semantics(
      label: '$label, $value, $caption',
      child: PremiumPanel(
        padding: const EdgeInsets.all(14),
        child: Row(children: [
          CircleAvatar(backgroundColor: scheme.primaryContainer, child: Icon(icon, color: scheme.primary)),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
            Text(label, style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w700, fontSize: 12)),
            const SizedBox(height: 3),
            Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
            const SizedBox(height: 2),
            Text(caption, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 11.5, height: 1.22)),
          ])),
          Container(width: 34, height: 34, decoration: BoxDecoration(color: trendColor.withValues(alpha: .10), shape: BoxShape.circle), child: Icon(trendIcon, color: trendColor, size: 18)),
        ]),
      ),
    );
  }
}

class _ActivityTimeline extends StatelessWidget {
  const _ActivityTimeline({required this.points, required this.studyTrend});
  final List<DailyLearningPoint> points;
  final TrendMetric studyTrend;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    if (points.isEmpty) {
      return const EmptyStateCard(icon: Icons.show_chart_rounded, title: 'La tendance apparaîtra bientôt', message: 'Quelques jours d’activité suffisent pour visualiser ton rythme de travail.');
    }
    final maxMinutes = points.fold<int>(1, (m, p) => p.studyMinutes > m ? p.studyMinutes : m);
    final delta = studyTrend.delta;
    return PremiumPanel(
      padding: const EdgeInsets.all(18),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Ton rythme sur 14 jours', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 3),
            Text('Chaque barre représente le temps étudié. Le point indique une journée active.', style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5)),
          ])),
          const SizedBox(width: 10),
          StatusPill(icon: delta > 0 ? Icons.north_east_rounded : delta < 0 ? Icons.south_east_rounded : Icons.east_rounded, label: delta.abs() < .5 ? 'stable' : '${delta > 0 ? '+' : ''}${delta.round()} min', tone: delta < 0 ? EduNovaColors.accent : delta > 0 ? EduNovaColors.success : scheme.primary),
        ]),
        const SizedBox(height: 20),
        SizedBox(
          height: 126,
          child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
            for (var i = 0; i < points.length; i++)
              Expanded(child: _ActivityBar(point: points[i], maxMinutes: maxMinutes, showLabel: i == 0 || i == 6 || i == points.length - 1)),
          ]),
        ),
      ]),
    );
  }
}

class _ActivityBar extends StatelessWidget {
  const _ActivityBar({required this.point, required this.maxMinutes, required this.showLabel});
  final DailyLearningPoint point;
  final int maxMinutes;
  final bool showLabel;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final ratio = point.studyMinutes <= 0 ? 0.04 : (point.studyMinutes / maxMinutes).clamp(.08, 1.0).toDouble();
    const weekdays = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];
    return Semantics(
      label: '${point.day.day}/${point.day.month}, ${point.studyMinutes} minutes étudiées, ${point.quizQuestions} questions quiz, ${point.flashcardsReviewed} flashcards',
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 2),
        child: Column(mainAxisAlignment: MainAxisAlignment.end, children: [
          Expanded(
            child: Align(
              alignment: Alignment.bottomCenter,
              child: FractionallySizedBox(
                heightFactor: ratio,
                child: Container(
                  width: 12,
                  decoration: BoxDecoration(
                    color: point.active ? scheme.primary : scheme.outlineVariant.withValues(alpha: .55),
                    borderRadius: BorderRadius.circular(99),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 5),
          Container(width: 5, height: 5, decoration: BoxDecoration(color: point.active ? EduNovaColors.success : scheme.outlineVariant, shape: BoxShape.circle)),
          const SizedBox(height: 4),
          Text(showLabel ? '${weekdays[point.day.weekday - 1]}${point.day.day}' : '', style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 9.5, fontWeight: FontWeight.w700)),
        ]),
      ),
    );
  }
}

class _RecommendationsSection extends StatelessWidget {
  const _RecommendationsSection({required this.recommendations, required this.onFeedback});
  final List<StudyRecommendation> recommendations;
  final Future<void> Function(RecommendationFeedback) onFeedback;

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      _SectionHeader(title: 'À faire maintenant', subtitle: recommendations.isEmpty ? 'Aucune action urgente détectée.' : '${recommendations.length} action${recommendations.length > 1 ? 's' : ''} classée${recommendations.length > 1 ? 's' : ''} par utilité'),
      const SizedBox(height: 10),
      if (recommendations.isEmpty)
        const EmptyStateCard(icon: Icons.check_circle_outline_rounded, title: 'Rien d’urgent', message: 'Continue ton rythme. EduNova fera réapparaître une recommandation lorsqu’elle aura une vraie valeur.')
      else
        ...recommendations.map((r) => Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: _RecommendationCard(
            recommendation: r,
            onNow: () => context.push(r.deepLink),
            onLater: () => onFeedback(RecommendationFeedback(recommendationId: r.id, state: RecommendationFeedbackState.snoozed, snoozedUntil: DateTime.now().add(const Duration(days: 1)), updatedAt: DateTime.now())),
            onDismiss: () => onFeedback(RecommendationFeedback(recommendationId: r.id, state: RecommendationFeedbackState.dismissed, updatedAt: DateTime.now())),
          ),
        )),
    ]);
  }
}

class _RecommendationCard extends StatelessWidget {
  const _RecommendationCard({required this.recommendation, required this.onNow, required this.onLater, required this.onDismiss});
  final StudyRecommendation recommendation;
  final VoidCallback onNow, onLater, onDismiss;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (priorityLabel, tone) = recommendation.priorityScore >= 82 ? ('Priorité haute', EduNovaColors.danger) : recommendation.priorityScore >= 62 ? ('À faire bientôt', EduNovaColors.accent) : ('À consolider', scheme.primary);
    final icon = switch (recommendation.kind) {
      RecommendationKind.assessmentFocus => Icons.event_available_rounded,
      RecommendationKind.recoverErrors => Icons.rule_rounded,
      RecommendationKind.quizDrill => Icons.quiz_rounded,
      RecommendationKind.flashcardReview => Icons.style_rounded,
      RecommendationKind.continueCourse => Icons.menu_book_rounded,
      RecommendationKind.planRecovery => Icons.tune_rounded,
    };
    return Semantics(
      container: true,
      label: '${recommendation.title}. $priorityLabel. ${recommendation.recommendedMinutes} minutes. ${recommendation.reason}',
      child: PremiumPanel(
        padding: EdgeInsets.zero,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(15, 15, 10, 12),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(width: 42, height: 42, decoration: BoxDecoration(color: tone.withValues(alpha: .11), borderRadius: BorderRadius.circular(14)), child: Icon(icon, color: tone, size: 22)),
              const SizedBox(width: 11),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Wrap(spacing: 7, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
                  StatusPill(icon: Icons.schedule_rounded, label: '${recommendation.recommendedMinutes} min', tone: scheme.primary),
                  StatusPill(icon: Icons.flag_outlined, label: priorityLabel, tone: tone),
                ]),
                const SizedBox(height: 9),
                Text(recommendation.title, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                const SizedBox(height: 4),
                Text(recommendation.reason, style: TextStyle(color: scheme.onSurfaceVariant, height: 1.35)),
              ])),
              PopupMenuButton<String>(
                tooltip: 'Options',
                onSelected: (v) { if (v == 'later') onLater(); if (v == 'dismiss') onDismiss(); },
                itemBuilder: (_) => const [PopupMenuItem(value: 'later', child: Text('Me le rappeler demain')), PopupMenuItem(value: 'dismiss', child: Text('Masquer cette recommandation'))],
              ),
            ]),
          ),
          Divider(height: 1, color: scheme.outlineVariant.withValues(alpha: .5)),
          Padding(
            padding: const EdgeInsets.fromLTRB(15, 10, 15, 12),
            child: Row(children: [
              Expanded(child: Text(_recommendationWhy(recommendation), style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 11.5, height: 1.3))),
              const SizedBox(width: 12),
              FilledButton.icon(onPressed: onNow, icon: const Icon(Icons.play_arrow_rounded, size: 18), label: const Text('Commencer')),
            ]),
          ),
        ]),
      ),
    );
  }

  String _recommendationWhy(StudyRecommendation r) => switch (r.kind) {
    RecommendationKind.assessmentFocus => 'Pourquoi : échéance proche + niveau de préparation observé.',
    RecommendationKind.recoverErrors => 'Pourquoi : des erreurs non récupérées restent ouvertes.',
    RecommendationKind.quizDrill => 'Pourquoi : le niveau actuel aux quiz peut encore progresser.',
    RecommendationKind.flashcardReview => 'Pourquoi : des cartes sont arrivées à échéance.',
    RecommendationKind.continueCourse => 'Pourquoi : couverture récente encore faible.',
    RecommendationKind.planRecovery => 'Pourquoi : le planning récent semble trop ambitieux.',
  };
}

class _CourseInsightsSection extends StatelessWidget {
  const _CourseInsightsSection({required this.courses});
  final List<CourseInsight> courses;

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      _SectionHeader(title: 'Matières à surveiller', subtitle: courses.isEmpty ? 'Les tendances apparaîtront après quelques activités.' : 'Touchez un cours pour comprendre le détail.'),
      const SizedBox(height: 10),
      if (courses.isEmpty)
        const EmptyStateCard(icon: Icons.insights_outlined, title: 'Pas encore assez de données', message: 'Lis, révise et fais quelques quiz : les tendances apparaîtront ici sans utiliser d’IA.')
      else
        ...courses.take(6).map((c) => Padding(padding: const EdgeInsets.only(bottom: 10), child: _CourseInsightTile(course: c))),
    ]);
  }
}

class _CourseInsightTile extends StatelessWidget {
  const _CourseInsightTile({required this.course});
  final CourseInsight course;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (tone, label) = switch (course.risk) {
      AnalyticsRisk.high => (EduNovaColors.danger, 'À renforcer'),
      AnalyticsRisk.medium => (EduNovaColors.accent, 'À consolider'),
      AnalyticsRisk.low => (EduNovaColors.success, 'Bon rythme'),
    };
    return InkWell(
      borderRadius: BorderRadius.circular(EduNovaRadius.lg),
      onTap: () => _showCourseDetail(context, course),
      child: PremiumPanel(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        child: Row(children: [
          if (course.readiness != null) ProgressRing(value: (course.readiness! / 100).clamp(0.0, 1.0).toDouble(), size: 54) else Container(width: 54, height: 54, decoration: BoxDecoration(color: scheme.surfaceContainerHighest, shape: BoxShape.circle), child: const Icon(Icons.insights_outlined)),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text(course.title, style: const TextStyle(fontWeight: FontWeight.w900))),
              StatusPill(icon: course.risk == AnalyticsRisk.low ? Icons.check_circle_outline_rounded : Icons.adjust_rounded, label: label, tone: tone),
            ]),
            const SizedBox(height: 5),
            Text(course.focusReason, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5, height: 1.3)),
            const SizedBox(height: 8),
            Wrap(spacing: 9, runSpacing: 5, children: [
              if (course.daysToNextAssessment != null) _TinyMetric(icon: Icons.event_outlined, label: 'J-${course.daysToNextAssessment}'),
              if (course.openErrors > 0) _TinyMetric(icon: Icons.rule_rounded, label: '${course.openErrors} erreurs'),
              if (course.overdueFlashcards > 0) _TinyMetric(icon: Icons.style_rounded, label: '${course.overdueFlashcards} cartes'),
              if (course.studyMinutes7d > 0) _TinyMetric(icon: Icons.timer_outlined, label: '${course.studyMinutes7d} min'),
            ]),
          ])),
          const SizedBox(width: 4),
          Icon(Icons.chevron_right_rounded, color: scheme.onSurfaceVariant),
        ]),
      ),
    );
  }

  void _showCourseDetail(BuildContext context, CourseInsight c) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      useSafeArea: true,
      builder: (sheetContext) => _CourseDetailSheet(course: c),
    );
  }
}

class _TinyMetric extends StatelessWidget {
  const _TinyMetric({required this.icon, required this.label});
  final IconData icon;
  final String label;
  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme.onSurfaceVariant;
    return Row(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 14, color: color), const SizedBox(width: 4), Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700))]);
  }
}

class _CourseDetailSheet extends StatelessWidget {
  const _CourseDetailSheet({required this.course});
  final CourseInsight course;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final metrics = <({String label, double? value, IconData icon})>[
      (label: 'Cours couvert', value: course.coverage, icon: Icons.menu_book_outlined),
      (label: 'Maîtrise quiz', value: course.quizMastery, icon: Icons.quiz_outlined),
      (label: 'Flashcards', value: course.flashcardMastery, icon: Icons.style_outlined),
      (label: 'Erreurs récupérées', value: course.weaknessRecovery, icon: Icons.task_alt_rounded),
    ];
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 28),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(children: [
          if (course.readiness != null) ProgressRing(value: (course.readiness! / 100).clamp(0.0, 1.0).toDouble(), size: 74),
          if (course.readiness != null) const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(course.title, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 4),
            Text(course.focusReason, style: TextStyle(color: scheme.onSurfaceVariant, height: 1.35)),
          ])),
        ]),
        const SizedBox(height: 20),
        Text('Ce qui compose ta préparation', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 10),
        ...metrics.map((m) => Padding(padding: const EdgeInsets.only(bottom: 10), child: _DimensionBar(label: m.label, value: m.value, icon: m.icon))),
        const SizedBox(height: 8),
        PremiumPanel(
          padding: const EdgeInsets.all(14),
          child: Wrap(spacing: 14, runSpacing: 10, children: [
            _TinyMetric(icon: Icons.rule_rounded, label: '${course.openErrors} erreurs ouvertes'),
            _TinyMetric(icon: Icons.style_rounded, label: '${course.overdueFlashcards} flashcards dues'),
            _TinyMetric(icon: Icons.timer_outlined, label: '${course.studyMinutes7d} min / 7 jours'),
            if (course.daysToNextAssessment != null) _TinyMetric(icon: Icons.event_outlined, label: 'Évaluation dans ${course.daysToNextAssessment} j'),
          ]),
        ),
        const SizedBox(height: 18),
        FilledButton.icon(onPressed: () { Navigator.of(context).pop(); context.push('/study/${course.courseId}?title=${Uri.encodeComponent(course.title)}'); }, icon: const Icon(Icons.play_arrow_rounded), label: const Text('Travailler ce cours')),
        const SizedBox(height: 8),
        OutlinedButton.icon(onPressed: () { Navigator.of(context).pop(); context.push('/revision'); }, icon: const Icon(Icons.event_note_rounded), label: const Text('Voir mon plan de révision')),
        const SizedBox(height: 10),
        Text('Le pourcentage de préparation synthétise uniquement les signaux disponibles. Il ne prédit ni ta note ni ta réussite.', textAlign: TextAlign.center, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 11.5, height: 1.3)),
      ]),
    );
  }
}

class _DimensionBar extends StatelessWidget {
  const _DimensionBar({required this.label, required this.value, required this.icon});
  final String label;
  final double? value;
  final IconData icon;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final normalized = value?.clamp(0.0, 1.0).toDouble();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Icon(icon, size: 18, color: scheme.primary), const SizedBox(width: 8), Expanded(child: Text(label, style: const TextStyle(fontWeight: FontWeight.w800))), Text(normalized == null ? '—' : '${(normalized * 100).round()} %', style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w800))]),
      const SizedBox(height: 7),
      LinearProgressIndicator(value: normalized ?? 0, minHeight: 7, borderRadius: BorderRadius.circular(99), backgroundColor: scheme.surfaceContainerHighest, color: normalized == null ? scheme.outlineVariant : scheme.primary),
    ]);
  }
}

class _MethodologyCard extends StatelessWidget {
  const _MethodologyCard({required this.report});
  final AnalyticsReport report;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return PremiumPanel(
      padding: EdgeInsets.zero,
      child: ExpansionTile(
        leading: Icon(Icons.shield_outlined, color: scheme.primary),
        title: const Text('Comment EduNova calcule ces tendances ?', style: TextStyle(fontWeight: FontWeight.w900)),
        subtitle: Text('Localement, sans IA payante et sans prédire tes résultats.', style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: [
          Text(report.explanation, style: TextStyle(color: scheme.onSurfaceVariant, height: 1.4)),
          const SizedBox(height: 12),
          const _MethodRow(icon: Icons.timer_outlined, text: 'Temps étudié, activité et respect du planning.'),
          const _MethodRow(icon: Icons.quiz_outlined, text: 'Résultats de quiz, erreurs récupérées et flashcards.'),
          const _MethodRow(icon: Icons.menu_book_outlined, text: 'Progression de lecture et échéances académiques.'),
          const _MethodRow(icon: Icons.lock_outline_rounded, text: 'Calcul local-first : tes documents personnels ne sont pas envoyés pour produire ce tableau.'),
        ],
      ),
    );
  }
}

class _MethodRow extends StatelessWidget {
  const _MethodRow({required this.icon, required this.text});
  final IconData icon;
  final String text;
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(top: 8), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(icon, size: 17), const SizedBox(width: 8), Expanded(child: Text(text))]));
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.subtitle});
  final String title, subtitle;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
      const SizedBox(height: 3),
      Text(subtitle, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5)),
    ]);
  }
}

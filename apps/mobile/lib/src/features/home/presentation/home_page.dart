import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../../../core/theme/tokens.dart';
import '../../../shared/presentation/widgets/premium_surface.dart';
import '../../analytics/domain/analytics.dart';
import '../../study_plan/domain/study_plan.dart';

class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final now = DateTime.now();
    final streak = ref.watch(localStreakProvider).valueOrNull;
    final prefs = ref.watch(engagementPreferencesProvider).valueOrNull;
    final days = ref.watch(engagementDaysProvider).valueOrNull ?? const [];
    final planAsync = ref.watch(todayPlanProvider);
    final eventsAsync = ref.watch(upcomingEventsProvider);
    final coursesAsync = ref.watch(libraryCoursesProvider);
    final analyticsAsync = ref.watch(analyticsReportProvider);
    final plan = planAsync.valueOrNull ?? const <StudyPlanItem>[];
    final events = eventsAsync.valueOrNull ?? const <AcademicEvent>[];
    final courses = coursesAsync.valueOrNull ?? const [];
    final nextEvent = events.where((e) => e.startsAt.isAfter(now)).fold<AcademicEvent?>(null, (best, e) => best == null || e.startsAt.isBefore(best.startsAt) ? e : best);
    final activeToday = days.isEmpty ? 0 : days.first.activeMinutes;
    final goal = prefs?.dailyGoalMinutes ?? 30;
    final goalProgress = goal <= 0 ? 0.0 : (activeToday / goal).clamp(0, 1).toDouble();
    final followed = courses.where((c) => c.followed).toList();
    final scheme = Theme.of(context).colorScheme;

    return SingleChildScrollView(
      child: EduNovaPageBody(
        padding: const EdgeInsets.fromLTRB(18, 16, 18, 120),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(_greeting(now.hour), style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: scheme.onSurfaceVariant)),
              const SizedBox(height: 2),
              Text('Prêt à avancer ?', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 4),
              Text(_dateLabel(now), style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w600)),
            ])),
            Stack(clipBehavior: Clip.none, children: [
              IconButton.filledTonal(tooltip: 'Rythme et notifications', onPressed: () => context.push('/engagement'), icon: const Icon(Icons.notifications_none_rounded)),
              if ((ref.watch(upcomingLocalNotificationsProvider).valueOrNull ?? const []).isNotEmpty)
                Positioned(right: 2, top: 2, child: Container(width: 9, height: 9, decoration: BoxDecoration(color: scheme.error, shape: BoxShape.circle, border: Border.all(color: scheme.surface, width: 1.5)))),
            ]),
          ]),
          const SizedBox(height: 16),
          _EngagementStrip(currentDays: streak?.currentDays ?? 0, weeklyMinutes: streak?.weeklyMinutes ?? 0, todayMinutes: activeToday, goalMinutes: goal, progress: goalProgress, onTap: () => context.push('/engagement')),
          const SizedBox(height: 10),
          analyticsAsync.when(
            loading: () => const PremiumPanel(padding: EdgeInsets.all(14), child: SkeletonLine(height: 56)),
            error: (_, __) => const SizedBox.shrink(),
            data: (report) => _ProgressInsightCard(report: report, onTap: () => context.push('/analytics')),
          ),
          const SizedBox(height: 12),
          _DeadlineHero(event: nextEvent, onStart: () => context.go('/revision')),
          const SizedBox(height: 22),
          Row(children: [Expanded(child: Text('Aujourd’hui', style: Theme.of(context).textTheme.titleLarge)), if (plan.isNotEmpty) Text('${plan.fold<int>(0, (a, b) => a + b.minutes)} min', style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w800))]),
          const SizedBox(height: 10),
          if (planAsync.isLoading)
            const PremiumPanel(child: Column(children: [SkeletonLine(height: 52), SizedBox(height: 10), SkeletonLine(height: 52)]))
          else if (plan.isEmpty)
            EmptyStateCard(icon: Icons.auto_awesome_rounded, title: 'Ton plan est prêt à être construit', message: 'Ajoute tes cours, ton horaire ou une prochaine interrogation. EduNova priorisera ensuite le travail utile.', action: FilledButton.tonalIcon(onPressed: () => context.go('/revision'), icon: const Icon(Icons.bolt_rounded), label: const Text('Ouvrir Réviser')))
          else
            PremiumPanel(child: Column(children: [
              for (var i = 0; i < plan.take(4).length; i++) ...[
                _PlanRow(item: plan[i], onTap: () => context.go('/revision')),
                if (i < plan.take(4).length - 1) const Divider(),
              ],
              const SizedBox(height: 10),
              SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: () => context.go('/revision'), icon: const Icon(Icons.play_arrow_rounded), label: Text('Commencer · ${plan.fold<int>(0, (a, b) => a + b.minutes)} min'))),
            ])),
          const SizedBox(height: 22),
          Text('Tes priorités', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 10),
          if (plan.isEmpty)
            Text('Les priorités apparaîtront dès qu’EduNova aura suffisamment de données sur ton travail.', style: TextStyle(color: scheme.onSurfaceVariant))
          else
            SizedBox(
              height: 126,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: plan.take(5).length,
                separatorBuilder: (_, __) => const SizedBox(width: 10),
                itemBuilder: (_, index) => _PriorityCard(item: plan[index]),
              ),
            ),
          const SizedBox(height: 22),
          Row(children: [Expanded(child: Text('Mes cours suivis', style: Theme.of(context).textTheme.titleLarge)), TextButton(onPressed: () => context.go('/courses'), child: const Text('Tous les cours'))]),
          const SizedBox(height: 10),
          if (coursesAsync.isLoading)
            const PremiumPanel(child: SkeletonLine(height: 60))
          else if (followed.isEmpty)
            EmptyStateCard(icon: Icons.bookmark_add_outlined, title: 'Aucun cours suivi', message: 'Épingle les cours importants pour les retrouver immédiatement sur tous tes appareils.', action: OutlinedButton.icon(onPressed: () => context.go('/courses'), icon: const Icon(Icons.explore_outlined), label: const Text('Explorer les cours')))
          else
            ...followed.take(2).map((course) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: PremiumPanel(
                padding: const EdgeInsets.all(14),
                child: ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: CircleAvatar(backgroundColor: scheme.secondaryContainer, child: const Icon(Icons.auto_stories_rounded)),
                  title: Text(course.title, style: const TextStyle(fontWeight: FontWeight.w800)),
                  subtitle: Text('${course.level} · ${course.semester}${course.premiumRequired ? ' · Premium' : ''}'),
                  trailing: IconButton.filledTonal(tooltip: 'Ouvrir le cours', onPressed: () => context.push('/library/${course.id}?title=${Uri.encodeComponent(course.title)}'), icon: const Icon(Icons.arrow_forward_rounded)),
                ),
              ),
            )),
        ]),
      ),
    );
  }

  String _greeting(int hour) => hour < 12 ? 'Bonjour 👋' : hour < 18 ? 'Bon après-midi 👋' : 'Bonsoir 👋';

  String _dateLabel(DateTime d) {
    const weekdays = ['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche'];
    const months = ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'];
    return '${weekdays[d.weekday - 1]} ${d.day} ${months[d.month - 1]}';
  }
}

class _EngagementStrip extends StatelessWidget {
  const _EngagementStrip({required this.currentDays, required this.weeklyMinutes, required this.todayMinutes, required this.goalMinutes, required this.progress, required this.onTap});
  final int currentDays, weeklyMinutes, todayMinutes, goalMinutes; final double progress; final VoidCallback onTap;
  @override Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      borderRadius: BorderRadius.circular(EduNovaRadius.lg),
      onTap: onTap,
      child: PremiumPanel(
        padding: const EdgeInsets.all(14),
        child: Row(children: [
          Stack(alignment: Alignment.center, children: [
            SizedBox(width: 52, height: 52, child: CircularProgressIndicator(value: progress, strokeWidth: 5, backgroundColor: scheme.outlineVariant.withValues(alpha: .5), strokeCap: StrokeCap.round)),
            Icon(progress >= 1 ? Icons.check_rounded : Icons.local_fire_department_rounded, color: progress >= 1 ? EduNovaColors.success : scheme.primary),
          ]),
          const SizedBox(width: 13),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(progress >= 1 ? 'Objectif du jour atteint' : '$todayMinutes / $goalMinutes min aujourd’hui', style: const TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 3),
            Text('$currentDays jour${currentDays > 1 ? 's' : ''} de rythme · $weeklyMinutes min / 7 jours', style: TextStyle(color: scheme.onSurfaceVariant)),
          ])),
          const Icon(Icons.chevron_right_rounded),
        ]),
      ),
    );
  }
}

class _DeadlineHero extends StatelessWidget {
  const _DeadlineHero({required this.event, required this.onStart});
  final AcademicEvent? event; final VoidCallback onStart;
  @override Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    if (event == null) {
      return PremiumPanel(
        emphasis: true,
        child: Row(children: [
          Container(width: 52, height: 52, decoration: BoxDecoration(color: scheme.primaryContainer, borderRadius: BorderRadius.circular(17)), child: Icon(Icons.event_available_rounded, color: scheme.primary)),
          const SizedBox(width: 14),
          const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Aucune échéance proche', style: TextStyle(fontWeight: FontWeight.w900)), SizedBox(height: 3), Text('Ajoute une interrogation ou un examen pour que le planning s’adapte automatiquement.')])),
        ]),
      );
    }
    final diff = event!.startsAt.difference(DateTime.now());
    final countdown = diff.inHours < 24 ? '${diff.inHours.clamp(0, 23)} h' : '${diff.inDays} j';
    final kind = switch (event!.kind) { AcademicEventKind.exam => 'Examen', AcademicEventKind.interrogation => 'Interrogation', AcademicEventKind.assignment => 'Travail', AcademicEventKind.practical => 'Pratique', _ => 'Échéance' };
    return Container(
      padding: const EdgeInsets.all(21),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [scheme.primary, Color.lerp(scheme.primary, EduNovaColors.secondary, .42)!]),
        borderRadius: BorderRadius.circular(EduNovaRadius.xl),
        boxShadow: [BoxShadow(color: scheme.primary.withValues(alpha: .20), blurRadius: 30, offset: const Offset(0, 12))],
      ),
      child: Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('PROCHAINE ÉCHÉANCE', style: TextStyle(color: scheme.onPrimary.withValues(alpha: .78), fontWeight: FontWeight.w800, fontSize: 12, letterSpacing: .5)),
          const SizedBox(height: 7),
          Text(event!.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: scheme.onPrimary, fontSize: 24, height: 1.1, fontWeight: FontWeight.w900)),
          const SizedBox(height: 5),
          Text('$kind · dans $countdown', style: TextStyle(color: scheme.onPrimary.withValues(alpha: .9), fontWeight: FontWeight.w600)),
          const SizedBox(height: 15),
          FilledButton.tonalIcon(onPressed: onStart, icon: const Icon(Icons.bolt_rounded), label: const Text('Préparer maintenant')),
        ])),
        const SizedBox(width: 14),
        Container(width: 74, height: 74, decoration: BoxDecoration(color: scheme.onPrimary.withValues(alpha: .14), shape: BoxShape.circle), child: Center(child: Text(countdown, style: TextStyle(color: scheme.onPrimary, fontWeight: FontWeight.w900, fontSize: 20)))),
      ]),
    );
  }
}

class _PlanRow extends StatelessWidget {
  const _PlanRow({required this.item, required this.onTap});
  final StudyPlanItem item; final VoidCallback onTap;
  @override Widget build(BuildContext context) {
    final icon = switch (item.kind) { StudyTaskKind.quiz => Icons.quiz_rounded, StudyTaskKind.flashcards => Icons.style_rounded, StudyTaskKind.errors => Icons.rule_rounded, StudyTaskKind.summary => Icons.summarize_rounded, StudyTaskKind.mockExam => Icons.assignment_turned_in_rounded, StudyTaskKind.diagnostic => Icons.analytics_outlined, _ => Icons.menu_book_rounded };
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: CircleAvatar(child: Icon(icon)),
      title: Text(item.title, style: const TextStyle(fontWeight: FontWeight.w800)),
      subtitle: Text('${item.minutes} min${item.reasons.isEmpty ? '' : ' · ${item.reasons.first}'}'),
      trailing: const Icon(Icons.chevron_right_rounded),
      onTap: onTap,
    );
  }
}

class _PriorityCard extends StatelessWidget {
  const _PriorityCard({required this.item});
  final StudyPlanItem item;
  @override Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return SizedBox(
      width: 188,
      child: PremiumPanel(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [CircleAvatar(radius: 19, child: Text('${item.priority}', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 12))), const Spacer(), Icon(Icons.trending_up_rounded, color: item.priority >= 80 ? EduNovaColors.danger : scheme.primary, size: 20)]),
          const SizedBox(height: 10),
          Text(item.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800)),
          const Spacer(),
          Text('${item.minutes} min', style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w700)),
        ]),
      ),
    );
  }
}


class _ProgressInsightCard extends StatelessWidget {
  const _ProgressInsightCard({required this.report, required this.onTap});
  final AnalyticsReport report;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (icon, title, tone) = switch (report.momentum) {
      AnalyticsTrend.improving => (Icons.trending_up_rounded, 'Ton rythme progresse', EduNovaColors.success),
      AnalyticsTrend.declining => (Icons.tune_rounded, 'Ton rythme mérite un ajustement', EduNovaColors.accent),
      AnalyticsTrend.stable => (Icons.horizontal_rule_rounded, 'Ton rythme est stable', scheme.primary),
    };
    final top = report.recommendations.isEmpty ? null : report.recommendations.first;
    return InkWell(
      borderRadius: BorderRadius.circular(EduNovaRadius.lg),
      onTap: onTap,
      child: PremiumPanel(
        emphasis: true,
        padding: const EdgeInsets.all(14),
        child: Row(children: [
          Container(width: 46, height: 46, decoration: BoxDecoration(color: tone.withValues(alpha: .12), borderRadius: BorderRadius.circular(15)), child: Icon(icon, color: tone)),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 3),
            Text(top == null ? '${report.activeDays7d}/7 jours actifs · continue régulièrement.' : '${top.title} · ${top.recommendedMinutes} min recommandées', maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12.5, height: 1.25)),
          ])),
          const SizedBox(width: 8),
          Icon(Icons.chevron_right_rounded, color: scheme.onSurfaceVariant),
        ]),
      ),
    );
  }
}

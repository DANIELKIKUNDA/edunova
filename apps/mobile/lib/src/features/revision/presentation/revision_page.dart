import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../../study_plan/domain/adaptive_planning.dart';
import '../../study_plan/domain/study_plan.dart';

class RevisionPage extends ConsumerWidget {
  const RevisionPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plan = ref.watch(adaptiveTodayBlocksProvider);
    final events = ref.watch(upcomingEventsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Réviser'),
        actions: [
          IconButton(
            tooltip: 'Réglages du planning',
            onPressed: () => context.push('/revision/planning-settings'),
            icon: const Icon(Icons.tune_rounded),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => _generate(context, ref, 30),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 120),
          children: [
            _HeroCard(
              title: 'Ton plan intelligent',
              subtitle: plan.maybeWhen(
                data: (rows) {
                  final active = rows.where((e) => e.status == 'planned').toList();
                  final minutes = active.fold<int>(0, (a, b) => a + b.minutes);
                  return active.isEmpty ? 'Choisis ton temps ou configure tes disponibilités.' : '$minutes min planifiées · ${active.length} bloc(s)';
                },
                orElse: () => 'Préparation…',
              ),
              onPressed: () => _chooseTime(context, ref),
            ),
            const SizedBox(height: 16),
            plan.when(
              loading: () => const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator())),
              error: (e, _) => _ErrorCard(message: e.toString()),
              data: (rows) => rows.isEmpty
                  ? const _EmptyPlan()
                  : Column(
                      children: rows.map((item) => _AdaptivePlanTile(
                        item: item,
                        onComplete: item.status == 'planned' ? () => ref.read(adaptivePlanningRepositoryProvider).completeBlock(item.id, actualMinutes: item.minutes) : null,
                        onDefer: item.status == 'planned' ? () => ref.read(adaptivePlanningRepositoryProvider).deferBlock(item.id) : null,
                        onPin: item.status == 'planned' ? () => ref.read(adaptivePlanningRepositoryProvider).setPinned(item.id, !item.pinned) : null,
                      )).toList(),
                    ),
            ),
            const SizedBox(height: 18),
            events.maybeWhen(
              data: (rows) {
                final now = DateTime.now();
                final urgent = rows.where((e) => e.startsAt.isAfter(now) && e.startsAt.difference(now) <= const Duration(hours: 36) && e.courseId != null).toList();
                if (urgent.isEmpty) return const SizedBox.shrink();
                return _ActionCard(
                  icon: Icons.warning_amber_rounded,
                  title: 'Évaluation imminente',
                  subtitle: '${urgent.first.title} · ${urgent.first.startsAt.difference(now).inHours} h',
                  button: 'Mode urgence',
                  onPressed: () => _emergency(context, ref, urgent.first),
                );
              },
              orElse: () => const SizedBox.shrink(),
            ),
            const SizedBox(height: 12),
            _ActionCard(
              icon: Icons.calendar_view_week_rounded,
              title: 'Mes disponibilités',
              subtitle: 'EduNova retire automatiquement les heures occupées par tes cours.',
              button: 'Configurer',
              onPressed: () => context.push('/revision/planning-settings'),
            ),
            const SizedBox(height: 12),
            _ActionCard(icon: Icons.error_outline_rounded, title: 'Mes erreurs', subtitle: 'Revoir ce qui te fait perdre des points', button: 'Réviser mes erreurs', onPressed: () {}),
            const SizedBox(height: 12),
            _ActionCard(icon: Icons.explore_rounded, title: 'Prendre de l’avance', subtitle: 'Explorer des cours d’un niveau supérieur', button: 'Explorer', onPressed: () {}),
          ],
        ),
      ),
    );
  }

  Future<void> _generate(BuildContext context, WidgetRef ref, int minutes) async {
    final plan = await ref.read(generateAdaptiveTodayPlanProvider)(now: DateTime.now(), budgetOverride: minutes);
    if (!context.mounted) return;
    if (plan.warnings.isNotEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(plan.warnings.first)));
    }
  }

  Future<void> _chooseTime(BuildContext context, WidgetRef ref) async {
    final value = await showModalBottomSheet<int>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Combien de temps as-tu ?', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            const Text('EduNova utilisera ce temps sans dépasser tes créneaux libres.'),
            const SizedBox(height: 16),
            Wrap(spacing: 10, runSpacing: 10, children: [for (final m in [5, 15, 30, 60]) ChoiceChip(label: Text('$m min'), selected: false, onSelected: (_) => Navigator.pop(context, m))]),
          ]),
        ),
      ),
    );
    if (value != null && context.mounted) await _generate(context, ref, value);
  }

  Future<void> _emergency(BuildContext context, WidgetRef ref, AcademicEvent event) async {
    final plan = await ref.read(generateAdaptiveTodayPlanProvider).emergency(now: DateTime.now(), event: event, budgetMinutes: 60);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Plan urgence prêt · ${plan.studyMinutes} min utiles.')));
    }
  }
}

class _HeroCard extends StatelessWidget {
  const _HeroCard({required this.title, required this.subtitle, required this.onPressed});
  final String title;
  final String subtitle;
  final VoidCallback onPressed;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(22),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        CircleAvatar(radius: 25, child: Icon(Icons.auto_awesome_rounded, color: Theme.of(context).colorScheme.primary)),
        const SizedBox(height: 16),
        Text(title, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 6),
        Text(subtitle),
        const SizedBox(height: 18),
        FilledButton.icon(onPressed: onPressed, icon: const Icon(Icons.timer_rounded), label: const Text('Planifier maintenant')),
      ]),
    ),
  );
}

class _AdaptivePlanTile extends StatelessWidget {
  const _AdaptivePlanTile({required this.item, this.onComplete, this.onDefer, this.onPin});
  final AdaptivePlanBlock item;
  final VoidCallback? onComplete;
  final VoidCallback? onDefer;
  final VoidCallback? onPin;

  @override
  Widget build(BuildContext context) {
    String hm(DateTime d) => '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
    final completed = item.status == 'completed';
    final deferred = item.status == 'deferred';
    final subtitle = <String>[
      '${hm(item.startsAt)}–${hm(item.endsAt)} · ${item.minutes} min',
      ...item.reasons.take(2),
    ].join(' · ');
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Card(
        child: ListTile(
          contentPadding: const EdgeInsets.fromLTRB(14, 12, 8, 12),
          leading: CircleAvatar(child: Icon(completed ? Icons.check_rounded : deferred ? Icons.redo_rounded : _icon(item.kind))),
          title: Text(item.title, style: TextStyle(fontWeight: FontWeight.w900, decoration: completed ? TextDecoration.lineThrough : null)),
          subtitle: Text(subtitle),
          trailing: onComplete == null
              ? Icon(completed ? Icons.check_circle_rounded : Icons.schedule_rounded)
              : PopupMenuButton<String>(
                  onSelected: (value) {
                    if (value == 'done') onComplete?.call();
                    if (value == 'defer') onDefer?.call();
                    if (value == 'pin') onPin?.call();
                  },
                  itemBuilder: (_) => [
                    const PopupMenuItem(value: 'done', child: ListTile(leading: Icon(Icons.check_rounded), title: Text('Terminer'))),
                    const PopupMenuItem(value: 'defer', child: ListTile(leading: Icon(Icons.schedule_send_rounded), title: Text('Reporter'))),
                    PopupMenuItem(value: 'pin', child: ListTile(leading: Icon(item.pinned ? Icons.push_pin : Icons.push_pin_outlined), title: Text(item.pinned ? 'Désépingler' : 'Épingler'))),
                  ],
                ),
        ),
      ),
    );
  }

  IconData _icon(StudyTaskKind kind) => switch (kind) {
    StudyTaskKind.read => Icons.menu_book_rounded,
    StudyTaskKind.summary => Icons.subject_rounded,
    StudyTaskKind.flashcards => Icons.style_rounded,
    StudyTaskKind.quiz => Icons.quiz_rounded,
    StudyTaskKind.errors => Icons.error_outline_rounded,
    StudyTaskKind.mockExam => Icons.assignment_turned_in_rounded,
    StudyTaskKind.diagnostic => Icons.monitor_heart_outlined,
  };
}

class _EmptyPlan extends StatelessWidget {
  const _EmptyPlan();
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(22),
      child: Column(children: [
        const Icon(Icons.route_rounded, size: 40),
        const SizedBox(height: 12),
        Text('Aucun bloc planifié', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 6),
        const Text('Choisis ton temps ou configure tes plages d’étude. EduNova tiendra compte de ton horaire, de tes échéances et de tes faiblesses.', textAlign: TextAlign.center),
      ]),
    ),
  );
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({required this.icon, required this.title, required this.subtitle, required this.button, required this.onPressed});
  final IconData icon;
  final String title;
  final String subtitle;
  final String button;
  final VoidCallback onPressed;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        CircleAvatar(radius: 24, child: Icon(icon)),
        const SizedBox(height: 16),
        Text(title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 6),
        Text(subtitle),
        const SizedBox(height: 18),
        FilledButton.tonal(onPressed: onPressed, child: Text(button)),
      ]),
    ),
  );
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message});
  final String message;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(18), child: Text(message)));
}

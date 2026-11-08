import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../../../core/theme/tokens.dart';
import '../../../shared/presentation/widgets/premium_surface.dart';
import '../domain/engagement.dart';

class EngagementPage extends ConsumerStatefulWidget {
  const EngagementPage({super.key});
  @override ConsumerState<EngagementPage> createState() => _EngagementPageState();
}

class _EngagementPageState extends ConsumerState<EngagementPage> {
  int _section = 0;

  String _time(int minute) => '${(minute ~/ 60).toString().padLeft(2, '0')}:${(minute % 60).toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    final prefsAsync = ref.watch(engagementPreferencesProvider);
    final daysAsync = ref.watch(engagementDaysProvider);
    final notifsAsync = ref.watch(upcomingLocalNotificationsProvider);
    final historyAsync = ref.watch(recentNotificationHistoryProvider);
    final streakAsync = ref.watch(localStreakProvider);
    final disableMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mon rythme'),
        actions: [
          IconButton(
            tooltip: 'Actualiser mon activité',
            onPressed: _refreshActivity,
            icon: const Icon(Icons.sync_rounded),
          ),
        ],
      ),
      body: EduNovaPageBody(
        maxWidth: 980,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _HeroHeader(streak: streakAsync.valueOrNull),
          const SizedBox(height: 18),
          SegmentedButton<int>(
            showSelectedIcon: false,
            segments: const [
              ButtonSegment(value: 0, icon: Icon(Icons.insights_rounded), label: Text('Rythme')),
              ButtonSegment(value: 1, icon: Icon(Icons.notifications_active_outlined), label: Text('Rappels')),
              ButtonSegment(value: 2, icon: Icon(Icons.tune_rounded), label: Text('Réglages')),
            ],
            selected: {_section},
            onSelectionChanged: (v) => setState(() => _section = v.first),
          ),
          const SizedBox(height: 18),
          AnimatedSwitcher(
            duration: disableMotion ? Duration.zero : EduNovaMotion.standard,
            switchInCurve: EduNovaMotion.curve,
            child: switch (_section) {
              0 => _RhythmSection(
                  key: const ValueKey('rhythm'),
                  prefsAsync: prefsAsync,
                  daysAsync: daysAsync,
                  streakAsync: streakAsync,
                  onRefresh: _refreshActivity,
                ),
              1 => _ReminderSection(
                  key: const ValueKey('reminders'),
                  notificationsAsync: notifsAsync,
                  historyAsync: historyAsync,
                  onReschedule: _reschedule,
                ),
              _ => _PreferencesSection(
                  key: const ValueKey('preferences'),
                  prefsAsync: prefsAsync,
                  timeLabel: _time,
                  onSave: _save,
                  onRequestPermission: _explainAndRequestPermission,
                  onPickMinute: _pickMinute,
                  systemNotificationsSupported: ref.read(localNotificationSchedulerProvider).supportsSystemNotifications,
                ),
            },
          ),
        ]),
      ),
    );
  }

  Future<void> _refreshActivity() async {
    final day = await ref.read(engagementRepositoryProvider).recomputeToday(DateTime.now());
    try { await ref.read(engagementRemoteGatewayProvider).syncDay(day); } catch (_) {}
    ref.invalidate(localStreakProvider);
  }

  Future<void> _reschedule() async {
    await ref.read(rescheduleLocalNotificationsProvider).run();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Rappels locaux mis à jour.')));
  }

  Future<void> _save(EngagementPreferences p) async {
    final normalized = p.copyWith(timezoneOffsetMinutes: DateTime.now().timeZoneOffset.inMinutes);
    await ref.read(engagementRepositoryProvider).savePreferences(normalized);
    try { await ref.read(engagementRemoteGatewayProvider).syncPreferences(normalized); } catch (_) {}
    try { await ref.read(rescheduleLocalNotificationsProvider).run(); } catch (_) {}
  }

  Future<int?> _pickMinute(int initialMinute) async {
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(hour: initialMinute ~/ 60, minute: initialMinute % 60),
      helpText: 'Choisir une heure',
      cancelText: 'Annuler',
      confirmText: 'Valider',
    );
    return time == null ? null : time.hour * 60 + time.minute;
  }

  Future<void> _explainAndRequestPermission() async {
    final proceed = await showModalBottomSheet<bool>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (context) {
        final scheme = Theme.of(context).colorScheme;
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(22, 6, 22, 26),
            child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                width: 54,
                height: 54,
                decoration: BoxDecoration(color: scheme.primaryContainer, borderRadius: BorderRadius.circular(18)),
                child: Icon(Icons.notifications_active_rounded, color: scheme.primary),
              ),
              const SizedBox(height: 16),
              Text('Des rappels utiles, jamais du bruit', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text(
                'EduNova utilise les notifications pour tes interrogations, ton plan du jour et les rappels que tu as choisis. Elles respectent tes heures calmes et ton plafond quotidien.',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: scheme.onSurfaceVariant),
              ),
              const SizedBox(height: 18),
              Row(children: [
                Expanded(child: OutlinedButton(onPressed: () => Navigator.pop(context, false), child: const Text('Plus tard'))),
                const SizedBox(width: 10),
                Expanded(child: FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Continuer'))),
              ]),
            ]),
          ),
        );
      },
    );
    if (proceed != true) return;
    final ok = await ref.read(localNotificationSchedulerProvider).requestPermission();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(ok ? 'Notifications système autorisées.' : 'Permission non accordée. Tu peux la réactiver plus tard.')));
  }
}

class _HeroHeader extends StatelessWidget {
  const _HeroHeader({required this.streak});
  final StreakView? streak;
  @override Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final days = streak?.currentDays ?? 0;
    final minutes = streak?.weeklyMinutes ?? 0;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [scheme.primary, Color.lerp(scheme.primary, EduNovaColors.secondary, .42)!],
        ),
        borderRadius: BorderRadius.circular(EduNovaRadius.xl),
        boxShadow: [BoxShadow(color: scheme.primary.withValues(alpha: .20), blurRadius: 30, offset: const Offset(0, 12))],
      ),
      child: Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Ton rythme d’étude', style: TextStyle(color: scheme.onPrimary.withValues(alpha: .82), fontWeight: FontWeight.w800, fontSize: 13)),
          const SizedBox(height: 6),
          Text(days == 0 ? 'Commence aujourd’hui' : '$days jour${days > 1 ? 's' : ''} de suite', style: TextStyle(color: scheme.onPrimary, fontWeight: FontWeight.w900, fontSize: 25)),
          const SizedBox(height: 6),
          Text('$minutes min sur les 7 derniers jours', style: TextStyle(color: scheme.onPrimary.withValues(alpha: .88))),
        ])),
        const SizedBox(width: 12),
        Container(
          width: 72,
          height: 72,
          decoration: BoxDecoration(color: scheme.onPrimary.withValues(alpha: .14), shape: BoxShape.circle),
          child: Icon(Icons.local_fire_department_rounded, color: scheme.onPrimary, size: 36),
        ),
      ]),
    );
  }
}

class _RhythmSection extends StatelessWidget {
  const _RhythmSection({super.key, required this.prefsAsync, required this.daysAsync, required this.streakAsync, required this.onRefresh});
  final AsyncValue<EngagementPreferences> prefsAsync;
  final AsyncValue<List<EngagementDailyStat>> daysAsync;
  final AsyncValue<StreakView> streakAsync;
  final Future<void> Function() onRefresh;

  @override Widget build(BuildContext context) {
    final prefs = prefsAsync.valueOrNull ?? const EngagementPreferences();
    final days = daysAsync.valueOrNull ?? const <EngagementDailyStat>[];
    final streak = streakAsync.valueOrNull;
    final today = days.isEmpty ? null : days.first;
    final todayMinutes = today?.activeMinutes ?? 0;
    final progress = prefs.dailyGoalMinutes <= 0 ? 0.0 : (todayMinutes / prefs.dailyGoalMinutes).clamp(0, 1).toDouble();
    final scheme = Theme.of(context).colorScheme;
    final recent = days.take(7).toList().reversed.toList();

    if (prefsAsync.isLoading && daysAsync.isLoading) {
      return const PremiumPanel(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SkeletonLine(width: 180, height: 18), SizedBox(height: 14), SkeletonLine(height: 64), SizedBox(height: 12), SkeletonLine(height: 64),
      ]));
    }
    if (prefsAsync.hasError || daysAsync.hasError) {
      return EmptyStateCard(icon: Icons.cloud_off_rounded, title: 'Rythme temporairement indisponible', message: 'Tes données locales restent intactes. Réessaie lorsque tu veux.', action: FilledButton.tonalIcon(onPressed: onRefresh, icon: const Icon(Icons.refresh_rounded), label: const Text('Réessayer')));
    }

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      LayoutBuilder(builder: (context, constraints) {
        final twoCols = constraints.maxWidth >= 720;
        final goal = PremiumPanel(
          emphasis: true,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text('Objectif du jour', style: Theme.of(context).textTheme.titleMedium)),
              StatusPill(icon: progress >= 1 ? Icons.check_rounded : Icons.timelapse_rounded, label: progress >= 1 ? 'Atteint' : '${(progress * 100).round()} %', tone: progress >= 1 ? EduNovaColors.success : scheme.primary),
            ]),
            const SizedBox(height: 14),
            ClipRRect(borderRadius: BorderRadius.circular(99), child: LinearProgressIndicator(value: progress, minHeight: 10)),
            const SizedBox(height: 10),
            Text('$todayMinutes / ${prefs.dailyGoalMinutes} min aujourd’hui', style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w700)),
          ]),
        );
        final week = PremiumPanel(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text('Les 7 derniers jours', style: Theme.of(context).textTheme.titleMedium)),
              Text('${streak?.weeklyActiveDays ?? recent.where((d) => d.active).length}/7 actifs', style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w700)),
            ]),
            const SizedBox(height: 16),
            _ActivityBars(days: recent),
          ]),
        );
        if (!twoCols) return Column(children: [goal, const SizedBox(height: 12), week]);
        return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: goal), const SizedBox(width: 12), Expanded(child: week)]);
      }),
      const SizedBox(height: 12),
      PremiumPanel(
        child: Row(children: [
          Expanded(child: _Metric(icon: Icons.timer_outlined, label: 'Cette semaine', value: '${streak?.weeklyMinutes ?? 0} min')),
          Container(width: 1, height: 42, color: scheme.outlineVariant),
          Expanded(child: _Metric(icon: Icons.emoji_events_outlined, label: 'Meilleure série', value: '${streak?.bestDays ?? 0} j')),
          Container(width: 1, height: 42, color: scheme.outlineVariant),
          Expanded(child: _Metric(icon: Icons.quiz_outlined, label: 'Quiz aujourd’hui', value: '${today?.quizQuestions ?? 0}')),
        ]),
      ),
      const SizedBox(height: 12),
      PremiumPanel(
        child: Row(children: [
          Container(width: 46, height: 46, decoration: BoxDecoration(color: scheme.secondaryContainer, borderRadius: BorderRadius.circular(15)), child: Icon(Icons.favorite_outline_rounded, color: scheme.secondary)),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Un rythme utile, pas une pression', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text('Les séries sont un repère personnel. Une journée manquée ne bloque aucune fonctionnalité et ne déclenche aucun message culpabilisant.', style: TextStyle(color: scheme.onSurfaceVariant)),
          ])),
        ]),
      ),
    ]);
  }
}

class _ActivityBars extends StatelessWidget {
  const _ActivityBars({required this.days});
  final List<EngagementDailyStat> days;
  @override Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final maxMinutes = days.fold<int>(30, (m, d) => d.activeMinutes > m ? d.activeMinutes : m);
    final padded = <EngagementDailyStat?>[...List.filled((7 - days.length).clamp(0, 7).toInt(), null), ...days];
    return SizedBox(
      height: 74,
      child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: padded.map((d) {
        final ratio = d == null ? 0.0 : (d.activeMinutes / maxMinutes).clamp(0, 1).toDouble();
        return Expanded(child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 3),
          child: Tooltip(
            message: d == null ? 'Aucune donnée' : '${d.activeMinutes} min',
            child: Column(mainAxisAlignment: MainAxisAlignment.end, children: [
              AnimatedContainer(
                duration: MediaQuery.maybeOf(context)?.disableAnimations == true ? Duration.zero : EduNovaMotion.standard,
                curve: EduNovaMotion.curve,
                height: 12 + 44 * ratio,
                decoration: BoxDecoration(color: d?.active == true ? scheme.primary : scheme.outlineVariant.withValues(alpha: .45), borderRadius: BorderRadius.circular(7)),
              ),
              const SizedBox(height: 6),
              Container(width: 5, height: 5, decoration: BoxDecoration(color: d?.active == true ? scheme.secondary : Colors.transparent, shape: BoxShape.circle)),
            ]),
          ),
        ));
      }).toList()),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.icon, required this.label, required this.value});
  final IconData icon; final String label; final String value;
  @override Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 8),
    child: Column(children: [Icon(icon, size: 20), const SizedBox(height: 7), Text(value, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)), const SizedBox(height: 2), Text(label, textAlign: TextAlign.center, maxLines: 2, style: Theme.of(context).textTheme.bodySmall)]),
  );
}

class _ReminderSection extends StatelessWidget {
  const _ReminderSection({super.key, required this.notificationsAsync, required this.historyAsync, required this.onReschedule});
  final AsyncValue<List<LocalNotificationView>> notificationsAsync;
  final AsyncValue<List<LocalNotificationView>> historyAsync;
  final Future<void> Function() onReschedule;

  @override Widget build(BuildContext context) {
    final values = notificationsAsync.valueOrNull ?? const <LocalNotificationView>[];
    final scheme = Theme.of(context).colorScheme;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      PremiumPanel(
        child: Row(children: [
          Container(width: 48, height: 48, decoration: BoxDecoration(color: scheme.primaryContainer, borderRadius: BorderRadius.circular(16)), child: Icon(Icons.notifications_active_outlined, color: scheme.primary)),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Rappels intelligents', style: Theme.of(context).textTheme.titleMedium), const SizedBox(height: 3), Text('Générés localement, respectueux de tes heures calmes et de ton plafond quotidien.', style: TextStyle(color: scheme.onSurfaceVariant))])),
          IconButton.filledTonal(tooltip: 'Reprogrammer', onPressed: onReschedule, icon: const Icon(Icons.refresh_rounded)),
        ]),
      ),
      const SizedBox(height: 12),
      if (notificationsAsync.isLoading) const PremiumPanel(child: Column(children: [SkeletonLine(height: 56), SizedBox(height: 10), SkeletonLine(height: 56)]))
      else if (notificationsAsync.hasError) EmptyStateCard(icon: Icons.notifications_off_outlined, title: 'Impossible de lire les rappels', message: 'Tu peux continuer à utiliser EduNova. Tes échéances restent enregistrées localement.', action: FilledButton.tonalIcon(onPressed: onReschedule, icon: const Icon(Icons.refresh_rounded), label: const Text('Réessayer')))
      else if (values.isEmpty) const EmptyStateCard(icon: Icons.notifications_none_rounded, title: 'Aucun rappel à venir', message: 'EduNova programmera automatiquement les rappels utiles lorsque tu ajoutes une échéance ou un plan de révision.')
      else ...values.map((n) => Padding(padding: const EdgeInsets.only(bottom: 10), child: _ReminderCard(notification: n))),
      const SizedBox(height: 10),
      if ((historyAsync.valueOrNull ?? const <LocalNotificationView>[]).isNotEmpty)
        PremiumPanel(
          child: ExpansionTile(
            tilePadding: EdgeInsets.zero,
            childrenPadding: const EdgeInsets.only(top: 4),
            leading: const Icon(Icons.history_rounded),
            title: const Text('Historique récent', style: TextStyle(fontWeight: FontWeight.w900)),
            subtitle: Text('${(historyAsync.valueOrNull ?? const <LocalNotificationView>[]).length} rappel(s)'),
            children: (historyAsync.valueOrNull ?? const <LocalNotificationView>[]).take(8).map((n) => ListTile(
              contentPadding: EdgeInsets.zero,
              dense: true,
              leading: Icon(n.status == 'opened' ? Icons.mark_email_read_outlined : Icons.notifications_none_rounded, size: 20),
              title: Text(n.title, maxLines: 1, overflow: TextOverflow.ellipsis),
              subtitle: Text('${_pastLabel(n.fireAt)} · ${n.status == 'opened' ? 'ouvert' : 'passé'}'),
              trailing: n.deepLink.isEmpty ? null : const Icon(Icons.chevron_right_rounded),
              onTap: n.deepLink.isEmpty ? null : () => context.push(n.deepLink),
            )).toList(),
          ),
        ),
    ]);
  }

  static String _pastLabel(DateTime date) {
    final diff = DateTime.now().difference(date.toLocal());
    if (diff.inMinutes < 60) return 'il y a ${diff.inMinutes.clamp(1, 59)} min';
    if (diff.inHours < 24) return 'il y a ${diff.inHours} h';
    if (diff.inDays == 1) return 'hier';
    if (diff.inDays < 7) return 'il y a ${diff.inDays} j';
    final d = date.toLocal();
    return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}';
  }
}

class _ReminderCard extends ConsumerWidget {
  const _ReminderCard({required this.notification});
  final LocalNotificationView notification;
  @override Widget build(BuildContext context, WidgetRef ref) {
    final scheme = Theme.of(context).colorScheme;
    final tone = notification.priority >= 80 ? EduNovaColors.danger : notification.priority >= 60 ? EduNovaColors.accent : scheme.primary;
    final icon = switch (notification.category) {
      'assessment' => Icons.assignment_rounded,
      'study_plan' => Icons.bolt_rounded,
      'flashcards' => Icons.style_rounded,
      _ => Icons.notifications_active_outlined,
    };
    return PremiumPanel(
      padding: const EdgeInsets.all(15),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(width: 44, height: 44, decoration: BoxDecoration(color: tone.withValues(alpha: .10), borderRadius: BorderRadius.circular(14)), child: Icon(icon, color: tone)),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [Expanded(child: Text(notification.title, style: const TextStyle(fontWeight: FontWeight.w800))), StatusPill(icon: Icons.schedule_rounded, label: _relative(notification.fireAt), tone: tone)]),
          const SizedBox(height: 5),
          Text(notification.body, style: TextStyle(color: scheme.onSurfaceVariant)),
          if (notification.deepLink.isNotEmpty) ...[
            const SizedBox(height: 9),
            TextButton.icon(onPressed: () async { await ref.read(engagementRepositoryProvider).markNotificationInteracted(notification.id); if (context.mounted) context.push(notification.deepLink); }, icon: const Icon(Icons.arrow_forward_rounded, size: 18), label: const Text('Ouvrir')),
          ],
        ])),
      ]),
    );
  }

  static String _relative(DateTime date) {
    final local = date.toLocal();
    final diff = local.difference(DateTime.now());
    if (diff.isNegative) return 'maintenant';
    if (diff.inMinutes < 60) return '${diff.inMinutes.clamp(1, 59)} min';
    if (diff.inHours < 24) return '${diff.inHours} h';
    if (diff.inDays == 1) return 'demain';
    if (diff.inDays < 7) return '${diff.inDays} j';
    return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')}';
  }
}

class _PreferencesSection extends StatelessWidget {
  const _PreferencesSection({super.key, required this.prefsAsync, required this.timeLabel, required this.onSave, required this.onRequestPermission, required this.onPickMinute, required this.systemNotificationsSupported});
  final AsyncValue<EngagementPreferences> prefsAsync;
  final String Function(int) timeLabel;
  final Future<void> Function(EngagementPreferences) onSave;
  final Future<void> Function() onRequestPermission;
  final Future<int?> Function(int) onPickMinute;
  final bool systemNotificationsSupported;

  @override Widget build(BuildContext context) {
    final prefs = prefsAsync.valueOrNull ?? const EngagementPreferences();
    final scheme = Theme.of(context).colorScheme;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      PremiumPanel(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Quand EduNova peut te rappeler', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text('Tu gardes toujours le contrôle. Les rappels personnels sont calculés sur ton appareil.', style: TextStyle(color: scheme.onSurfaceVariant)),
          const SizedBox(height: 14),
          _SettingToggle(icon: Icons.assignment_outlined, title: 'Interrogations & examens', subtitle: 'Échéances proches et préparation insuffisante', value: prefs.assessmentEnabled, onChanged: (v) => onSave(prefs.copyWith(assessmentEnabled: v))),
          _SettingToggle(icon: Icons.bolt_outlined, title: 'Plan du jour', subtitle: 'Une action concrète, jamais “reviens dans l’app”', value: prefs.studyPlanEnabled, onChanged: (v) => onSave(prefs.copyWith(studyPlanEnabled: v))),
          _SettingToggle(icon: Icons.style_outlined, title: 'Flashcards dues', subtitle: 'Uniquement lorsque des cartes nécessitent une révision', value: prefs.flashcardsEnabled, onChanged: (v) => onSave(prefs.copyWith(flashcardsEnabled: v))),
          _SettingToggle(icon: Icons.local_fire_department_outlined, title: 'Série de révision', subtitle: 'Optionnel, désactivé par défaut pour éviter la pression', value: prefs.streakEnabled, onChanged: (v) => onSave(prefs.copyWith(streakEnabled: v))),
          _SettingToggle(icon: Icons.new_releases_outlined, title: 'Nouveaux contenus', subtitle: 'Cours, interrogations et ressources ajoutées à ta bibliothèque', value: prefs.contentEnabled, onChanged: (v) => onSave(prefs.copyWith(contentEnabled: v))),
          _SettingToggle(icon: Icons.campaign_outlined, title: 'Push EduNova', subtitle: 'Canal distant pour les informations réellement utiles', value: prefs.pushEnabled, onChanged: (v) => onSave(prefs.copyWith(pushEnabled: v))),
        ]),
      ),
      const SizedBox(height: 12),
      LayoutBuilder(builder: (context, constraints) {
        final wide = constraints.maxWidth >= 720;
        final schedule = PremiumPanel(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Horaires', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            _TimeRow(icon: Icons.bedtime_outlined, title: 'Début heures calmes', value: timeLabel(prefs.quietStartMinute), onTap: () async { final m = await onPickMinute(prefs.quietStartMinute); if (m != null) await onSave(prefs.copyWith(quietStartMinute: m)); }),
            _TimeRow(icon: Icons.wb_sunny_outlined, title: 'Fin heures calmes', value: timeLabel(prefs.quietEndMinute), onTap: () async { final m = await onPickMinute(prefs.quietEndMinute); if (m != null) await onSave(prefs.copyWith(quietEndMinute: m)); }),
            _TimeRow(icon: Icons.self_improvement_outlined, title: 'Heure d’étude préférée', value: timeLabel(prefs.preferredStudyMinute), onTap: () async { final m = await onPickMinute(prefs.preferredStudyMinute); if (m != null) await onSave(prefs.copyWith(preferredStudyMinute: m)); }),
          ]),
        );
        final limits = PremiumPanel(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Intensité', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 14),
            Text('Maximum de rappels par jour', style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            SegmentedButton<int>(segments: [0,1,2,3].map((v) => ButtonSegment(value: v, label: Text('$v'))).toList(), selected: {prefs.maxDailyNotifications}, onSelectionChanged: (v) => onSave(prefs.copyWith(maxDailyNotifications: v.first))),
            const SizedBox(height: 16),
            Text('Objectif quotidien', style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(initialValue: prefs.dailyGoalMinutes, decoration: const InputDecoration(prefixIcon: Icon(Icons.timer_outlined)), items: [15,30,45,60,90,120].map((v) => DropdownMenuItem(value: v, child: Text('$v min'))).toList(), onChanged: (v) { if (v != null) onSave(prefs.copyWith(dailyGoalMinutes: v)); }),
          ]),
        );
        if (!wide) return Column(children: [schedule, const SizedBox(height: 12), limits]);
        return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: schedule), const SizedBox(width: 12), Expanded(child: limits)]);
      }),
      const SizedBox(height: 12),
      PremiumPanel(
        child: Row(children: [
          Container(width: 48, height: 48, decoration: BoxDecoration(color: scheme.secondaryContainer, borderRadius: BorderRadius.circular(16)), child: Icon(Icons.privacy_tip_outlined, color: scheme.secondary)),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(systemNotificationsSupported ? 'Permission système' : 'Notifications sur cette plateforme', style: Theme.of(context).textTheme.titleMedium), const SizedBox(height: 3), Text(systemNotificationsSupported ? 'EduNova demande la permission seulement quand tu le décides ici.' : 'Les rappels locaux natifs sont certifiés sur Android/iOS. Sur PWA/desktop, le canal push sera utilisé lorsqu’il est configuré.', style: TextStyle(color: scheme.onSurfaceVariant))])),
          const SizedBox(width: 10),
          if(systemNotificationsSupported) FilledButton.tonalIcon(onPressed: onRequestPermission, icon: const Icon(Icons.notifications_active_outlined), label: const Text('Autoriser')) else const StatusPill(icon: Icons.info_outline_rounded,label:'Canal distant'),
        ]),
      ),
    ]);
  }
}

class _SettingToggle extends StatelessWidget {
  const _SettingToggle({required this.icon, required this.title, required this.subtitle, required this.value, required this.onChanged});
  final IconData icon; final String title; final String subtitle; final bool value; final ValueChanged<bool> onChanged;
  @override Widget build(BuildContext context) => SwitchListTile.adaptive(
    contentPadding: EdgeInsets.zero,
    secondary: Icon(icon),
    value: value,
    onChanged: onChanged,
    title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
    subtitle: Text(subtitle),
  );
}

class _TimeRow extends StatelessWidget {
  const _TimeRow({required this.icon, required this.title, required this.value, required this.onTap});
  final IconData icon; final String title; final String value; final VoidCallback onTap;
  @override Widget build(BuildContext context) => ListTile(
    contentPadding: EdgeInsets.zero,
    leading: Icon(icon),
    title: Text(title),
    trailing: FilledButton.tonal(onPressed: onTap, child: Text(value)),
  );
}

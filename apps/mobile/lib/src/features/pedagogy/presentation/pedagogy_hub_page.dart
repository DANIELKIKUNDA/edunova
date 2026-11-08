import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../domain/pedagogy.dart';

class PedagogyHubPage extends ConsumerWidget {
  const PedagogyHubPage({super.key, required this.courseId, this.title = 'Cours'});

  final String courseId;
  final String title;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summaries = ref.watch(courseSummariesProvider(courseId));
    final cards = ref.watch(dueFlashcardsProvider(courseId));
    final questions = ref.watch(courseQuestionsProvider(courseId));
    final errors = ref.watch(courseErrorsProvider(courseId));

    return DefaultTabController(
      length: 4,
      child: Scaffold(
        appBar: AppBar(
          title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title),
            Text('Espace d’apprentissage', style: Theme.of(context).textTheme.labelMedium),
          ]),
          bottom: const TabBar(
            isScrollable: true,
            tabs: [
              Tab(text: 'Résumé'),
              Tab(text: 'Flashcards'),
              Tab(text: 'Quiz'),
              Tab(text: 'Mes erreurs'),
            ],
          ),
        ),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: () => context.push('/assistant?courseId=$courseId&subjectDomain=general'),
          icon: const Icon(Icons.psychology_alt_rounded),
          label: const Text('Assistant'),
        ),
        body: TabBarView(children: [
          _SummaryView(value: summaries, courseId: courseId),
          _CountView(
            icon: Icons.style_rounded,
            title: 'Révision espacée',
            subtitle: 'Les cartes difficiles reviennent plus vite. Les notions maîtrisées s’espacent.',
            value: cards,
            label: 'cartes à revoir',
            onStart: () => context.push('/study/$courseId/flashcards?title=${Uri.encodeComponent(title)}'),
          ),
          _CountView(
            icon: Icons.quiz_rounded,
            title: 'Teste ta maîtrise',
            subtitle: 'Questions, correction expliquée et renvoi vers le cours quand une notion bloque.',
            value: questions,
            label: 'questions disponibles',
            onStart: () => context.push('/study/$courseId/quiz?title=${Uri.encodeComponent(title)}'),
          ),
          _ErrorsView(value: errors),
        ]),
      ),
    );
  }
}

class _SummaryView extends StatelessWidget {
  const _SummaryView({required this.value, required this.courseId});
  final AsyncValue<List<StudySummary>> value;
  final String courseId;

  @override
  Widget build(BuildContext context) => value.when(
    loading: () => const Center(child: CircularProgressIndicator()),
    error: (e, _) => _StateCard(icon: Icons.error_outline_rounded, title: 'Résumé indisponible', body: e.toString()),
    data: (items) {
      if (items.isEmpty) {
        return const _StateCard(
          icon: Icons.auto_awesome_rounded,
          title: 'Aucun résumé préparé',
          body: 'Dès que le cours est analysé, EduNova proposera un résumé express, un résumé complet et les points essentiels.',
        );
      }
      return ListView(
        padding: const EdgeInsets.fromLTRB(18, 18, 18, 40),
        children: items.map((item) => Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  _Pill(text: _summaryLabel(item.kind)),
                  const Spacer(),
                  Icon(Icons.schedule_rounded, size: 16, color: Theme.of(context).colorScheme.primary),
                  const SizedBox(width: 5),
                  Text('${item.estimatedMinutes} min'),
                ]),
                const SizedBox(height: 14),
                Text(item.title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
                const SizedBox(height: 10),
                Text(item.bodyMarkdown, maxLines: 8, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 16),
                Row(children: [
                  const Icon(Icons.verified_rounded, size: 18),
                  const SizedBox(width: 6),
                  Expanded(child: Text('${item.sources.length} source(s) liée(s)', style: Theme.of(context).textTheme.labelLarge)),
                  IconButton.filledTonal(onPressed: () => context.push('/audio/$courseId'), tooltip: 'Écouter', icon: const Icon(Icons.headphones_rounded)),
                ]),
              ]),
            ),
          ),
        )).toList(growable: false),
      );
    },
  );

  static String _summaryLabel(SummaryKind kind) => switch (kind) {
    SummaryKind.express => 'EXPRESS',
    SummaryKind.complete => 'COMPLET',
    SummaryKind.keyPoints => 'À RETENIR',
  };
}

class _CountView<T> extends StatelessWidget {
  const _CountView({required this.icon, required this.title, required this.subtitle, required this.value, required this.label, required this.onStart});
  final IconData icon;
  final String title;
  final String subtitle;
  final AsyncValue<List<T>> value;
  final String label;
  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) => value.when(
    loading: () => const Center(child: CircularProgressIndicator()),
    error: (e, _) => _StateCard(icon: Icons.error_outline_rounded, title: 'Chargement impossible', body: e.toString()),
    data: (items) => ListView(
      padding: const EdgeInsets.all(18),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              CircleAvatar(radius: 28, child: Icon(icon, size: 28)),
              const SizedBox(height: 18),
              Text(title, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              Text(subtitle),
              const SizedBox(height: 22),
              Text('${items.length}', style: Theme.of(context).textTheme.displaySmall?.copyWith(fontWeight: FontWeight.w900)),
              Text(label),
              const SizedBox(height: 22),
              FilledButton.icon(
                onPressed: items.isEmpty ? null : onStart,
                icon: const Icon(Icons.play_arrow_rounded),
                label: const Text('Commencer'),
              ),
            ]),
          ),
        ),
      ],
    ),
  );
}

class _ErrorsView extends StatelessWidget {
  const _ErrorsView({required this.value});
  final AsyncValue<List<LearningError>> value;

  @override
  Widget build(BuildContext context) => value.when(
    loading: () => const Center(child: CircularProgressIndicator()),
    error: (e, _) => _StateCard(icon: Icons.error_outline_rounded, title: 'Erreurs indisponibles', body: e.toString()),
    data: (items) {
      if (items.isEmpty) {
        return const _StateCard(icon: Icons.check_circle_rounded, title: 'Aucune erreur ouverte', body: 'Les erreurs retravaillées deux fois avec succès quittent automatiquement cette liste.');
      }
      return ListView(
        padding: const EdgeInsets.all(18),
        children: items.map((item) => Card(
          child: ListTile(
            contentPadding: const EdgeInsets.all(18),
            leading: CircleAvatar(child: Text('${item.failureCount}×')),
            title: Text('Question ${item.questionId}', style: const TextStyle(fontWeight: FontWeight.w800)),
            subtitle: Text('Échec(s) : ${item.failureCount} · récupération : ${item.recoveryStreak}/2'),
            trailing: const Icon(Icons.chevron_right_rounded),
          ),
        )).toList(growable: false),
      );
    },
  );
}

class _StateCard extends StatelessWidget {
  const _StateCard({required this.icon, required this.title, required this.body});
  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            CircleAvatar(radius: 30, child: Icon(icon, size: 30)),
            const SizedBox(height: 16),
            Text(title, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            Text(body, textAlign: TextAlign.center),
          ]),
        ),
      ),
    ),
  );
}

class _Pill extends StatelessWidget {
  const _Pill({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.primaryContainer,
      borderRadius: BorderRadius.circular(999),
    ),
    child: Text(text, style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11, color: Theme.of(context).colorScheme.onPrimaryContainer)),
  );
}

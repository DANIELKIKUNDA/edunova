import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../domain/pedagogy.dart';

class FlashcardSessionPage extends ConsumerStatefulWidget {
  const FlashcardSessionPage({super.key, required this.courseId, required this.title});
  final String courseId;
  final String title;

  @override
  ConsumerState<FlashcardSessionPage> createState() => _FlashcardSessionPageState();
}

class _FlashcardSessionPageState extends ConsumerState<FlashcardSessionPage> {
  int _index = 0;
  bool _revealed = false;
  bool _saving = false;
  String? _saveError;

  @override
  Widget build(BuildContext context) {
    final asyncCards = ref.watch(dueFlashcardsProvider(widget.courseId));
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: asyncCards.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Padding(padding: const EdgeInsets.all(24), child: Text(e.toString()))),
        data: (cards) {
          if (cards.isEmpty) {
            return const _DoneState(
              title: 'Révision terminée',
              body: 'Aucune carte n’est due maintenant. EduNova te les représentera au bon moment.',
            );
          }
          final safeIndex = _index.clamp(0, cards.length - 1);
          final card = cards[safeIndex];
          return SafeArea(
            child: Column(children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 6),
                child: Row(children: [
                  Expanded(child: LinearProgressIndicator(value: (safeIndex + 1) / cards.length, minHeight: 8, borderRadius: BorderRadius.circular(99))),
                  const SizedBox(width: 12),
                  Text('${safeIndex + 1}/${cards.length}', style: const TextStyle(fontWeight: FontWeight.w800)),
                ]),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: GestureDetector(
                    onTap: () => setState(() => _revealed = true),
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 240),
                      child: Card(
                        key: ValueKey('${card.id}-$_revealed'),
                        child: Padding(
                          padding: const EdgeInsets.all(28),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Text(_revealed ? 'RÉPONSE' : 'QUESTION', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.2, color: Theme.of(context).colorScheme.primary)),
                              const SizedBox(height: 18),
                              Text(_revealed ? card.back : card.front, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800, height: 1.35)),
                              const SizedBox(height: 24),
                              if (!_revealed) ...[
                                Text('Touchez la carte pour révéler la réponse.', style: Theme.of(context).textTheme.bodyMedium),
                              ] else ...[
                                Row(children: [
                                  const Icon(Icons.source_rounded, size: 18),
                                  const SizedBox(width: 7),
                                  Expanded(child: Text('${card.sources.length} source(s) reliée(s)', style: Theme.of(context).textTheme.labelLarge)),
                                ]),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              if (_saveError != null) Padding(
                padding: const EdgeInsets.symmetric(horizontal: 18),
                child: Text(_saveError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ),
              if (_revealed)
                Padding(
                  padding: const EdgeInsets.fromLTRB(14, 0, 14, 18),
                  child: Row(children: [
                    _RatingButton(label: 'À revoir', icon: Icons.refresh_rounded, onPressed: _saving ? null : () => _rate(card, ReviewRating.again)),
                    _RatingButton(label: 'Difficile', icon: Icons.trending_down_rounded, onPressed: _saving ? null : () => _rate(card, ReviewRating.hard)),
                    _RatingButton(label: 'Correct', icon: Icons.check_rounded, onPressed: _saving ? null : () => _rate(card, ReviewRating.good)),
                    _RatingButton(label: 'Facile', icon: Icons.bolt_rounded, onPressed: _saving ? null : () => _rate(card, ReviewRating.easy)),
                  ]),
                ),
            ]),
          );
        },
      ),
    );
  }

  Future<void> _rate(StudyFlashcard card, ReviewRating rating) async {
    if (_saving) return;
    setState(() { _saving = true; _saveError = null; });
    try {
    final repo = ref.read(pedagogyRepositoryProvider);
    final current = await repo.getFlashcardState(card.id) ?? FlashcardReviewState(flashcardId: card.id);
    final next = ref.read(flashcardSchedulerProvider).review(current, rating);
    await repo.saveFlashcardReview(next, rating: rating, previous: current, reviewedAt: DateTime.now());
    if (!mounted) return;
    setState(() {
      _revealed = false;
      _index += 1;
    });
    } catch (error) {
      if (mounted) setState(() => _saveError = "Révision non enregistrée : $error");
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }
}

class _RatingButton extends StatelessWidget {
  const _RatingButton({required this.label, required this.icon, required this.onPressed});
  final String label;
  final IconData icon;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: FilledButton.tonal(
        onPressed: onPressed,
        style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 14)),
        child: Column(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 20), const SizedBox(height: 4), Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800))]),
      ),
    ),
  );
}

class _DoneState extends StatelessWidget {
  const _DoneState({required this.title, required this.body});
  final String title;
  final String body;
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const CircleAvatar(radius: 34, child: Icon(Icons.done_all_rounded, size: 34)),
        const SizedBox(height: 18),
        Text(title, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        Text(body, textAlign: TextAlign.center),
      ]),
    ),
  );
}

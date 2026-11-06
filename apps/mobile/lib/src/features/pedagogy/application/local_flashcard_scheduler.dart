import '../domain/pedagogy.dart';

class LocalFlashcardScheduler {
  FlashcardReviewState review(FlashcardReviewState state, ReviewRating rating, {DateTime? now}) {
    final anchor = now ?? DateTime.now();
    var repetitions = state.repetitions;
    var ease = state.easeFactor;
    var lapses = state.lapses;
    late int interval;

    switch (rating) {
      case ReviewRating.again:
        interval = 1; repetitions = 0; lapses += 1; ease = (ease - 0.20).clamp(1.3, 3.2).toDouble();
        break;
      case ReviewRating.hard:
        interval = state.intervalDays == 0 ? 1 : (state.intervalDays * 1.2).round().clamp(1, 9999).toInt();
        repetitions += 1; ease = (ease - 0.15).clamp(1.3, 3.2).toDouble();
        break;
      case ReviewRating.good:
        interval = repetitions == 0 ? 1 : repetitions == 1 ? 3 : (state.intervalDays * ease).round().clamp(1, 9999).toInt();
        repetitions += 1;
        break;
      case ReviewRating.easy:
        interval = repetitions == 0 ? 3 : repetitions == 1 ? 7 : (state.intervalDays * ease * 1.3).round().clamp(2, 9999).toInt();
        repetitions += 1; ease = (ease + 0.15).clamp(1.3, 3.2).toDouble();
        break;
    }

    return FlashcardReviewState(
      flashcardId: state.flashcardId,
      repetitions: repetitions,
      easeFactor: double.parse(ease.toStringAsFixed(3)),
      intervalDays: interval,
      dueAt: anchor.add(Duration(days: interval)),
      lapses: lapses,
    );
  }
}

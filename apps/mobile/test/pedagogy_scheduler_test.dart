import 'package:edunova/src/features/pedagogy/application/local_flashcard_scheduler.dart';
import 'package:edunova/src/features/pedagogy/domain/pedagogy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('again resets repetition and records a lapse', () {
    final scheduler = LocalFlashcardScheduler();
    final result = scheduler.review(
      const FlashcardReviewState(flashcardId: 'f1', repetitions: 4, easeFactor: 2.5, intervalDays: 12),
      ReviewRating.again,
      now: DateTime(2026, 9, 20),
    );
    expect(result.repetitions, 0);
    expect(result.intervalDays, 1);
    expect(result.lapses, 1);
    expect(result.easeFactor, 2.3);
  });

  test('easy accelerates interval', () {
    final scheduler = LocalFlashcardScheduler();
    final result = scheduler.review(
      const FlashcardReviewState(flashcardId: 'f1', repetitions: 3, easeFactor: 2.5, intervalDays: 10),
      ReviewRating.easy,
      now: DateTime(2026, 9, 20),
    );
    expect(result.intervalDays, 32);
    expect(result.easeFactor, 2.65);
  });
}

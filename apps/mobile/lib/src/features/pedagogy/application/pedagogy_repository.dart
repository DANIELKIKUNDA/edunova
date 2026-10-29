import '../domain/pedagogy.dart';

abstract interface class PedagogyRepository {
  Stream<List<StudySummary>> watchSummaries(String courseId);
  Stream<List<StudyFlashcard>> watchDueFlashcards(String courseId, {DateTime? now});
  Stream<List<StudyQuizQuestion>> watchQuestions(String courseId);
  Stream<List<LearningError>> watchOpenErrors(String courseId);
  Future<FlashcardReviewState?> getFlashcardState(String flashcardId);
  Future<void> saveFlashcardReview(FlashcardReviewState state, {ReviewRating? rating, FlashcardReviewState? previous, DateTime? reviewedAt});
  Future<void> recordQuestionResult({required String questionId, required String courseId, required bool correct, required DateTime at});
  Future<void> saveQuizAnswer({
    required String id,
    required String attemptId,
    required String questionId,
    required String answerJson,
    required bool isCorrect,
    required double score,
    required DateTime answeredAt,
  });
  Future<QuizSessionState?> loadOpenQuizSession(String courseId);
  Future<void> saveQuizSessionState(QuizSessionState state);
  Future<void> closeQuizSession(String attemptId);
  Future<void> saveQuizAttempt({
    required String id,
    required String courseId,
    required int scorePercent,
    required int totalQuestions,
    required int correctQuestions,
    required DateTime startedAt,
    required DateTime completedAt,
  });
}

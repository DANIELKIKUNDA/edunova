import '../../../core/security/local_account_access.dart';
import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';

import '../../../core/database/app_database.dart';
import '../application/pedagogy_repository.dart';
import '../domain/pedagogy.dart';

class DriftPedagogyRepository implements PedagogyRepository {
  final LocalAccountAccess _access = LocalAccountAccess();
  DriftPedagogyRepository(this._db);
  final AppDatabase _db;
  static const _uuid = Uuid();

  Future<void> _enqueue({required String aggregateType, required String aggregateId, required String eventType, required Map<String, Object?> payload}) async {
    await _db.into(_db.localOutboxItems).insert(
      LocalOutboxItemsCompanion.insert(
        id: _uuid.v4(), aggregateType: aggregateType, aggregateId: aggregateId,
        eventType: eventType, payloadJson: jsonEncode(payload), occurredAt: DateTime.now().toUtc(),
      ),
    );
  }

  List<SourceReference> _decodeSources(String value) {
    final rows = (jsonDecode(value) as List).cast<Map<String, dynamic>>();
    return rows.map((row) => SourceReference.fromJson(row)).toList(growable: false);
  }

  @override
  Stream<List<StudySummary>> watchSummaries(String courseId) {
    final query = _db.select(_db.localSummaries)
      ..where((t) => t.courseId.equals(courseId))
      ..orderBy([(t) => OrderingTerm.asc(t.kind)]);
    return _access.protect(query.watch().map((rows) => rows.map((row) => StudySummary(
      id: row.id,
      courseId: row.courseId,
      sectionId: row.sectionId,
      kind: SummaryKind.values.byName(row.kind),
      title: row.title,
      bodyMarkdown: row.bodyMarkdown,
      estimatedMinutes: row.estimatedMinutes,
      status: ContentReviewStatus.values.byName(row.status),
      sources: _decodeSources(row.sourceRefsJson),
    )).toList(growable: false)));
  }

  @override
  Stream<List<StudyFlashcard>> watchDueFlashcards(String courseId, {DateTime? now}) {
    final anchor = now ?? DateTime.now();
    final cards = _db.localFlashcards;
    final states = _db.localFlashcardStates;
    final query = _db.select(cards).join([
      leftOuterJoin(states, states.flashcardId.equalsExp(cards.id)),
    ])
      ..where(cards.courseId.equals(courseId))
      ..where(states.dueAt.isNull() | states.dueAt.isSmallerOrEqualValue(anchor));
    return query.watch().map((rows) => rows.map((joined) {
      final row = joined.readTable(cards);
      return StudyFlashcard(
        id: row.id,
        courseId: row.courseId,
        sectionId: row.sectionId,
        front: row.front,
        back: row.back,
        difficulty: row.difficulty,
        sources: _decodeSources(row.sourceRefsJson),
      );
    }).toList(growable: false));
  }

  @override
  Stream<List<StudyQuizQuestion>> watchQuestions(String courseId) {
    final query = _db.select(_db.localQuizQuestions)
      ..where((t) => t.courseId.equals(courseId));
    return _access.protect(query.watch().map((rows) => rows.map((row) {
      final optionRows = (jsonDecode(row.optionsJson) as List).cast<Map<String, dynamic>>();
      return StudyQuizQuestion(
        id: row.id,
        courseId: row.courseId,
        sectionId: row.sectionId,
        kind: QuizQuestionKind.values.byName(row.kind),
        prompt: row.prompt,
        options: optionRows.map((item) => QuizOption(id: item['id'] as String, text: item['text'] as String)).toList(growable: false),
        answerJson: row.answerJson,
        explanation: row.explanation,
        difficulty: row.difficulty,
        sources: _decodeSources(row.sourceRefsJson),
      );
    }).toList(growable: false)));
  }

  @override
  Stream<List<LearningError>> watchOpenErrors(String courseId) {
    final query = _db.select(_db.localErrorLedgerItems)
      ..where((t) => t.courseId.equals(courseId) & t.recoveredAt.isNull())
      ..orderBy([(t) => OrderingTerm.desc(t.lastFailedAt)]);
    return _access.protect(query.watch().map((rows) => rows.map((row) => LearningError(
      questionId: row.questionId,
      courseId: row.courseId,
      failureCount: row.failureCount,
      recoveryStreak: row.recoveryStreak,
      firstFailedAt: row.firstFailedAt,
      lastFailedAt: row.lastFailedAt,
      recoveredAt: row.recoveredAt,
    )).toList(growable: false)));
  }

  @override
  Future<FlashcardReviewState?> getFlashcardState(String flashcardId) async {
    await _access.assertOwned();
    final query = _db.select(_db.localFlashcardStates)..where((t) => t.flashcardId.equals(flashcardId));
    final row = await query.getSingleOrNull();
    if (row == null) return null;
    return FlashcardReviewState(
      flashcardId: row.flashcardId,
      repetitions: row.repetitions,
      easeFactor: row.easeFactor,
      intervalDays: row.intervalDays,
      dueAt: row.dueAt,
      lapses: row.lapses,
    );
  }

  @override
  Future<void> saveFlashcardReview(FlashcardReviewState state, {ReviewRating? rating, FlashcardReviewState? previous, DateTime? reviewedAt}) async {
    final at = (reviewedAt ?? DateTime.now()).toUtc();
    await _db.transaction(() async {
      await _db.into(_db.localFlashcardStates).insertOnConflictUpdate(
        LocalFlashcardStatesCompanion.insert(
          flashcardId: state.flashcardId, repetitions: Value(state.repetitions),
          easeFactor: Value(state.easeFactor), intervalDays: Value(state.intervalDays),
          dueAt: Value(state.dueAt), lapses: Value(state.lapses),
        ),
      );
      if (rating != null) {
        await _db.into(_db.localFlashcardReviewEvents).insert(
          LocalFlashcardReviewEventsCompanion.insert(
            id: _uuid.v4(), flashcardId: state.flashcardId, rating: rating.name,
            intervalBeforeDays: previous?.intervalDays ?? 0, intervalAfterDays: state.intervalDays,
            reviewedAt: at, dueAtAfter: Value(state.dueAt),
          ),
        );
        await _enqueue(
          aggregateType: 'flashcard', aggregateId: state.flashcardId, eventType: 'pedagogy.flashcard.reviewed',
          payload: {'rating': rating.name, 'repetitions': state.repetitions, 'intervalDays': state.intervalDays, 'dueAt': state.dueAt?.toUtc().toIso8601String(), 'lapses': state.lapses},
        );
      }
    });
  }

  @override
  Future<void> recordQuestionResult({required String questionId, required String courseId, required bool correct, required DateTime at}) async {
    final query = _db.select(_db.localErrorLedgerItems)..where((t) => t.questionId.equals(questionId));
    final current = await query.getSingleOrNull();
    await _db.transaction(() async {
      if (!correct) {
        await _db.into(_db.localErrorLedgerItems).insertOnConflictUpdate(
          LocalErrorLedgerItemsCompanion.insert(
            questionId: questionId, courseId: courseId, firstFailedAt: current?.firstFailedAt ?? at, lastFailedAt: at,
            failureCount: Value((current?.failureCount ?? 0) + 1), recoveryStreak: const Value(0), recoveredAt: const Value(null),
          ),
        );
      } else if (current != null) {
        final streak = current.recoveryStreak + 1;
        await _db.into(_db.localErrorLedgerItems).insertOnConflictUpdate(
          LocalErrorLedgerItemsCompanion.insert(
            questionId: current.questionId, courseId: current.courseId, firstFailedAt: current.firstFailedAt, lastFailedAt: current.lastFailedAt,
            failureCount: Value(current.failureCount), recoveryStreak: Value(streak), recoveredAt: Value(streak >= 2 ? at : null),
          ),
        );
      }
      await _enqueue(
        aggregateType: 'question', aggregateId: questionId, eventType: 'pedagogy.question.answered',
        payload: {'courseId': courseId, 'correct': correct, 'answeredAt': at.toUtc().toIso8601String()},
      );
    });
  }

  @override
  Future<void> saveQuizAnswer({required String id, required String attemptId, required String questionId, required String answerJson, required bool isCorrect, required double score, required DateTime answeredAt}) async {
    await _db.transaction(() async {
      await _db.into(_db.localQuizAnswers).insertOnConflictUpdate(
        LocalQuizAnswersCompanion.insert(
          id: id, attemptId: attemptId, questionId: questionId, answerJson: answerJson,
          isCorrect: isCorrect, score: score, answeredAt: answeredAt,
        ),
      );
      await _enqueue(
        aggregateType: 'quizAttempt', aggregateId: attemptId, eventType: 'pedagogy.quiz.answer.saved',
        payload: {'answerId': id, 'questionId': questionId, 'correct': isCorrect, 'score': score, 'answeredAt': answeredAt.toUtc().toIso8601String()},
      );
    });
  }

  @override
  Future<QuizSessionState?> loadOpenQuizSession(String courseId) async {
    await _access.assertOwned();
    final query = _db.select(_db.localQuizSessionStates)
      ..where((t) => t.courseId.equals(courseId) & t.status.equals('inProgress'))
      ..orderBy([(t) => OrderingTerm.desc(t.updatedAt)])
      ..limit(1);
    final row = await query.getSingleOrNull();
    if (row == null) return null;
    return QuizSessionState(
      attemptId: row.attemptId, courseId: row.courseId, mode: row.mode, currentIndex: row.currentIndex,
      selectedAnswersJson: row.selectedAnswersJson, correctCount: row.correctCount, status: row.status,
      startedAt: row.startedAt, updatedAt: row.updatedAt,
    );
  }

  @override
  Future<void> saveQuizSessionState(QuizSessionState state) async {
    await _access.assertOwned();
    await _db.into(_db.localQuizSessionStates).insertOnConflictUpdate(
      LocalQuizSessionStatesCompanion.insert(
        attemptId: state.attemptId, courseId: state.courseId, mode: Value(state.mode), currentIndex: Value(state.currentIndex),
        selectedAnswersJson: Value(state.selectedAnswersJson), correctCount: Value(state.correctCount), status: Value(state.status),
        startedAt: state.startedAt, updatedAt: state.updatedAt,
      ),
    );
  }

  @override
  Future<void> closeQuizSession(String attemptId) async {
    await _access.assertOwned();
    await (_db.update(_db.localQuizSessionStates)..where((t) => t.attemptId.equals(attemptId))).write(
      LocalQuizSessionStatesCompanion(status: const Value('completed'), updatedAt: Value(DateTime.now())),
    );
  }

  @override
  Future<void> saveQuizAttempt({required String id, required String courseId, required int scorePercent, required int totalQuestions, required int correctQuestions, required DateTime startedAt, required DateTime completedAt}) async {
    await _db.transaction(() async {
      await _db.into(_db.localQuizAttempts).insertOnConflictUpdate(
        LocalQuizAttemptsCompanion.insert(
          id: id, courseId: courseId, scorePercent: scorePercent, totalQuestions: totalQuestions, correctQuestions: correctQuestions,
          startedAt: startedAt, completedAt: completedAt,
        ),
      );
      await closeQuizSession(id);
      await _enqueue(
        aggregateType: 'quizAttempt', aggregateId: id, eventType: 'pedagogy.quiz.completed',
        payload: {'courseId': courseId, 'scorePercent': scorePercent, 'totalQuestions': totalQuestions, 'correctQuestions': correctQuestions, 'startedAt': startedAt.toUtc().toIso8601String(), 'completedAt': completedAt.toUtc().toIso8601String()},
      );
    });
  }


}

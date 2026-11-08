import 'dart:convert';

enum SummaryKind { express, complete, keyPoints }
enum ContentReviewStatus { draftAi, reviewRequired, approved, published, rejected }
enum ReviewRating { again, hard, good, easy }
enum QuizQuestionKind { singleChoice, multipleChoice, trueFalse, numeric, freeText }

class SourceReference {
  const SourceReference({required this.documentId, required this.chunkId, required this.startPage, required this.endPage, this.excerpt = ''});
  final String documentId;
  final String chunkId;
  final int startPage;
  final int endPage;
  final String excerpt;

  Map<String, Object?> toJson() => {
    'documentId': documentId, 'chunkId': chunkId, 'startPage': startPage, 'endPage': endPage, 'excerpt': excerpt,
  };

  static SourceReference fromJson(Map<String, Object?> json) => SourceReference(
    documentId: json['documentId'] as String,
    chunkId: json['chunkId'] as String,
    startPage: json['startPage'] as int,
    endPage: json['endPage'] as int,
    excerpt: (json['excerpt'] as String?) ?? '',
  );
}

class StudySummary {
  const StudySummary({required this.id, required this.courseId, required this.kind, required this.title, required this.bodyMarkdown, required this.estimatedMinutes, required this.status, required this.sources, this.sectionId});
  final String id;
  final String courseId;
  final String? sectionId;
  final SummaryKind kind;
  final String title;
  final String bodyMarkdown;
  final int estimatedMinutes;
  final ContentReviewStatus status;
  final List<SourceReference> sources;
}

class StudyFlashcard {
  const StudyFlashcard({required this.id, required this.courseId, required this.front, required this.back, required this.difficulty, required this.sources, this.sectionId});
  final String id;
  final String courseId;
  final String? sectionId;
  final String front;
  final String back;
  final int difficulty;
  final List<SourceReference> sources;
}

class FlashcardReviewState {
  const FlashcardReviewState({required this.flashcardId, this.repetitions = 0, this.easeFactor = 2.5, this.intervalDays = 0, this.dueAt, this.lapses = 0});
  final String flashcardId;
  final int repetitions;
  final double easeFactor;
  final int intervalDays;
  final DateTime? dueAt;
  final int lapses;
}

class QuizOption {
  const QuizOption({required this.id, required this.text});
  final String id;
  final String text;
  Map<String, String> toJson() => {'id': id, 'text': text};
}

class StudyQuizQuestion {
  const StudyQuizQuestion({required this.id, required this.courseId, required this.kind, required this.prompt, required this.options, required this.answerJson, required this.explanation, required this.difficulty, required this.sources, this.sectionId});
  final String id;
  final String courseId;
  final String? sectionId;
  final QuizQuestionKind kind;
  final String prompt;
  final List<QuizOption> options;
  final String answerJson;
  final String explanation;
  final int difficulty;
  final List<SourceReference> sources;

  Map<String, dynamic> get answerPayload => jsonDecode(answerJson) as Map<String, dynamic>;

  List<String> get correctOptionIds => ((answerPayload['correctOptionIds'] as List?) ?? const []).cast<String>();
}

class LearningError {
  const LearningError({required this.questionId, required this.courseId, required this.failureCount, required this.recoveryStreak, required this.firstFailedAt, required this.lastFailedAt, this.recoveredAt});
  final String questionId;
  final String courseId;
  final int failureCount;
  final int recoveryStreak;
  final DateTime firstFailedAt;
  final DateTime lastFailedAt;
  final DateTime? recoveredAt;
  bool get isRecovered => recoveredAt != null;
}


class QuizSessionState {
  const QuizSessionState({
    required this.attemptId,
    required this.courseId,
    required this.currentIndex,
    required this.correctCount,
    required this.startedAt,
    required this.updatedAt,
    this.mode = 'practice',
    this.selectedAnswersJson = '{}',
    this.status = 'inProgress',
  });
  final String attemptId;
  final String courseId;
  final String mode;
  final int currentIndex;
  final String selectedAnswersJson;
  final int correctCount;
  final String status;
  final DateTime startedAt;
  final DateTime updatedAt;
}

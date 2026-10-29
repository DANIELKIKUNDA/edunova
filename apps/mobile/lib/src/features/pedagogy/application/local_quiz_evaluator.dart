import 'dart:math' as math;

import '../domain/pedagogy.dart';

class LocalAnswerEvaluation {
  const LocalAnswerEvaluation({required this.correct, required this.score});
  final bool correct;
  final double score;
}

class LocalQuizEvaluator {
  const LocalQuizEvaluator();

  LocalAnswerEvaluation evaluate({
    required StudyQuizQuestion question,
    Set<String> selectedOptionIds = const {},
    String? textValue,
    double? numericValue,
  }) {
    final payload = question.answerPayload;
    switch (question.kind) {
      case QuizQuestionKind.singleChoice:
      case QuizQuestionKind.trueFalse:
        final expected = question.correctOptionIds.toSet();
        final correct = expected.length == selectedOptionIds.length && expected.containsAll(selectedOptionIds);
        return LocalAnswerEvaluation(correct: correct, score: correct ? 1 : 0);
      case QuizQuestionKind.multipleChoice:
        final expected = question.correctOptionIds.toSet();
        final actual = selectedOptionIds;
        if (expected.isEmpty && actual.isEmpty) {
          return const LocalAnswerEvaluation(correct: true, score: 1);
        }
        final truePositive = expected.intersection(actual).length;
        final falsePositive = actual.difference(expected).length;
        final falseNegative = expected.difference(actual).length;
        final raw = (truePositive - .25 * falsePositive - .25 * falseNegative) / math.max(1, expected.length);
        final score = raw.clamp(0.0, 1.0).toDouble();
        return LocalAnswerEvaluation(correct: score >= .999, score: score);
      case QuizQuestionKind.numeric:
        if (numericValue == null) return const LocalAnswerEvaluation(correct: false, score: 0);
        final expected = (payload['expectedNumeric'] as num?)?.toDouble();
        if (expected == null) return const LocalAnswerEvaluation(correct: false, score: 0);
        final absTolerance = ((payload['numericTolerance'] as num?) ?? 0).toDouble();
        final relTolerance = ((payload['relativeTolerance'] as num?) ?? 0).toDouble();
        final allowed = math.max(absTolerance, expected.abs() * relTolerance);
        final correct = (numericValue - expected).abs() <= allowed;
        return LocalAnswerEvaluation(correct: correct, score: correct ? 1 : 0);
      case QuizQuestionKind.freeText:
        final actual = _normalize(textValue ?? '');
        final accepted = <String>{
          if (payload['expectedText'] is String) _normalize(payload['expectedText'] as String),
          ...((payload['acceptedTextAnswers'] as List?) ?? const []).whereType<String>().map(_normalize),
        }..remove('');
        final correct = actual.isNotEmpty && accepted.contains(actual);
        return LocalAnswerEvaluation(correct: correct, score: correct ? 1 : 0);
    }
  }

  String _normalize(String value) => value.trim().toLowerCase().replaceAll(RegExp(r'\s+'), ' ');
}

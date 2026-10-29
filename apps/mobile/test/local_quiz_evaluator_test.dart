import 'package:edunova/src/features/pedagogy/application/local_quiz_evaluator.dart';
import 'package:edunova/src/features/pedagogy/domain/pedagogy.dart';
import 'package:flutter_test/flutter_test.dart';

StudyQuizQuestion q(QuizQuestionKind kind, String answerJson, {List<QuizOption> options = const []}) => StudyQuizQuestion(
  id: 'q', courseId: 'c', kind: kind, prompt: 'Question valide et suffisamment longue ?', options: options,
  answerJson: answerJson, explanation: 'Explication', difficulty: 3, sources: const [],
);

void main() {
  const evaluator = LocalQuizEvaluator();
  test('multiple choice partial scoring penalizes guessing', () {
    final question = q(QuizQuestionKind.multipleChoice, '{"correctOptionIds":["A","B"]}', options: const [QuizOption(id:'A',text:'a'),QuizOption(id:'B',text:'b'),QuizOption(id:'C',text:'c')]);
    final result = evaluator.evaluate(question: question, selectedOptionIds: {'A','C'});
    expect(result.correct, isFalse);
    expect(result.score, greaterThan(0));
    expect(result.score, lessThan(1));
  });

  test('numeric supports absolute tolerance', () {
    final question = q(QuizQuestionKind.numeric, '{"expectedNumeric":9.81,"numericTolerance":0.02}');
    expect(evaluator.evaluate(question: question, numericValue: 9.80).correct, isTrue);
  });

  test('free text supports accepted variants', () {
    final question = q(QuizQuestionKind.freeText, '{"expectedText":"sodium","acceptedTextAnswers":["Na+"]}');
    expect(evaluator.evaluate(question: question, textValue: 'Na+').correct, isTrue);
  });
}

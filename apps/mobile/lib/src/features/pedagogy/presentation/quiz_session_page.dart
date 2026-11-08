import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../../core/di/providers.dart';
import '../application/local_quiz_evaluator.dart';
import '../domain/pedagogy.dart';

class QuizSessionPage extends ConsumerStatefulWidget {
  const QuizSessionPage({super.key, required this.courseId, required this.title});
  final String courseId;
  final String title;

  @override
  ConsumerState<QuizSessionPage> createState() => _QuizSessionPageState();
}

class _QuizSessionPageState extends ConsumerState<QuizSessionPage> {
  int _index = 0;
  final Set<String> _selectedIds = {};
  final TextEditingController _textController = TextEditingController();
  bool _checked = false;
  int _correct = 0;
  String _attemptId = const Uuid().v4();
  DateTime _startedAt = DateTime.now();
  bool _sessionReady = false;
  bool _saving = false;
  String? _operationError;

  @override
  void initState() {
    super.initState();
    Future.microtask(_restoreOrCreateSession);
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _restoreOrCreateSession() async {
    try {
    final repo = ref.read(pedagogyRepositoryProvider);
    final existing = await repo.loadOpenQuizSession(widget.courseId);
    if (existing != null) {
      _attemptId = existing.attemptId;
      _startedAt = existing.startedAt;
      _index = existing.currentIndex;
      _correct = existing.correctCount;
    } else {
      final now = DateTime.now();
      await repo.saveQuizSessionState(QuizSessionState(
        attemptId: _attemptId,
        courseId: widget.courseId,
        currentIndex: 0,
        correctCount: 0,
        startedAt: now,
        updatedAt: now,
      ));
    }
    if (!mounted) return;
    setState(() => _sessionReady = true);
    } catch (error) {
      if (!mounted) return;
      setState(() => _operationError = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final asyncQuestions = ref.watch(courseQuestionsProvider(widget.courseId));
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: _operationError != null && !_sessionReady
          ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Text("Impossible de reprendre le quiz."),
              TextButton(onPressed: () { setState(() => _operationError = null); _restoreOrCreateSession(); }, child: const Text("Réessayer")),
            ]))
          : !_sessionReady
          ? const Center(child: CircularProgressIndicator())
          : asyncQuestions.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text(e.toString())),
              data: (questions) {
                if (questions.isEmpty) {
                  return const Center(child: Padding(padding: EdgeInsets.all(24), child: Text('Aucune question disponible pour ce cours.')));
                }
                if (_index >= questions.length) {
                  final percent = (_correct / questions.length * 100).round();
                  return _ResultState(score: percent, correct: _correct, total: questions.length);
                }
                final question = questions[_index];
                final evaluation = _currentEvaluation(question);
                return ListView(
                  padding: const EdgeInsets.fromLTRB(18, 18, 18, 36),
                  children: [
                    Row(children: [
                      Expanded(child: LinearProgressIndicator(value: (_index + 1) / questions.length, minHeight: 8, borderRadius: BorderRadius.circular(99))),
                      const SizedBox(width: 12),
                      Text('${_index + 1}/${questions.length}', style: const TextStyle(fontWeight: FontWeight.w900)),
                    ]),
                    const SizedBox(height: 20),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(22),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Row(children: [
                            Text('QUESTION ${_index + 1}', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.1, color: Theme.of(context).colorScheme.primary)),
                            const Spacer(),
                            _KindChip(kind: question.kind),
                          ]),
                          const SizedBox(height: 14),
                          Text(question.prompt, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900, height: 1.35)),
                        ]),
                      ),
                    ),
                    const SizedBox(height: 14),
                    ..._answerWidgets(question),
                    if (_checked) ...[
                      const SizedBox(height: 8),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Row(children: [
                              Icon(evaluation.correct ? Icons.check_circle_rounded : Icons.lightbulb_rounded),
                              const SizedBox(width: 8),
                              Text(evaluation.correct ? 'Bonne réponse' : 'À revoir', style: const TextStyle(fontWeight: FontWeight.w900)),
                            ]),
                            const SizedBox(height: 10),
                            Text(question.explanation.isEmpty ? 'Consulte le passage source pour consolider cette notion.' : question.explanation),
                            const SizedBox(height: 12),
                            Text('${question.sources.length} source(s) reliée(s)', style: Theme.of(context).textTheme.labelLarge),
                          ]),
                        ),
                      ),
                    ],
                    const SizedBox(height: 18),
                    if (_operationError != null) Text(_operationError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                    FilledButton(
                      onPressed: _saving || !_hasAnswer(question)
                          ? null
                          : _checked
                              ? () => _next(questions.length)
                              : () => _check(question, evaluation),
                      child: Text(_saving ? 'Enregistrement…' : _checked ? 'Question suivante' : 'Vérifier'),
                    ),
                  ],
                );
              },
            ),
    );
  }

  List<Widget> _answerWidgets(StudyQuizQuestion question) {
    switch (question.kind) {
      case QuizQuestionKind.singleChoice:
      case QuizQuestionKind.trueFalse:
        return [RadioGroup<String>(
          groupValue: _selectedIds.isEmpty ? null : _selectedIds.first,
          onChanged: (value) {
            if (_checked || value == null) return;
            setState(() { _selectedIds..clear()..add(value); });
          },
          child: Column(children: question.options.map((option) => _singleOption(question, option)).toList(growable: false)),
        )];
      case QuizQuestionKind.multipleChoice:
        return question.options.map((option) => _multipleOption(question, option)).toList(growable: false);
      case QuizQuestionKind.numeric:
        return [
          TextField(
            controller: _textController,
            enabled: !_checked,
            keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
            decoration: const InputDecoration(labelText: 'Ta réponse numérique', border: OutlineInputBorder()),
            onChanged: (_) => setState(() {}),
          ),
        ];
      case QuizQuestionKind.freeText:
        return [
          TextField(
            controller: _textController,
            enabled: !_checked,
            minLines: 2,
            maxLines: 5,
            decoration: const InputDecoration(labelText: 'Ta réponse', border: OutlineInputBorder()),
            onChanged: (_) => setState(() {}),
          ),
        ];
    }
  }

  Widget _singleOption(StudyQuizQuestion question, QuizOption option) {
    final selected = _selectedIds.contains(option.id);
    final shouldShowCorrect = _checked && question.correctOptionIds.contains(option.id);
    final shouldShowWrong = _checked && selected && !question.correctOptionIds.contains(option.id);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Card(
        child: RadioListTile<String>(
          value: option.id,
          enabled: !_checked,
          secondary: shouldShowCorrect ? const Icon(Icons.check_circle_rounded) : shouldShowWrong ? const Icon(Icons.cancel_rounded) : null,
          title: Text(option.text, style: const TextStyle(fontWeight: FontWeight.w700)),
        ),
      ),
    );
  }

  Widget _multipleOption(StudyQuizQuestion question, QuizOption option) {
    final selected = _selectedIds.contains(option.id);
    final shouldShowCorrect = _checked && question.correctOptionIds.contains(option.id);
    final shouldShowWrong = _checked && selected && !question.correctOptionIds.contains(option.id);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Card(
        child: CheckboxListTile(
          value: selected,
          onChanged: _checked ? null : (value) => setState(() { value == true ? _selectedIds.add(option.id) : _selectedIds.remove(option.id); }),
          secondary: shouldShowCorrect ? const Icon(Icons.check_circle_rounded) : shouldShowWrong ? const Icon(Icons.cancel_rounded) : null,
          title: Text(option.text, style: const TextStyle(fontWeight: FontWeight.w700)),
        ),
      ),
    );
  }

  bool _hasAnswer(StudyQuizQuestion question) {
    if (question.kind == QuizQuestionKind.numeric || question.kind == QuizQuestionKind.freeText) {
      return _textController.text.trim().isNotEmpty;
    }
    return _selectedIds.isNotEmpty;
  }

  LocalAnswerEvaluation _currentEvaluation(StudyQuizQuestion question) {
    final normalizedNumeric = double.tryParse(_textController.text.trim().replaceAll(',', '.'));
    return ref.read(localQuizEvaluatorProvider).evaluate(
      question: question,
      selectedOptionIds: _selectedIds,
      textValue: _textController.text,
      numericValue: normalizedNumeric,
    );
  }

  Future<void> _check(StudyQuizQuestion question, LocalAnswerEvaluation evaluation) async {
    if (_saving || _checked) return;
    setState(() { _saving = true; _operationError = null; });
    try {
    final now = DateTime.now();
    final repo = ref.read(pedagogyRepositoryProvider);
    await repo.recordQuestionResult(questionId: question.id, courseId: question.courseId, correct: evaluation.correct, at: now);
    await repo.saveQuizAnswer(
      id: const Uuid().v4(),
      attemptId: _attemptId,
      questionId: question.id,
      answerJson: jsonEncode({
        'selectedOptionIds': _selectedIds.toList(growable: false),
        'textValue': _textController.text.trim().isEmpty ? null : _textController.text.trim(),
      }),
      isCorrect: evaluation.correct,
      score: evaluation.score,
      answeredAt: now,
    );
    final nextCorrect = _correct + (evaluation.correct ? 1 : 0);
    await repo.saveQuizSessionState(QuizSessionState(
      attemptId: _attemptId,
      courseId: widget.courseId,
      currentIndex: _index + 1,
      correctCount: nextCorrect,
      startedAt: _startedAt,
      updatedAt: now,
    ));
    if (!mounted) return;
    setState(() {
      _checked = true;
      _correct = nextCorrect;
    });
    } catch (error) {
      if (mounted) setState(() => _operationError = "Enregistrement impossible : $error");
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _next(int totalQuestions) async {
    if (_saving) return;
    setState(() { _saving = true; _operationError = null; });
    try {
    final isLast = _index + 1 >= totalQuestions;
    if (isLast) {
      await ref.read(pedagogyRepositoryProvider).saveQuizAttempt(
        id: _attemptId,
        courseId: widget.courseId,
        scorePercent: totalQuestions == 0 ? 0 : (_correct / totalQuestions * 100).round(),
        totalQuestions: totalQuestions,
        correctQuestions: _correct,
        startedAt: _startedAt,
        completedAt: DateTime.now(),
      );
    }
    if (!mounted) return;
    setState(() {
      _index += 1;
      _selectedIds.clear();
      _textController.clear();
      _checked = false;
    });
    } catch (error) {
      if (mounted) setState(() => _operationError = "Finalisation impossible : $error");
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }
}

class _KindChip extends StatelessWidget {
  const _KindChip({required this.kind});
  final QuizQuestionKind kind;

  @override
  Widget build(BuildContext context) {
    final label = switch (kind) {
      QuizQuestionKind.singleChoice => 'QCM',
      QuizQuestionKind.multipleChoice => 'MULTI',
      QuizQuestionKind.trueFalse => 'V/F',
      QuizQuestionKind.numeric => 'NUM',
      QuizQuestionKind.freeText => 'TEXTE',
    };
    return Chip(label: Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w900)), visualDensity: VisualDensity.compact);
  }
}

class _ResultState extends StatelessWidget {
  const _ResultState({required this.score, required this.correct, required this.total});
  final int score;
  final int correct;
  final int total;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(30),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            CircleAvatar(radius: 36, child: Text('$score%', style: const TextStyle(fontWeight: FontWeight.w900))),
            const SizedBox(height: 18),
            Text('Session terminée', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            Text('$correct bonne(s) réponse(s) sur $total', textAlign: TextAlign.center),
            const SizedBox(height: 10),
            const Text('Les erreurs restent dans « Mes erreurs » jusqu’à deux réussites consécutives.', textAlign: TextAlign.center),
          ]),
        ),
      ),
    ),
  );
}

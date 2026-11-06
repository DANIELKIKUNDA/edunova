from datetime import datetime, timezone

import pytest

from app.modules.pedagogy.domain.model import (
    AdaptiveReadinessCalculator,
    Answer,
    ErrorLedger,
    ErrorItem,
    FlashcardScheduler,
    FlashcardState,
    PreparationSignals,
    QuestionKind,
    QuestionOption,
    QuizEvaluator,
    QuizQuestion,
    ReviewRating,
)
from app.shared.domain.errors import ValidationError

NOW = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)


def _single_question() -> QuizQuestion:
    return QuizQuestion(
        id="q1",
        course_id="c1",
        section_id="s1",
        kind=QuestionKind.SINGLE_CHOICE,
        prompt="Quel ion domine la dépolarisation ?",
        options=(QuestionOption("A", "Na+"), QuestionOption("B", "K+")),
        correct_option_ids=("A",),
        explanation="L'entrée de Na+ domine la phase ascendante.",
    )


def test_scheduler_again_resets_and_counts_lapse():
    state = FlashcardState("f1", repetitions=4, ease_factor=2.5, interval_days=12)
    result = FlashcardScheduler().review(state, ReviewRating.AGAIN, now=NOW)
    assert result.state.interval_days == 1
    assert result.state.repetitions == 0
    assert result.state.lapses == 1
    assert result.state.ease_factor == 2.3


def test_scheduler_easy_accelerates_interval():
    state = FlashcardState("f1", repetitions=3, ease_factor=2.5, interval_days=10)
    result = FlashcardScheduler().review(state, ReviewRating.EASY, now=NOW)
    assert result.state.interval_days == 32
    assert result.state.ease_factor == 2.65


def test_scheduler_rejects_naive_datetime():
    with pytest.raises(ValidationError):
        FlashcardScheduler().review(FlashcardState("f1"), ReviewRating.GOOD, now=datetime(2026, 1, 1))


def test_single_choice_evaluation():
    question = _single_question()
    evaluator = QuizEvaluator()
    assert evaluator.evaluate(question, Answer(selected_option_ids=("A",))).correct is True
    assert evaluator.evaluate(question, Answer(selected_option_ids=("B",))).correct is False


def test_multiple_choice_partial_score_penalizes_guessing():
    question = QuizQuestion(
        id="q2",
        course_id="c1",
        section_id=None,
        kind=QuestionKind.MULTIPLE_CHOICE,
        prompt="Choisir les réponses correctes",
        options=(QuestionOption("A", "1"), QuestionOption("B", "2"), QuestionOption("C", "3")),
        correct_option_ids=("A", "B"),
    )
    result = QuizEvaluator().evaluate(question, Answer(selected_option_ids=("A", "C")))
    assert result.correct is False
    assert 0 < result.score < 1


def test_numeric_tolerance():
    question = QuizQuestion(
        id="q3",
        course_id="c1",
        section_id=None,
        kind=QuestionKind.NUMERIC,
        prompt="Valeur ?",
        expected_numeric=9.81,
        numeric_tolerance=0.02,
    )
    assert QuizEvaluator().evaluate(question, Answer(numeric_value=9.80)).correct is True
    assert QuizEvaluator().evaluate(question, Answer(numeric_value=9.7)).correct is False


def test_attempt_aggregates_scores():
    question = _single_question()
    result = QuizEvaluator().attempt([question, question], [Answer(selected_option_ids=("A",)), Answer(selected_option_ids=("B",))])
    assert result.total_questions == 2
    assert result.correct_questions == 1
    assert result.score_percent == 50


def test_attempt_rejects_mismatched_lengths():
    with pytest.raises(ValidationError):
        QuizEvaluator().attempt([_single_question()], [])


def test_error_ledger_requires_two_successes_to_recover():
    ledger = ErrorLedger()
    failed = ledger.fail(None, question_id="q1", at=NOW)
    one = ledger.succeed(failed, at=NOW)
    assert one.recovered_at is None
    two = ledger.succeed(one, at=NOW)
    assert two.recovered_at == NOW


def test_new_failure_resets_recovery_streak():
    ledger = ErrorLedger()
    item = ErrorItem("q1", NOW, NOW, failure_count=2, recovery_streak=1)
    result = ledger.fail(item, question_id="q1", at=NOW)
    assert result.failure_count == 3
    assert result.recovery_streak == 0
    assert result.recovered_at is None


def test_adaptive_readiness_renormalizes_missing_signals():
    value = AdaptiveReadinessCalculator().calculate(PreparationSignals(coverage=1.0, quiz_mastery=0.0))
    # (1*0.3 + 0*0.4) / 0.7 = 42.857
    assert value == 43


def test_adaptive_readiness_rejects_no_signal():
    with pytest.raises(ValidationError):
        AdaptiveReadinessCalculator().calculate(PreparationSignals())


def test_numeric_relative_tolerance():
    question = QuizQuestion(
        id="q-rel", course_id="c1", section_id=None, kind=QuestionKind.NUMERIC,
        prompt="Valeur mesurée ?", expected_numeric=100.0, numeric_relative_tolerance=0.02,
    )
    assert QuizEvaluator().evaluate(question, Answer(numeric_value=101.5)).correct is True
    assert QuizEvaluator().evaluate(question, Answer(numeric_value=103.0)).correct is False


def test_free_text_accepts_normalized_variants():
    question = QuizQuestion(
        id="q-text", course_id="c1", section_id=None, kind=QuestionKind.FREE_TEXT,
        prompt="Ion ?", expected_text="Sodium", accepted_text_answers=("Na+", "ion sodium"),
    )
    assert QuizEvaluator().evaluate(question, Answer(text_value="  NA+ ")).correct is True

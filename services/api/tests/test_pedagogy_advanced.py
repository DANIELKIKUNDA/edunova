import pytest

from app.modules.pedagogy.domain.advanced import (
    AdaptivePracticeSelector,
    CognitiveLevel,
    ContentScope,
    ContentVisibilityPolicy,
    LearningObjective,
    MasteryEstimator,
    MasteryEvidence,
    PracticeCandidate,
    QuestionQualityValidator,
)
from app.modules.pedagogy.domain.model import ContentStatus, QuestionKind, QuestionOption, QuizQuestion
from app.shared.domain.errors import ValidationError


def test_shared_content_requires_published_status_but_personal_draft_is_visible():
    policy = ContentVisibilityPolicy()
    assert policy.can_student_view(scope=ContentScope.PLATFORM, status=ContentStatus.REVIEW_REQUIRED) is False
    assert policy.can_student_view(scope=ContentScope.PLATFORM, status=ContentStatus.PUBLISHED) is True
    assert policy.can_student_view(scope=ContentScope.PERSONAL, status=ContentStatus.REVIEW_REQUIRED) is True
    assert policy.can_student_view(scope=ContentScope.PERSONAL, status=ContentStatus.REJECTED) is False


def test_mastery_estimator_is_weighted_and_recency_aware():
    score = MasteryEstimator().calculate([
        MasteryEvidence('obj', score=1.0, weight=1, recency_factor=0.5),
        MasteryEvidence('obj', score=0.0, weight=1, recency_factor=1.0),
    ])
    assert score == 33


def test_learning_objective_cannot_depend_on_itself():
    with pytest.raises(ValidationError):
        LearningObjective('o1', 'c1', None, 'Comprendre', CognitiveLevel.UNDERSTAND, ('o1',))


def test_adaptive_practice_prioritizes_low_mastery_and_errors():
    ranked = AdaptivePracticeSelector().rank([
        PracticeCandidate('strong', 2, mastery=.9, error_count=0, seen_count=3),
        PracticeCandidate('weak', 3, mastery=.2, error_count=3, seen_count=1),
        PracticeCandidate('new', 2, mastery=.6, error_count=0, seen_count=0),
    ])
    assert ranked[0].question_id == 'weak'


def test_question_quality_detects_duplicate_options_and_duplicate_prompts():
    q1 = QuizQuestion(
        id='q1', course_id='c1', section_id=None, kind=QuestionKind.SINGLE_CHOICE,
        prompt='Quel ion domine la dépolarisation ?',
        options=(QuestionOption('A', 'Na+'), QuestionOption('B', 'Na+')),
        correct_option_ids=('A',), explanation='explication',
    )
    q2 = QuizQuestion(
        id='q2', course_id='c1', section_id=None, kind=QuestionKind.SINGLE_CHOICE,
        prompt='Quel ion domine la dépolarisation ?',
        options=(QuestionOption('A', 'Na+'), QuestionOption('B', 'K+')),
        correct_option_ids=('A',), explanation='explication',
    )
    validator = QuestionQualityValidator()
    report = validator.validate(q1)
    assert report.valid is False
    assert 'duplicate_options' in report.warnings
    assert validator.find_duplicates([q1, q2]) == (('q1', 'q2'),)

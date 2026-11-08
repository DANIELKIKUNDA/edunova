import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.readiness.domain.model import ReadinessCalculator, ReadinessInputs


def test_readiness_score_is_explainable_weighted_score() -> None:
    result = ReadinessCalculator().calculate(
        ReadinessInputs(
            coverage=1.0,
            quiz_mastery=0.75,
            flashcard_mastery=0.8,
            weakness_recovery=0.6,
        )
    )
    assert result.value == 81
    assert result.label == "Bien préparé"

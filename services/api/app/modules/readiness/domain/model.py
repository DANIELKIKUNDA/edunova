from dataclasses import dataclass

from app.shared.domain.errors import ValidationError


@dataclass(frozen=True)
class ReadinessInputs:
    coverage: float
    quiz_mastery: float
    flashcard_mastery: float
    weakness_recovery: float

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not 0 <= value <= 1:
                raise ValidationError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class ReadinessScore:
    value: int
    label: str


class ReadinessCalculator:
    """Score de préparation explicable, jamais une prédiction de note."""

    WEIGHTS = {
        "coverage": 0.30,
        "quiz_mastery": 0.40,
        "flashcard_mastery": 0.15,
        "weakness_recovery": 0.15,
    }

    def calculate(self, inputs: ReadinessInputs) -> ReadinessScore:
        raw = (
            inputs.coverage * self.WEIGHTS["coverage"]
            + inputs.quiz_mastery * self.WEIGHTS["quiz_mastery"]
            + inputs.flashcard_mastery * self.WEIGHTS["flashcard_mastery"]
            + inputs.weakness_recovery * self.WEIGHTS["weakness_recovery"]
        )
        value = round(raw * 100)
        if value < 40:
            label = "À renforcer"
        elif value < 70:
            label = "En progression"
        elif value < 90:
            label = "Bien préparé"
        else:
            label = "Très bien préparé"
        return ReadinessScore(value=value, label=label)

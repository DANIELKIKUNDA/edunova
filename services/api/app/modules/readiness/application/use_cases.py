from app.modules.readiness.domain.model import (
    ReadinessCalculator,
    ReadinessInputs,
    ReadinessScore,
)


class CalculateReadiness:
    def __init__(self, calculator: ReadinessCalculator | None = None) -> None:
        self._calculator = calculator or ReadinessCalculator()

    def execute(self, inputs: ReadinessInputs) -> ReadinessScore:
        return self._calculator.calculate(inputs)

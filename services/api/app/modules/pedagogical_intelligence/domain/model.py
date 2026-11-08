from dataclasses import dataclass

@dataclass(frozen=True)
class LearningSignal:
    objective_id: str
    learner_count: int
    assessed_count: int
    mean_score: float | None = None
    failure_count: int = 0
    attendance_rate: float | None = None

@dataclass(frozen=True)
class TeachingInsight:
    objective_id: str
    level: str
    action: str
    reason: str
    evidence: tuple[str, ...]
    confidence: str

@dataclass(frozen=True)
class PedagogicalReport:
    method: str
    predictive_model: bool
    objective_count: int
    insights: tuple[TeachingInsight, ...]

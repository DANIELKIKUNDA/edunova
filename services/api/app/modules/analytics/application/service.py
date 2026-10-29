from __future__ import annotations

from ..domain.engine import AnalyticsEngine
from ..domain.model import AnalyticsReport, AnalyticsSnapshot


class AnalyticsService:
    def __init__(self, engine: AnalyticsEngine | None = None) -> None:
        self.engine = engine or AnalyticsEngine()

    def analyze(self, snapshot: AnalyticsSnapshot) -> AnalyticsReport:
        return self.engine.build(snapshot)

from __future__ import annotations

from datetime import datetime

from app.modules.planning.domain.model import (
    AcademicEvent, CoursePlanningState, DayPlan, EmergencyPlanner, PriorityEngine,
    StudyTaskCandidate, TimeBoxPlanner,
)


class PlanningService:
    def __init__(self) -> None:
        self.priority = PriorityEngine()
        self.timebox = TimeBoxPlanner()
        self.emergency = EmergencyPlanner()

    def today(
        self,
        *,
        now: datetime,
        states: dict[str, CoursePlanningState],
        events: list[AcademicEvent],
        tasks: list[StudyTaskCandidate],
        budget_minutes: int,
        tomorrow_course_ids: set[str] | None = None,
    ) -> DayPlan:
        ranked = self.priority.rank(
            now=now, states=states, events=events, tasks=tasks, tomorrow_course_ids=tomorrow_course_ids,
        )
        return self.timebox.build(now=now, ranked=ranked, budget_minutes=budget_minutes)

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from enum import StrEnum


class EngagementCategory(StrEnum):
    ASSESSMENT = "assessment"
    STUDY_PLAN = "study_plan"
    FLASHCARDS = "flashcards"
    STREAK = "streak"
    CONTENT = "content"
    SYSTEM = "system"


class DeliveryChannel(StrEnum):
    LOCAL = "local"
    PUSH = "push"


@dataclass(frozen=True)
class NotificationPreferences:
    quiet_start_minute: int = 22 * 60
    quiet_end_minute: int = 7 * 60
    max_daily_notifications: int = 2
    assessment_enabled: bool = True
    study_plan_enabled: bool = True
    flashcards_enabled: bool = True
    streak_enabled: bool = False
    content_enabled: bool = True
    push_enabled: bool = True
    preferred_study_minute: int = 19 * 60
    timezone_offset_minutes: int = 0
    daily_goal_minutes: int = 30

    def __post_init__(self):
        if not (0 <= self.quiet_start_minute < 1440 and 0 <= self.quiet_end_minute < 1440):
            raise ValueError("quiet_hours_out_of_range")
        if not (0 <= self.preferred_study_minute < 1440):
            raise ValueError("preferred_study_time_out_of_range")
        if not 0 <= self.max_daily_notifications <= 6:
            raise ValueError("max_daily_notifications_out_of_range")
        if not -840 <= self.timezone_offset_minutes <= 840:
            raise ValueError("timezone_offset_out_of_range")
        if not 5 <= self.daily_goal_minutes <= 240:
            raise ValueError("daily_goal_out_of_range")

    def category_enabled(self, category: EngagementCategory) -> bool:
        return {
            EngagementCategory.ASSESSMENT: self.assessment_enabled,
            EngagementCategory.STUDY_PLAN: self.study_plan_enabled,
            EngagementCategory.FLASHCARDS: self.flashcards_enabled,
            EngagementCategory.STREAK: self.streak_enabled,
            EngagementCategory.CONTENT: self.content_enabled,
            EngagementCategory.SYSTEM: True,
        }[category]


@dataclass(frozen=True)
class NotificationIntent:
    id: str
    account_id: str
    dedupe_key: str
    category: EngagementCategory
    channel: DeliveryChannel
    title: str
    body: str
    deep_link: str
    fire_at: datetime
    expires_at: datetime
    priority: int = 50
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        if self.fire_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("notification_times_must_be_timezone_aware")
        if self.expires_at <= self.fire_at:
            raise ValueError("notification_expiry_must_follow_fire_at")
        if not 0 <= self.priority <= 100:
            raise ValueError("priority_out_of_range")


@dataclass(frozen=True)
class EngagementDay:
    day_key: str
    active_minutes: int = 0
    completed_tasks: int = 0
    quiz_questions: int = 0
    flashcards_reviewed: int = 0

    @property
    def active(self) -> bool:
        return self.active_minutes > 0 or self.completed_tasks > 0 or self.quiz_questions > 0 or self.flashcards_reviewed > 0


@dataclass(frozen=True)
class StreakSummary:
    current_days: int
    best_days: int
    last_active_day: str | None
    weekly_active_days: int
    weekly_minutes: int


def is_quiet(local_minute: int, preferences: NotificationPreferences) -> bool:
    start, end = preferences.quiet_start_minute, preferences.quiet_end_minute
    if start == end:
        return False
    if start < end:
        return start <= local_minute < end
    return local_minute >= start or local_minute < end


def next_allowed_time(candidate: datetime, preferences: NotificationPreferences) -> datetime:
    minute = candidate.hour * 60 + candidate.minute
    if not is_quiet(minute, preferences):
        return candidate
    end = preferences.quiet_end_minute
    day = candidate.date()
    # If quiet spans midnight and we are in its evening half, next allowed is tomorrow.
    if preferences.quiet_start_minute > preferences.quiet_end_minute and minute >= preferences.quiet_start_minute:
        day = day + timedelta(days=1)
    return datetime(day.year, day.month, day.day, end // 60, end % 60, tzinfo=candidate.tzinfo)


def next_allowed_utc(candidate: datetime, preferences: NotificationPreferences) -> datetime:
    if candidate.tzinfo is None:
        raise ValueError("candidate_must_be_timezone_aware")
    local_tz = timezone(timedelta(minutes=preferences.timezone_offset_minutes))
    local_candidate = candidate.astimezone(local_tz)
    adjusted_local = next_allowed_time(local_candidate, preferences)
    return adjusted_local.astimezone(UTC)

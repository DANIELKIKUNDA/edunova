from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .ports import EngagementRepository, PushRegistry, PushSender
from ..domain.model import (
    DeliveryChannel, EngagementCategory, EngagementDay, NotificationIntent,
    NotificationPreferences, StreakSummary, next_allowed_utc,
)


class EngagementService:
    def __init__(self, repository: EngagementRepository, push_registry: PushRegistry, now=lambda: datetime.now(UTC), push_sender: PushSender | None = None):
        self.repository = repository
        self.push_registry = push_registry
        self.now = now
        self.push_sender = push_sender

    def preferences(self, account_id: str) -> NotificationPreferences:
        return self.repository.get_preferences(account_id)

    def update_preferences(self, account_id: str, preferences: NotificationPreferences) -> NotificationPreferences:
        self.repository.save_preferences(account_id, preferences)
        return preferences

    def register_push(self, account_id: str, device_id: str, platform: str, token: str) -> None:
        if platform not in {"android", "ios", "web"}:
            raise ValueError("unsupported_push_platform")
        if len(token.strip()) < 16:
            raise ValueError("invalid_push_token")
        self.push_registry.register(account_id, device_id, platform, token.strip())

    def revoke_push(self, account_id: str, device_id: str) -> None:
        self.push_registry.revoke(account_id, device_id)

    def schedule(self, intent: NotificationIntent) -> bool:
        prefs = self.preferences(intent.account_id)
        if not prefs.category_enabled(intent.category):
            return False
        if intent.channel == DeliveryChannel.PUSH and not prefs.push_enabled:
            return False
        adjusted = NotificationIntent(
            id=intent.id, account_id=intent.account_id, dedupe_key=intent.dedupe_key,
            category=intent.category, channel=intent.channel, title=intent.title, body=intent.body,
            deep_link=intent.deep_link, fire_at=next_allowed_utc(intent.fire_at, prefs),
            expires_at=max(intent.expires_at, next_allowed_utc(intent.fire_at, prefs) + timedelta(hours=1)),
            priority=intent.priority, created_at=intent.created_at,
        )
        day_key = adjusted.fire_at.date().isoformat()
        existing = self.repository.list_scheduled_for_day(intent.account_id, day_key)
        if any(x.dedupe_key == adjusted.dedupe_key for x in existing):
            return False
        if prefs.max_daily_notifications == 0:
            return False
        if len(existing) >= prefs.max_daily_notifications:
            lowest = min(existing, key=lambda x: x.priority, default=None)
            if lowest is None or adjusted.priority <= lowest.priority:
                return False
            self.repository.cancel_intent(lowest.id)
        return self.repository.save_intent(adjusted)

    def assessment_reminders(self, *, account_id: str, event_id: str, course_title: str, starts_at: datetime, readiness: int) -> tuple[NotificationIntent, ...]:
        now = self.now()
        result = []
        for label, delta, priority in (("j3", timedelta(days=3), 72), ("j1", timedelta(days=1), 86), ("h3", timedelta(hours=3), 96)):
            fire_at = starts_at - delta
            if fire_at <= now or fire_at >= starts_at:
                continue
            if label == "j3" and readiness >= 85:
                continue
            body = f"Préparation actuelle : {readiness} %. Continue avec la prochaine action utile."
            result.append(NotificationIntent(
                id=str(uuid4()), account_id=account_id, dedupe_key=f"assessment:{event_id}:{label}",
                category=EngagementCategory.ASSESSMENT, channel=DeliveryChannel.LOCAL,
                title=f"{course_title} — évaluation bientôt", body=body,
                deep_link=f"/calendar?event={event_id}", fire_at=fire_at,
                expires_at=starts_at, priority=priority,
            ))
        return tuple(result)


    def dispatch_due_push(self, limit: int = 100) -> dict[str, int]:
        if self.push_sender is None:
            return {"sent": 0, "invalid_tokens": 0, "skipped": 0}
        sent = invalid_count = skipped = 0
        now = self.now()
        for intent in self.repository.list_due_push(now, limit):
            prefs = self.preferences(intent.account_id)
            if not prefs.push_enabled or not prefs.category_enabled(intent.category) or intent.expires_at <= now:
                skipped += 1
                self.repository.mark_delivered(intent.id, now)
                continue
            tokens = self.push_registry.active_tokens(intent.account_id)
            if not tokens:
                skipped += 1
                self.repository.mark_delivered(intent.id, now)
                continue
            invalid = self.push_sender.send(tokens=tokens, title=intent.title, body=intent.body, deep_link=intent.deep_link)
            for token in invalid:
                self.push_registry.revoke_token(token)
            invalid_count += len(invalid)
            sent += 1
            self.repository.mark_delivered(intent.id, now)
        return {"sent": sent, "invalid_tokens": invalid_count, "skipped": skipped}

    def record_activity(self, account_id: str, day: EngagementDay) -> StreakSummary:
        self.repository.upsert_day(account_id, day)
        return self.streak(account_id)

    def streak(self, account_id: str) -> StreakSummary:
        days = sorted(self.repository.recent_days(account_id, 120), key=lambda x: x.day_key)
        active = [d for d in days if d.active]
        if not active:
            return StreakSummary(0, 0, None, 0, 0)
        best = current_run = 1
        previous = datetime.fromisoformat(active[0].day_key).date()
        for d in active[1:]:
            current = datetime.fromisoformat(d.day_key).date()
            if current == previous + timedelta(days=1):
                current_run += 1
            elif current != previous:
                best = max(best, current_run)
                current_run = 1
            previous = current
        best = max(best, current_run)
        today = self.now().date()
        active_dates = {datetime.fromisoformat(d.day_key).date() for d in active}
        current = 0
        cursor = today if today in active_dates else today - timedelta(days=1)
        while cursor in active_dates:
            current += 1
            cursor -= timedelta(days=1)
        rolling_start = today - timedelta(days=6)
        weekly = [d for d in active if datetime.fromisoformat(d.day_key).date() >= rolling_start]
        return StreakSummary(current, best, active[-1].day_key, len(weekly), sum(d.active_minutes for d in weekly))

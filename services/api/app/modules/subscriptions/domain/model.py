from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class Subscription:
    premium_until: datetime | None
    ai_credits_remaining: int = 0

    def is_premium(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(UTC)
        return self.premium_until is not None and self.premium_until > now

    @classmethod
    def activate_30_days(cls, *, from_time: datetime | None = None, ai_credits: int = 25) -> "Subscription":
        start = from_time or datetime.now(UTC)
        return cls(premium_until=start + timedelta(days=30), ai_credits_remaining=ai_credits)

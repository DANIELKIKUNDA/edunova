import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.subscriptions.domain.model import Subscription


def test_subscription_is_active_for_30_days() -> None:
    start = datetime(2026, 9, 20, tzinfo=UTC)
    subscription = Subscription.activate_30_days(from_time=start, ai_credits=25)
    assert subscription.is_premium(start + timedelta(days=29))
    assert not subscription.is_premium(start + timedelta(days=31))
    assert subscription.ai_credits_remaining == 25

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.modules.subscriptions.domain.model import Subscription

router = APIRouter()


class SubscriptionStatusResponse(BaseModel):
    premium: bool
    premium_until: datetime | None
    ai_credits_remaining: int


@router.get("/status", response_model=SubscriptionStatusResponse)
def demo_status() -> SubscriptionStatusResponse:
    # Adapter de démonstration. Sera remplacé par repository + auth.
    subscription = Subscription.activate_30_days(from_time=datetime.now(UTC), ai_credits=25)
    return SubscriptionStatusResponse(
        premium=subscription.is_premium(),
        premium_until=subscription.premium_until,
        ai_credits_remaining=subscription.ai_credits_remaining,
    )

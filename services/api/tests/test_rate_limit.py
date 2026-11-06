from datetime import UTC, datetime

import pytest

from app.shared.security.rate_limit import InMemoryRateLimiter, RateLimitExceeded


def test_rate_limiter_blocks_after_limit_inside_window():
    r = InMemoryRateLimiter(); now = datetime(2026,9,20,tzinfo=UTC)
    r.check(key='k', limit=2, window_seconds=60, now=now)
    r.check(key='k', limit=2, window_seconds=60, now=now)
    with pytest.raises(RateLimitExceeded):
        r.check(key='k', limit=2, window_seconds=60, now=now)

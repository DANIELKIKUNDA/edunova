from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock


class RateLimitExceeded(Exception):
    pass


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._items: dict[str, list[datetime]] = {}
        self._lock = Lock()

    def check(self, *, key: str, limit: int, window_seconds: int, now: datetime | None = None) -> None:
        now = now or datetime.now(UTC)
        cutoff = now - timedelta(seconds=window_seconds)
        with self._lock:
            bucket = [x for x in self._items.get(key, []) if x > cutoff]
            if len(bucket) >= limit:
                raise RateLimitExceeded(key)
            bucket.append(now)
            self._items[key] = bucket


class RedisRateLimiter:
    def __init__(self, redis_client) -> None:
        self.redis = redis_client

    def check(self, *, key: str, limit: int, window_seconds: int, now: datetime | None = None) -> None:
        redis_key = f"edunova:ratelimit:{key}"
        pipe = self.redis.pipeline()
        pipe.incr(redis_key)
        pipe.ttl(redis_key)
        count, ttl = pipe.execute()
        if ttl == -1:
            self.redis.expire(redis_key, window_seconds)
        if int(count) > limit:
            raise RateLimitExceeded(key)

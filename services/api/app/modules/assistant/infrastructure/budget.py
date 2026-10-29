from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4


class InMemoryDailyAiBudgetGate:
    """Process-local budget gate for tests/development.

    Production uses the Redis implementation so the cap is shared by all workers.
    """

    def __init__(self, daily_limit_units: int = 1_000_000) -> None:
        self.daily_limit_units = daily_limit_units
        self._lock = Lock()
        self._used: dict[str, int] = {}
        self._reservations: dict[str, tuple[str, int, bool]] = {}

    def reserve(self, units: int) -> str:
        if units < 0:
            raise ValueError("invalid_ai_budget_units")
        day = datetime.now(UTC).date().isoformat()
        with self._lock:
            used = self._used.get(day, 0)
            if used + units > self.daily_limit_units:
                raise ValueError("ai_daily_budget_exhausted")
            self._used[day] = used + units
            rid = uuid4().hex
            self._reservations[rid] = (day, units, True)
            return rid

    def commit(self, reservation_id: str) -> None:
        with self._lock:
            item = self._reservations.get(reservation_id)
            if item is None:
                return
            day, units, active = item
            self._reservations[reservation_id] = (day, units, False)

    def release(self, reservation_id: str) -> None:
        with self._lock:
            item = self._reservations.get(reservation_id)
            if item is None:
                return
            day, units, active = item
            if active:
                self._used[day] = max(0, self._used.get(day, 0) - units)
            self._reservations[reservation_id] = (day, units, False)


class RedisDailyAiBudgetGate:
    """Atomic global daily spend guard shared across API workers."""

    def __init__(self, redis_client, *, daily_limit_units: int, prefix: str = "edunova:ai:budget") -> None:
        self.redis = redis_client
        self.daily_limit_units = daily_limit_units
        self.prefix = prefix

    def _day_key(self) -> str:
        return f"{self.prefix}:{datetime.now(UTC).date().isoformat()}"

    def reserve(self, units: int) -> str:
        if units < 0:
            raise ValueError("invalid_ai_budget_units")
        key = self._day_key()
        # One script makes increment + limit decision atomic across workers.
        script = """
        local value = redis.call('INCRBY', KEYS[1], ARGV[1])
        if value == tonumber(ARGV[1]) then redis.call('EXPIRE', KEYS[1], 172800) end
        if value > tonumber(ARGV[2]) then
          redis.call('DECRBY', KEYS[1], ARGV[1])
          return -1
        end
        return value
        """
        result = int(self.redis.eval(script, 1, key, units, self.daily_limit_units))
        if result < 0:
            raise ValueError("ai_daily_budget_exhausted")
        rid = uuid4().hex
        reservation_key = f"{self.prefix}:reservation:{rid}"
        self.redis.hset(reservation_key, mapping={"day_key": key, "units": units, "active": 1})
        self.redis.expire(reservation_key, 172800)
        return rid

    def commit(self, reservation_id: str) -> None:
        key = f"{self.prefix}:reservation:{reservation_id}"
        self.redis.hset(key, "active", 0)

    def release(self, reservation_id: str) -> None:
        key = f"{self.prefix}:reservation:{reservation_id}"
        script = """
        if redis.call('EXISTS', KEYS[1]) == 0 then return 0 end
        local active = redis.call('HGET', KEYS[1], 'active')
        if active ~= '1' then return 0 end
        local day_key = redis.call('HGET', KEYS[1], 'day_key')
        local units = tonumber(redis.call('HGET', KEYS[1], 'units') or '0')
        if day_key and units > 0 then redis.call('DECRBY', day_key, units) end
        redis.call('HSET', KEYS[1], 'active', 0)
        return units
        """
        self.redis.eval(script, 1, key)

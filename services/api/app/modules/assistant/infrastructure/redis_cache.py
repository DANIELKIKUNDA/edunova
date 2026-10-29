from __future__ import annotations

import json
from dataclasses import asdict

from app.modules.assistant.domain.model import AssistantAnswer, Citation


class RedisAssistantCache:
    def __init__(self, redis_client, prefix: str = "edunova:assistant:cache:") -> None:
        self.redis = redis_client; self.prefix = prefix
    def get(self, key: str):
        raw=self.redis.get(self.prefix+key)
        if not raw: return None
        d=json.loads(raw)
        return AssistantAnswer(
            text=d["text"],citations=tuple(Citation(**c) for c in d["citations"]),grounded=d["grounded"],confidence=d["confidence"],abstained=d["abstained"],
            provider=d.get("provider"),model=d.get("model"),credits_charged=d.get("credits_charged",0),cache_hit=d.get("cache_hit",False),safety_flags=tuple(d.get("safety_flags",[])),usage=d.get("usage",{}),route_reason=d.get("route_reason"),
        )
    def set(self, key: str, answer: AssistantAnswer, ttl_seconds: int) -> None:
        self.redis.setex(self.prefix+key, ttl_seconds, json.dumps(asdict(answer), ensure_ascii=False))

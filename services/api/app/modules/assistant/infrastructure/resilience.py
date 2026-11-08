from __future__ import annotations

from threading import Lock
from time import monotonic

from app.modules.assistant.domain.model import ProviderResult


class ProviderCircuitOpen(RuntimeError):
    pass


class CircuitBreakerProvider:
    """Small process-local circuit breaker around an LLM adapter.

    It does not retry the same request: fallback is handled by AssistantService.
    This avoids duplicate paid calls and keeps provider concerns isolated.
    """

    def __init__(self, inner, *, failure_threshold: int = 3, cooldown_seconds: float = 60.0) -> None:
        self.inner = inner
        self.name = inner.name
        self.model = inner.model
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = max(1.0, cooldown_seconds)
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = Lock()

    def generate(self, *, system_prompt: str, user_prompt: str, max_output_tokens: int) -> ProviderResult:
        with self._lock:
            if self._opened_at is not None:
                if monotonic() - self._opened_at < self.cooldown_seconds:
                    raise ProviderCircuitOpen(f"provider_circuit_open:{self.name}:{self.model}")
                self._opened_at = None
                self._failures = 0
        try:
            result = self.inner.generate(system_prompt=system_prompt, user_prompt=user_prompt, max_output_tokens=max_output_tokens)
        except Exception:
            with self._lock:
                self._failures += 1
                if self._failures >= self.failure_threshold:
                    self._opened_at = monotonic()
            raise
        with self._lock:
            self._failures = 0
            self._opened_at = None
        return result

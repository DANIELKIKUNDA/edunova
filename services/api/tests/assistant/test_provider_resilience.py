import json

import pytest

from app.modules.assistant.domain.model import ProviderResult
from app.modules.assistant.infrastructure.provider_config import load_external_ai_providers
from app.modules.assistant.infrastructure.resilience import CircuitBreakerProvider, ProviderCircuitOpen


class StubProvider:
    def __init__(self, *, fail=False):
        self.name = "stub"
        self.model = "m1"
        self.fail = fail
        self.calls = 0

    def generate(self, *, system_prompt: str, user_prompt: str, max_output_tokens: int) -> ProviderResult:
        self.calls += 1
        if self.fail:
            raise RuntimeError("boom")
        return ProviderResult(text="ok", input_tokens=2, output_tokens=1)


def test_multi_provider_config_loads_profiles_without_embedding_secrets():
    spec = [
        {
            "name": "provider-a",
            "base_url": "https://a.example/v1",
            "api_key_env": "A_KEY",
            "models": [
                {"model": "flash", "quality_tier": 1, "cost_units": 1, "max_context_tokens": 8000, "capabilities": ["chat"]},
            ],
        },
        {
            "name": "provider-b",
            "base_url": "https://b.example/v1",
            "api_key_env": "B_KEY",
            "models": [
                {"model": "reason", "quality_tier": 2, "cost_units": 2, "max_context_tokens": 16000, "capabilities": ["chat", "reasoning", "high_reliability"]},
            ],
        },
    ]
    env = {"AI_PROVIDERS_JSON": json.dumps(spec), "A_KEY": "secret-a", "B_KEY": "secret-b"}
    providers, profiles = load_external_ai_providers(env)
    assert set(providers) == {("provider-a", "flash"), ("provider-b", "reason")}
    assert {p.model for p in profiles} == {"flash", "reason"}
    assert "secret-a" not in env["AI_PROVIDERS_JSON"]
    assert "secret-b" not in env["AI_PROVIDERS_JSON"]


def test_provider_config_rejects_duplicate_provider_model():
    spec = [{
        "name": "provider-a",
        "base_url": "https://a.example/v1",
        "api_key_env": "A_KEY",
        "models": [
            {"model": "flash", "quality_tier": 1, "cost_units": 1, "max_context_tokens": 8000},
            {"model": "flash", "quality_tier": 1, "cost_units": 1, "max_context_tokens": 8000},
        ],
    }]
    with pytest.raises(RuntimeError, match="duplicate_ai_provider_model"):
        load_external_ai_providers({"AI_PROVIDERS_JSON": json.dumps(spec), "A_KEY": "secret"})


def test_circuit_breaker_opens_after_threshold_and_stops_paid_calls():
    inner = StubProvider(fail=True)
    wrapped = CircuitBreakerProvider(inner, failure_threshold=2, cooldown_seconds=60)
    for _ in range(2):
        with pytest.raises(RuntimeError, match="boom"):
            wrapped.generate(system_prompt="s", user_prompt="u", max_output_tokens=20)
    assert inner.calls == 2
    with pytest.raises(ProviderCircuitOpen):
        wrapped.generate(system_prompt="s", user_prompt="u", max_output_tokens=20)
    assert inner.calls == 2


def test_successful_provider_call_resets_failure_counter():
    inner = StubProvider(fail=True)
    wrapped = CircuitBreakerProvider(inner, failure_threshold=2, cooldown_seconds=60)
    with pytest.raises(RuntimeError):
        wrapped.generate(system_prompt="s", user_prompt="u", max_output_tokens=20)
    inner.fail = False
    assert wrapped.generate(system_prompt="s", user_prompt="u", max_output_tokens=20).text == "ok"
    inner.fail = True
    with pytest.raises(RuntimeError):
        wrapped.generate(system_prompt="s", user_prompt="u", max_output_tokens=20)
    # Only one failure after a successful reset: circuit is not open yet.
    inner.fail = False
    assert wrapped.generate(system_prompt="s", user_prompt="u", max_output_tokens=20).text == "ok"

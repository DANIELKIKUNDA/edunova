from __future__ import annotations

import json
import os
from collections.abc import Mapping

from app.modules.assistant.domain.model import ModelProfile
from app.modules.assistant.infrastructure.http_provider import OpenAICompatibleProvider
from app.modules.assistant.infrastructure.resilience import CircuitBreakerProvider


def load_external_ai_providers(env: Mapping[str, str] | None = None):
    """Build provider adapters and model profiles without embedding secrets in config JSON.

    AI_PROVIDERS_JSON example:
    [
      {
        "name":"provider-a",
        "base_url":"https://api.example/v1",
        "api_key_env":"PROVIDER_A_KEY",
        "models":[
          {"model":"flash","quality_tier":1,"cost_units":1,"max_context_tokens":8000,"capabilities":["chat"]},
          {"model":"reason","quality_tier":2,"cost_units":2,"max_context_tokens":16000,"capabilities":["chat","reasoning","high_reliability"]}
        ]
      }
    ]
    """
    source = os.environ if env is None else env
    raw = str(source.get("AI_PROVIDERS_JSON", "")).strip()
    providers = {}
    profiles: list[ModelProfile] = []
    if raw:
        try:
            specs = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("invalid_AI_PROVIDERS_JSON") from exc
        if not isinstance(specs, list):
            raise RuntimeError("AI_PROVIDERS_JSON_must_be_list")
        for provider_spec in specs:
            if not isinstance(provider_spec, dict):
                raise RuntimeError("invalid_ai_provider_spec")
            name = str(provider_spec.get("name", "")).strip()
            base_url = str(provider_spec.get("base_url", "")).strip()
            api_key_env = str(provider_spec.get("api_key_env", "")).strip()
            api_key = str(source.get(api_key_env, "")).strip() if api_key_env else ""
            if not (name and base_url and api_key_env and api_key):
                continue
            timeout = float(provider_spec.get("timeout_seconds", 45.0))
            failure_threshold = int(provider_spec.get("failure_threshold", 3))
            cooldown = float(provider_spec.get("cooldown_seconds", 60.0))
            models = provider_spec.get("models") or []
            if not isinstance(models, list):
                raise RuntimeError("invalid_ai_models_spec")
            for model_spec in models:
                model = str(model_spec.get("model", "")).strip()
                if not model:
                    continue
                quality = int(model_spec.get("quality_tier", 1))
                cost = int(model_spec.get("cost_units", 1))
                context = int(model_spec.get("max_context_tokens", 8000))
                capabilities = frozenset(str(x) for x in (model_spec.get("capabilities") or ["chat"]))
                if quality < 1 or cost < 1 or context < 2000:
                    raise RuntimeError("invalid_ai_model_limits")
                key = (name, model)
                if key in providers:
                    raise RuntimeError("duplicate_ai_provider_model")
                inner = OpenAICompatibleProvider(name=name, model=model, base_url=base_url, api_key=api_key, timeout_seconds=timeout)
                wrapped = CircuitBreakerProvider(inner, failure_threshold=failure_threshold, cooldown_seconds=cooldown)
                providers[key] = wrapped
                profiles.append(ModelProfile(provider=name, model=model, quality_tier=quality, cost_units=cost, max_context_tokens=context, capabilities=capabilities))
        return providers, tuple(profiles)

    # Backward-compatible single-provider configuration.
    base_url = str(source.get("AI_PROVIDER_BASE_URL", "")).strip()
    api_key = str(source.get("AI_PROVIDER_API_KEY", "")).strip()
    provider_name = str(source.get("AI_PROVIDER_NAME", "external")).strip() or "external"
    flash_model = str(source.get("AI_FLASH_MODEL", "")).strip()
    reasoning_model = str(source.get("AI_REASONING_MODEL", "")).strip()
    if base_url and api_key and flash_model:
        inner = OpenAICompatibleProvider(name=provider_name, model=flash_model, base_url=base_url, api_key=api_key)
        providers[(provider_name, flash_model)] = CircuitBreakerProvider(inner)
        profiles.append(ModelProfile(provider=provider_name, model=flash_model, quality_tier=1, cost_units=int(source.get("AI_FLASH_CREDITS", "1")), max_context_tokens=int(source.get("AI_FLASH_CONTEXT", "8000")), capabilities=frozenset({"chat"})))
    if base_url and api_key and reasoning_model:
        inner = OpenAICompatibleProvider(name=provider_name, model=reasoning_model, base_url=base_url, api_key=api_key)
        providers[(provider_name, reasoning_model)] = CircuitBreakerProvider(inner)
        profiles.append(ModelProfile(provider=provider_name, model=reasoning_model, quality_tier=2, cost_units=int(source.get("AI_REASONING_CREDITS", "2")), max_context_tokens=int(source.get("AI_REASONING_CONTEXT", "16000")), capabilities=frozenset({"chat", "reasoning", "high_reliability"})))
    return providers, tuple(profiles)

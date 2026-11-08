from __future__ import annotations


PRODUCTION_LIKE_ENVS = frozenset({"production", "staging", "preproduction"})
PILOT_ENVS = frozenset({"staging", "preproduction"})


def normalize_environment(value: str) -> str:
    return value.strip().lower()


def is_production_like_env(value: str) -> bool:
    return normalize_environment(value) in PRODUCTION_LIKE_ENVS


def sandbox_payments_enabled(environment: str, provider: str) -> bool:
    env = normalize_environment(environment)
    mode = provider.strip().lower()
    if env in {"development", "test"}:
        return True
    return env in PILOT_ENVS and mode == "sandbox"

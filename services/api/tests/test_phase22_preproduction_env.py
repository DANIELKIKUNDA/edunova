from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[3] / "scripts" / "validate_preproduction_env.py"
API_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(API_ROOT))
SPEC = importlib.util.spec_from_file_location("validate_preproduction_env", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


VALID = {
    "EDUNOVA_ENV": "preproduction",
    "DATABASE_URL": "postgresql+psycopg://pilot:strong-db-pass@postgres:5432/edunova",
    "REDIS_URL": "redis://redis:6379/0",
    "JWT_SECRET": "j" * 64,
    "RESOURCE_DELIVERY_SECRET": "r" * 64,
    "MFA_ENCRYPTION_KEY": "m" * 32,
    "ATTENDANCE_QR_SECRET": "q" * 32,
    "ATTENDANCE_PROXIMITY_SECRET": "p" * 32,
    "CORS_ORIGINS": "https://pilot.edunova.example",
    "CONTENT_STORAGE_BACKEND": "s3",
    "CONTENT_STORAGE_BUCKET": "edunova-pilot-private",
    "PAYMENT_PROVIDER": "sandbox",
    "AI_ALLOW_PERSONAL_DOCUMENTS": "false",
    "AI_DAILY_CREDIT_BUDGET": "0",
}


def _configure(monkeypatch, **changes):
    for key in set(VALID) | set(changes):
        monkeypatch.delenv(key, raising=False)
    values = VALID | changes
    for key, value in values.items():
        os.environ[key] = value


def test_valid_preproduction_environment_passes(monkeypatch):
    _configure(monkeypatch)
    assert MODULE.validate() == []


def test_placeholder_secrets_and_local_cors_fail_closed(monkeypatch):
    _configure(
        monkeypatch,
        JWT_SECRET="replace-with-a-random-secret-of-at-least-64-characters-before-production",
        CORS_ORIGINS="http://localhost:8080",
    )
    errors = MODULE.validate()
    assert any("JWT_SECRET contains a placeholder" in item for item in errors)
    assert any("CORS origin" in item for item in errors)


def test_real_payments_and_personal_ai_are_blocked_during_pilot(monkeypatch):
    _configure(monkeypatch, PAYMENT_PROVIDER="production", AI_ALLOW_PERSONAL_DOCUMENTS="true")
    errors = MODULE.validate()
    assert any("PAYMENT_PROVIDER" in item for item in errors)
    assert any("AI_ALLOW_PERSONAL_DOCUMENTS" in item for item in errors)


def test_staging_and_preproduction_are_production_like():
    from app.shared.config.environment import is_production_like_env

    assert is_production_like_env("production")
    assert is_production_like_env("staging")
    assert is_production_like_env("preproduction")
    assert not is_production_like_env("test")


def test_sandbox_payments_are_limited_to_non_production_pilot_environments():
    from app.shared.config.environment import sandbox_payments_enabled

    assert sandbox_payments_enabled("preproduction", "sandbox")
    assert sandbox_payments_enabled("staging", "sandbox")
    assert not sandbox_payments_enabled("production", "sandbox")
    assert not sandbox_payments_enabled("preproduction", "production")

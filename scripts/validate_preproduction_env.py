#!/usr/bin/env python3
"""Fail-closed validation for EduNova pilot/preproduction configuration."""
from __future__ import annotations

import os
import re
import sys
from urllib.parse import urlparse


PLACEHOLDERS = {
    "edunova",
    "password",
    "changeme",
    "change-me",
    "replace-me",
    "replace-with-a-random-secret-of-at-least-64-characters-before-production",
}
REQUIRED_SECRETS = {
    "JWT_SECRET": 64,
    "RESOURCE_DELIVERY_SECRET": 64,
    "MFA_ENCRYPTION_KEY": 32,
    "ATTENDANCE_QR_SECRET": 32,
    "ATTENDANCE_PROXIMITY_SECRET": 32,
}


def _value(name: str) -> str:
    return os.getenv(name, "").strip()


def validate() -> list[str]:
    errors: list[str] = []
    environment = _value("EDUNOVA_ENV")
    if environment not in {"staging", "preproduction"}:
        errors.append("EDUNOVA_ENV must be staging or preproduction")

    database_url = _value("DATABASE_URL")
    parsed_database = urlparse(database_url.replace("postgresql+psycopg://", "postgresql://", 1))
    if parsed_database.scheme not in {"postgres", "postgresql"} or not parsed_database.hostname:
        errors.append("DATABASE_URL must be a PostgreSQL URL")
    if parsed_database.password and parsed_database.password.lower() in PLACEHOLDERS:
        errors.append("DATABASE_URL contains a placeholder password")

    redis_url = _value("REDIS_URL")
    if urlparse(redis_url).scheme not in {"redis", "rediss"}:
        errors.append("REDIS_URL must be a Redis URL")

    for name, minimum in REQUIRED_SECRETS.items():
        value = _value(name)
        if len(value) < minimum:
            errors.append(f"{name} must contain at least {minimum} characters")
        elif value.lower() in PLACEHOLDERS or re.search(r"(?i)(replace|change.?me|example|password)", value):
            errors.append(f"{name} contains a placeholder value")

    origins = [item.strip() for item in _value("CORS_ORIGINS").split(",") if item.strip()]
    if not origins:
        errors.append("CORS_ORIGINS must contain at least one explicit origin")
    for origin in origins:
        parsed = urlparse(origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
            errors.append(f"CORS origin must be an HTTPS origin without a path: {origin}")
        if "localhost" in origin or "127.0.0.1" in origin or "*" in origin:
            errors.append(f"CORS origin is not suitable for preproduction: {origin}")

    storage_backend = _value("CONTENT_STORAGE_BACKEND")
    if storage_backend != "s3":
        errors.append("CONTENT_STORAGE_BACKEND must be s3")
    if not _value("CONTENT_STORAGE_BUCKET"):
        errors.append("CONTENT_STORAGE_BUCKET is required")

    payment_provider = _value("PAYMENT_PROVIDER")
    if payment_provider not in {"disabled", "sandbox"}:
        errors.append("PAYMENT_PROVIDER must remain disabled or sandbox during the controlled pilot")

    if _value("AI_ALLOW_PERSONAL_DOCUMENTS").lower() == "true":
        errors.append("AI_ALLOW_PERSONAL_DOCUMENTS must remain false until a privacy contract is approved")
    budget = _value("AI_DAILY_CREDIT_BUDGET")
    try:
        if int(budget or "0") < 0:
            errors.append("AI_DAILY_CREDIT_BUDGET cannot be negative")
    except ValueError:
        errors.append("AI_DAILY_CREDIT_BUDGET must be an integer")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("EduNova preproduction environment: VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

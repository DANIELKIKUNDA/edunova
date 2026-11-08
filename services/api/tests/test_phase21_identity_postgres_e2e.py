"""Phase 21.B identity journey using the real API and PostgreSQL runtime."""
from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.runtime import runtime


pytestmark = pytest.mark.skipif(
    "PHASE21_POSTGRES_URL" not in os.environ,
    reason="requires the dedicated Phase 21 PostgreSQL service",
)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_identity_session_revocation_is_persisted_in_postgresql() -> None:
    assert runtime.engine.dialect.name == "postgresql"
    email = f"phase21-{uuid4().hex}@example.test"
    password = "Phase21-Strong-Password!"

    with TestClient(app) as client:
        anonymous = client.get("/v1/identity/me")
        assert anonymous.status_code == 401
        assert anonymous.json()["detail"] == "missing_bearer_token"

        registered = client.post(
            "/v1/identity/register",
            json={
                "display_name": "Phase 21 Student",
                "email": email,
                "password": password,
                "device_name": "phase21-android",
            },
        )
        assert registered.status_code == 201, registered.text
        first = registered.json()
        account_id = first["account_id"]

        profile = client.get("/v1/identity/me", headers=_bearer(first["access_token"]))
        assert profile.status_code == 200
        assert profile.json() == {
            "id": account_id,
            "display_name": "Phase 21 Student",
            "email": email,
            "phone_number": None,
            "state": "active",
        }

        logged_in = client.post(
            "/v1/identity/login",
            json={
                "login": email,
                "password": password,
                "device_name": "phase21-web",
            },
        )
        assert logged_in.status_code == 200, logged_in.text
        second = logged_in.json()

        sessions = client.get(
            "/v1/identity/sessions", headers=_bearer(second["access_token"])
        )
        assert sessions.status_code == 200
        active_devices = {item["device_name"] for item in sessions.json() if item["active"]}
        assert active_devices == {"phase21-android", "phase21-web"}

        logged_out = client.post(
            "/v1/identity/logout-all", headers=_bearer(second["access_token"])
        )
        assert logged_out.status_code == 200
        assert logged_out.json()["sessions_revoked"] == 2

        rejected = client.get("/v1/identity/me", headers=_bearer(second["access_token"]))
        assert rejected.status_code == 401
        assert rejected.json()["detail"] == "invalid_or_expired_token"

        replay = client.post(
            "/v1/identity/refresh",
            json={"refresh_token": second["refresh_token"], "device_name": "replay"},
        )
        assert replay.status_code == 401
        assert replay.json()["detail"] == "invalid_refresh_token"

    with runtime.engine.connect() as connection:
        account = connection.execute(
            text("SELECT email, token_version FROM accounts WHERE id = :account_id"),
            {"account_id": account_id},
        ).one()
        session_rows = connection.execute(
            text(
                "SELECT device_name, revoked_at IS NOT NULL AS revoked "
                "FROM refresh_sessions WHERE account_id = :account_id ORDER BY device_name"
            ),
            {"account_id": account_id},
        ).all()

    assert account.email == email
    assert account.token_version == 2
    assert session_rows == [
        ("phase21-android", True),
        ("phase21-web", True),
    ]

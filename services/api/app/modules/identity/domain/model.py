from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AccountState(StrEnum):
    ACTIVE = "active"
    LOCKED = "locked"
    DISABLED = "disabled"


@dataclass
class Account:
    id: str
    display_name: str
    password_hash: str
    created_at: datetime
    email: str | None = None
    phone_number: str | None = None
    state: AccountState = AccountState.ACTIVE
    token_version: int = 1

    def __post_init__(self) -> None:
        if not self.email and not self.phone_number:
            raise ValueError("email_or_phone_required")
        if self.email:
            self.email = self.email.strip().lower()
        if self.phone_number:
            self.phone_number = self.phone_number.strip()


@dataclass
class RefreshSession:
    id: str
    account_id: str
    token_hash: str
    created_at: datetime
    expires_at: datetime | None
    device_name: str | None = None
    revoked_at: datetime | None = None
    replaced_by: str | None = None

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and (self.expires_at is None or now < self.expires_at)


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in_seconds: int


@dataclass(frozen=True)
class SessionView:
    id: str
    device_name: str | None
    created_at: datetime
    expires_at: datetime | None
    active: bool


@dataclass(frozen=True)
class PasswordChangeResult:
    revoked_sessions: int


@dataclass
class RecoveryChallenge:
    id: str
    account_id: str
    destination: str
    channel: str
    code_hash: str
    created_at: datetime
    expires_at: datetime
    attempts_left: int = 5
    consumed_at: datetime | None = None

    def is_active(self, now: datetime) -> bool:
        return self.consumed_at is None and self.attempts_left > 0 and now < self.expires_at

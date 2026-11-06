from __future__ import annotations

from app.modules.identity.domain.model import Account, RefreshSession


class InMemoryAccountRepository:
    def __init__(self) -> None:
        self.items: dict[str, Account] = {}

    def get(self, account_id: str) -> Account | None:
        return self.items.get(account_id)

    def find_by_login(self, login: str) -> Account | None:
        key = login.strip().lower()
        return next(
            (
                a for a in self.items.values()
                if (a.email and a.email.lower() == key) or (a.phone_number and a.phone_number == login.strip())
            ),
            None,
        )

    def save(self, account: Account) -> None:
        self.items[account.id] = account


class InMemorySessionRepository:
    def __init__(self) -> None:
        self.items: dict[str, RefreshSession] = {}

    def get_by_hash(self, token_hash: str) -> RefreshSession | None:
        return next((s for s in self.items.values() if s.token_hash == token_hash), None)

    def get(self, session_id: str) -> RefreshSession | None:
        return self.items.get(session_id)

    def list_for_account(self, account_id: str) -> list[RefreshSession]:
        return sorted([s for s in self.items.values() if s.account_id == account_id], key=lambda s: s.created_at, reverse=True)

    def save(self, session: RefreshSession) -> None:
        self.items[session.id] = session

    def revoke(self, account_id: str, session_id: str, now) -> bool:
        item = self.items.get(session_id)
        if not item or item.account_id != account_id or item.revoked_at is not None:
            return False
        item.revoked_at = now
        return True

    def revoke_all(self, account_id: str, now=None) -> int:
        from datetime import UTC, datetime
        now = now or datetime.now(UTC)
        count = 0
        for item in self.items.values():
            if item.account_id == account_id and item.revoked_at is None:
                item.revoked_at = now
                count += 1
        return count


class InMemoryRecoveryChallengeRepository:
    def __init__(self) -> None:
        self.items = {}
    def get(self, challenge_id: str):
        return self.items.get(challenge_id)
    def save(self, challenge) -> None:
        self.items[challenge.id] = challenge


class InMemoryVerificationSender:
    enabled = True
    def __init__(self) -> None:
        self.sent: list[dict] = []
    def send(self, *, destination: str, channel: str, code: str) -> None:
        self.sent.append({"destination": destination, "channel": channel, "code": code})


class DisabledVerificationSender:
    enabled = False
    def send(self, *, destination: str, channel: str, code: str) -> None:
        raise RuntimeError("verification_sender_not_configured")

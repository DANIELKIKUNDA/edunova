from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4
import hashlib
import secrets
import hmac

from app.modules.identity.application.ports import AccountRepository, PasswordHasher, SessionRepository, TokenIssuer, RecoveryChallengeRepository, VerificationSender
from app.modules.identity.domain.model import Account, AccountState, AuthTokens, RefreshSession, SessionView, RecoveryChallenge


@dataclass(frozen=True)
class RegisterInput:
    display_name: str
    password: str
    email: str | None = None
    phone_number: str | None = None
    device_name: str | None = None


class IdentityService:
    def __init__(self, *, accounts: AccountRepository, sessions: SessionRepository, hasher: PasswordHasher, tokens: TokenIssuer, now: callable, recovery=None, verification_sender=None) -> None:
        self.accounts = accounts
        self.sessions = sessions
        self.hasher = hasher
        self.tokens = tokens
        self.now = now
        self.recovery = recovery
        self.verification_sender = verification_sender

    def register(self, data: RegisterInput) -> tuple[Account, AuthTokens]:
        if len(data.display_name.strip()) < 1:
            raise ValueError("display_name_too_short")
        if len(data.password) < 8:
            raise ValueError("password_too_short")
        if data.email and self.accounts.find_by_login(data.email):
            raise ValueError("login_already_exists")
        if data.phone_number and self.accounts.find_by_login(data.phone_number):
            raise ValueError("login_already_exists")
        now = self.now()
        account = Account(
            id=str(uuid4()),
            display_name=data.display_name.strip(),
            email=data.email,
            phone_number=data.phone_number,
            password_hash=self.hasher.hash(data.password),
            created_at=now,
        )
        self.accounts.save(account)
        return account, self._create_session(account, data.device_name)

    def login(self, *, login: str, password: str, device_name: str | None = None) -> tuple[Account, AuthTokens]:
        account = self.accounts.find_by_login(login)
        if not account or not self.hasher.verify(account.password_hash, password):
            raise ValueError("invalid_credentials")
        if account.state != AccountState.ACTIVE:
            raise ValueError("account_not_active")
        return account, self._create_session(account, device_name)

    def refresh(self, refresh_token: str, device_name: str | None = None) -> AuthTokens:
        token_hash = self.tokens.hash_refresh(refresh_token)
        old = self.sessions.get_by_hash(token_hash)
        now = self.now()
        if old and old.revoked_at is not None and old.replaced_by:
            # Reuse of a rotated token is treated as credential theft: revoke every session
            # and invalidate access tokens by bumping token_version.
            account = self.accounts.get(old.account_id)
            if account:
                self.sessions.revoke_all(account.id, now)
                account.token_version += 1
                self.accounts.save(account)
            raise ValueError("invalid_refresh_token")
        if not old or not old.is_active(now):
            raise ValueError("invalid_refresh_token")
        account = self.accounts.get(old.account_id)
        if not account or account.state != AccountState.ACTIVE:
            raise ValueError("account_not_active")
        old.revoked_at = now
        tokens = self._create_session(account, device_name or old.device_name)
        new_hash = self.tokens.hash_refresh(tokens.refresh_token)
        replacement = self.sessions.get_by_hash(new_hash)
        old.replaced_by = replacement.id if replacement else None
        self.sessions.save(old)
        return tokens

    def logout(self, refresh_token: str) -> None:
        token_hash = self.tokens.hash_refresh(refresh_token)
        session = self.sessions.get_by_hash(token_hash)
        if session and session.revoked_at is None:
            session.revoked_at = self.now()
            self.sessions.save(session)

    def list_sessions(self, account_id: str) -> list[SessionView]:
        now = self.now()
        return [
            SessionView(id=s.id, device_name=s.device_name, created_at=s.created_at, expires_at=s.expires_at, active=s.is_active(now))
            for s in self.sessions.list_for_account(account_id)
        ]

    def revoke_session(self, *, account_id: str, session_id: str) -> bool:
        return self.sessions.revoke(account_id, session_id, self.now())

    def logout_all(self, account_id: str) -> int:
        now = self.now()
        count = self.sessions.revoke_all(account_id, now)
        account = self.accounts.get(account_id)
        if account:
            account.token_version += 1
            self.accounts.save(account)
        return count

    def change_password(self, *, account_id: str, current_password: str, new_password: str) -> None:
        account = self.accounts.get(account_id)
        if not account or account.state != AccountState.ACTIVE:
            raise ValueError("account_not_active")
        if not self.hasher.verify(account.password_hash, current_password):
            raise ValueError("invalid_current_password")
        if len(new_password) < 8:
            raise ValueError("password_too_short")
        if self.hasher.verify(account.password_hash, new_password):
            raise ValueError("new_password_must_differ")
        account.password_hash = self.hasher.hash(new_password)
        account.token_version += 1
        self.accounts.save(account)
        self.sessions.revoke_all(account_id, self.now())

    def request_password_recovery(self, login: str) -> str:
        if self.recovery is None or self.verification_sender is None or not getattr(self.verification_sender, "enabled", False):
            raise ValueError("recovery_not_configured")
        account = self.accounts.find_by_login(login)
        # Never disclose whether the account exists. Unknown logins get an opaque fake id.
        if not account:
            return str(uuid4())
        destination = account.phone_number or account.email or ""
        channel = "sms" if account.phone_number else "email"
        now = self.now()
        code = f"{secrets.randbelow(1_000_000):06d}"
        challenge_id = str(uuid4())
        code_hash = hashlib.sha256(f"{challenge_id}:{code}".encode()).hexdigest()
        challenge = RecoveryChallenge(
            id=challenge_id, account_id=account.id, destination=destination, channel=channel,
            code_hash=code_hash, created_at=now, expires_at=now + timedelta(minutes=10), attempts_left=5,
        )
        self.recovery.save(challenge)
        self.verification_sender.send(destination=destination, channel=channel, code=code)
        return challenge_id

    def confirm_password_recovery(self, *, challenge_id: str, code: str, new_password: str) -> None:
        if self.recovery is None:
            raise ValueError("recovery_not_configured")
        challenge = self.recovery.get(challenge_id)
        now = self.now()
        if not challenge or not challenge.is_active(now):
            raise ValueError("invalid_or_expired_recovery_challenge")
        supplied_hash = hashlib.sha256(f"{challenge_id}:{code.strip()}".encode()).hexdigest()
        if not hmac.compare_digest(challenge.code_hash, supplied_hash):
            challenge.attempts_left -= 1
            self.recovery.save(challenge)
            raise ValueError("invalid_recovery_code")
        if len(new_password) < 8:
            raise ValueError("password_too_short")
        account = self.accounts.get(challenge.account_id)
        if not account or account.state != AccountState.ACTIVE:
            raise ValueError("account_not_active")
        account.password_hash = self.hasher.hash(new_password)
        account.token_version += 1
        self.accounts.save(account)
        self.sessions.revoke_all(account.id, now)
        challenge.consumed_at = now
        self.recovery.save(challenge)

    def _create_session(self, account: Account, device_name: str | None) -> AuthTokens:
        now = self.now()
        access_token, expires_in = self.tokens.issue_access(account, now)
        refresh_token, token_hash = self.tokens.new_refresh_token()
        self.sessions.save(
            RefreshSession(
                id=str(uuid4()),
                account_id=account.id,
                token_hash=token_hash,
                created_at=now,
                # Trusted-device sessions are persistent by product contract.
                # They end only by explicit revocation/logout or a critical security event.
                expires_at=None,
                device_name=device_name,
            )
        )
        return AuthTokens(access_token=access_token, refresh_token=refresh_token, expires_in_seconds=expires_in)

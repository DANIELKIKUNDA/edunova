from datetime import UTC, datetime, timedelta

import pytest

from app.modules.identity.application.auth_context import Authenticator
from app.modules.identity.application.service import IdentityService, RegisterInput
from app.modules.identity.infrastructure.memory import InMemoryAccountRepository, InMemorySessionRepository
from app.modules.identity.infrastructure.security import Argon2PasswordHasher, JwtTokenIssuer


class Clock:
    def __init__(self): self.value = datetime.now(UTC)
    def __call__(self): return self.value


def make_identity():
    accounts = InMemoryAccountRepository(); sessions = InMemorySessionRepository(); clock = Clock()
    hasher = Argon2PasswordHasher(); issuer = JwtTokenIssuer(secret="x" * 64)
    service = IdentityService(accounts=accounts, sessions=sessions, hasher=hasher, tokens=issuer, now=clock)
    return service, accounts, sessions, issuer, clock


def test_registration_hashes_password_and_access_token_authenticates():
    service, accounts, _, issuer, _ = make_identity()
    account, tokens = service.register(RegisterInput(display_name="Daniel", password="StrongPass123", email="daniel@example.com"))
    stored = accounts.get(account.id)
    assert stored is not None and stored.password_hash != "StrongPass123"
    assert Authenticator(accounts=accounts, tokens=issuer).authenticate(tokens.access_token).account_id == account.id


def test_duplicate_login_is_rejected():
    service, *_ = make_identity()
    service.register(RegisterInput(display_name="A", password="StrongPass123", email="a@example.com"))
    with pytest.raises(ValueError, match="login_already_exists"):
        service.register(RegisterInput(display_name="B", password="StrongPass123", email="A@example.com"))


def test_refresh_token_rotation_blocks_replay():
    service, *_ = make_identity()
    _, tokens = service.register(RegisterInput(display_name="A", password="StrongPass123", phone_number="+243999000111"))
    new_tokens = service.refresh(tokens.refresh_token)
    assert new_tokens.refresh_token != tokens.refresh_token
    with pytest.raises(ValueError, match="invalid_refresh_token"):
        service.refresh(tokens.refresh_token)


def test_bad_password_is_rejected():
    service, *_ = make_identity()
    service.register(RegisterInput(display_name="A", password="StrongPass123", email="a@example.com"))
    with pytest.raises(ValueError, match="invalid_credentials"):
        service.login(login="a@example.com", password="wrong-password")


def test_short_jwt_secret_is_rejected():
    with pytest.raises(ValueError, match="at least 32"):
        JwtTokenIssuer(secret="short")


def test_refresh_token_reuse_revokes_all_sessions_and_access_tokens():
    service, accounts, sessions, issuer, _ = make_identity()
    account, tokens = service.register(RegisterInput(display_name="A", password="StrongPass123", email="a2@example.com", device_name="phone"))
    rotated = service.refresh(tokens.refresh_token, "phone")
    # Replay of the already rotated token is treated as theft.
    with pytest.raises(ValueError, match="invalid_refresh_token"):
        service.refresh(tokens.refresh_token)
    assert all(not s.active for s in service.list_sessions(account.id))
    with pytest.raises(ValueError):
        Authenticator(accounts=accounts, tokens=issuer).authenticate(rotated.access_token)


def test_sessions_can_be_listed_and_one_device_revoked():
    service, *_ = make_identity()
    account, first = service.register(RegisterInput(display_name="A", password="StrongPass123", email="devices@example.com", device_name="Android"))
    _, second = service.login(login="devices@example.com", password="StrongPass123", device_name="Windows")
    active = [s for s in service.list_sessions(account.id) if s.active]
    assert len(active) == 2
    target = next(s for s in active if s.device_name == "Android")
    assert service.revoke_session(account_id=account.id, session_id=target.id)
    active_after = [s for s in service.list_sessions(account.id) if s.active]
    assert len(active_after) == 1 and active_after[0].device_name == "Windows"


def test_password_change_revokes_every_session_and_old_password():
    service, *_ = make_identity()
    account, _ = service.register(RegisterInput(display_name="A", password="StrongPass123", email="pw@example.com"))
    service.login(login="pw@example.com", password="StrongPass123", device_name="second")
    service.change_password(account_id=account.id, current_password="StrongPass123", new_password="NewStrongPass456")
    assert all(not s.active for s in service.list_sessions(account.id))
    with pytest.raises(ValueError, match="invalid_credentials"):
        service.login(login="pw@example.com", password="StrongPass123")
    service.login(login="pw@example.com", password="NewStrongPass456")


def test_password_recovery_code_expires_and_is_single_use():
    from app.modules.identity.infrastructure.memory import InMemoryRecoveryChallengeRepository, InMemoryVerificationSender
    accounts = InMemoryAccountRepository(); sessions = InMemorySessionRepository(); clock = Clock()
    recovery = InMemoryRecoveryChallengeRepository(); sender = InMemoryVerificationSender()
    service = IdentityService(accounts=accounts,sessions=sessions,hasher=Argon2PasswordHasher(),tokens=JwtTokenIssuer(secret="r"*64),now=clock,recovery=recovery,verification_sender=sender)
    account, _ = service.register(RegisterInput(display_name="A", password="StrongPass123", email="recover@example.com"))
    challenge_id = service.request_password_recovery("recover@example.com")
    assert sender.sent and sender.sent[-1]["destination"] == "recover@example.com"
    code = sender.sent[-1]["code"]
    service.confirm_password_recovery(challenge_id=challenge_id, code=code, new_password="RecoveredPass456")
    service.login(login="recover@example.com", password="RecoveredPass456")
    with pytest.raises(ValueError, match="invalid_or_expired_recovery_challenge"):
        service.confirm_password_recovery(challenge_id=challenge_id, code=code, new_password="AnotherPass789")


def test_password_recovery_limits_wrong_attempts_without_account_enumeration():
    from app.modules.identity.infrastructure.memory import InMemoryRecoveryChallengeRepository, InMemoryVerificationSender
    accounts = InMemoryAccountRepository(); sessions = InMemorySessionRepository(); clock = Clock()
    recovery = InMemoryRecoveryChallengeRepository(); sender = InMemoryVerificationSender()
    service = IdentityService(accounts=accounts,sessions=sessions,hasher=Argon2PasswordHasher(),tokens=JwtTokenIssuer(secret="s"*64),now=clock,recovery=recovery,verification_sender=sender)
    fake = service.request_password_recovery("missing@example.com")
    assert fake and sender.sent == []
    service.register(RegisterInput(display_name="A", password="StrongPass123", email="known@example.com"))
    challenge_id = service.request_password_recovery("known@example.com")
    for _ in range(5):
        with pytest.raises(ValueError, match="invalid_recovery_code"):
            service.confirm_password_recovery(challenge_id=challenge_id, code="000000", new_password="RecoveredPass456")
    with pytest.raises(ValueError, match="invalid_or_expired_recovery_challenge"):
        service.confirm_password_recovery(challenge_id=challenge_id, code=sender.sent[-1]["code"], new_password="RecoveredPass456")

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.domain.model import Account, AccountState, RefreshSession, RecoveryChallenge
from app.shared.infrastructure.database import Base


class AccountRow(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(512))
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(32), default="active")
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RefreshSessionRow(Base):
    __tablename__ = "refresh_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[str | None] = mapped_column(String(64), nullable=True)


class RecoveryChallengeRow(Base):
    __tablename__ = "recovery_challenges"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    destination: Mapped[str] = mapped_column(String(320))
    channel: Mapped[str] = mapped_column(String(16))
    code_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    attempts_left: Mapped[int] = mapped_column(Integer, default=5)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SqlAlchemyAccountRepository:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def get(self, account_id: str) -> Account | None:
        with self.session_factory() as session:
            row = session.get(AccountRow, account_id)
            return _account_from_row(row) if row else None

    def find_by_login(self, login: str) -> Account | None:
        key = login.strip()
        with self.session_factory() as session:
            stmt = select(AccountRow).where(
                (AccountRow.email == key.lower()) | (AccountRow.phone_number == key)
            )
            row = session.scalar(stmt)
            return _account_from_row(row) if row else None

    def save(self, account: Account) -> None:
        with self.session_factory() as session:
            session.merge(AccountRow(
                id=account.id,
                display_name=account.display_name,
                password_hash=account.password_hash,
                email=account.email,
                phone_number=account.phone_number,
                state=account.state.value,
                token_version=account.token_version,
                created_at=account.created_at,
            ))
            session.commit()


class SqlAlchemySessionRepository:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def get_by_hash(self, token_hash: str) -> RefreshSession | None:
        with self.session_factory() as session:
            row = session.scalar(select(RefreshSessionRow).where(RefreshSessionRow.token_hash == token_hash))
            return _session_from_row(row) if row else None

    def get(self, session_id: str) -> RefreshSession | None:
        with self.session_factory() as session:
            row = session.get(RefreshSessionRow, session_id)
            return _session_from_row(row) if row else None

    def list_for_account(self, account_id: str) -> list[RefreshSession]:
        with self.session_factory() as session:
            rows = session.scalars(select(RefreshSessionRow).where(RefreshSessionRow.account_id == account_id).order_by(RefreshSessionRow.created_at.desc())).all()
            return [_session_from_row(row) for row in rows]

    def save(self, item: RefreshSession) -> None:
        with self.session_factory() as session:
            session.merge(RefreshSessionRow(
                id=item.id, account_id=item.account_id, token_hash=item.token_hash, created_at=item.created_at,
                expires_at=item.expires_at, device_name=item.device_name, revoked_at=item.revoked_at, replaced_by=item.replaced_by,
            ))
            session.commit()

    def revoke(self, account_id: str, session_id: str, now) -> bool:
        with self.session_factory() as session:
            row = session.get(RefreshSessionRow, session_id)
            if row is None or row.account_id != account_id or row.revoked_at is not None:
                return False
            row.revoked_at = now
            session.commit()
            return True

    def revoke_all(self, account_id: str, now=None) -> int:
        from datetime import UTC, datetime
        now = now or datetime.now(UTC)
        with self.session_factory() as session:
            rows = session.scalars(select(RefreshSessionRow).where(RefreshSessionRow.account_id == account_id)).all()
            count = 0
            for row in rows:
                if row.revoked_at is None:
                    row.revoked_at = now
                    count += 1
            session.commit()
            return count



class SqlAlchemyRecoveryChallengeRepository:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def get(self, challenge_id: str) -> RecoveryChallenge | None:
        with self.session_factory() as session:
            row = session.get(RecoveryChallengeRow, challenge_id)
            if not row:
                return None
            return RecoveryChallenge(
                id=row.id, account_id=row.account_id, destination=row.destination, channel=row.channel,
                code_hash=row.code_hash, created_at=_utc(row.created_at), expires_at=_utc(row.expires_at),
                attempts_left=row.attempts_left, consumed_at=_utc(row.consumed_at),
            )

    def save(self, c: RecoveryChallenge) -> None:
        with self.session_factory() as session:
            session.merge(RecoveryChallengeRow(
                id=c.id, account_id=c.account_id, destination=c.destination, channel=c.channel, code_hash=c.code_hash,
                created_at=c.created_at, expires_at=c.expires_at, attempts_left=c.attempts_left, consumed_at=c.consumed_at,
            ))
            session.commit()


def _utc(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _account_from_row(row: AccountRow) -> Account:
    return Account(
        id=row.id,
        display_name=row.display_name,
        password_hash=row.password_hash,
        email=row.email,
        phone_number=row.phone_number,
        state=AccountState(row.state),
        token_version=row.token_version,
        created_at=_utc(row.created_at),
    )


def _session_from_row(row: RefreshSessionRow) -> RefreshSession:
    return RefreshSession(
        id=row.id,
        account_id=row.account_id,
        token_hash=row.token_hash,
        created_at=_utc(row.created_at),
        expires_at=_utc(row.expires_at),
        device_name=row.device_name,
        revoked_at=_utc(row.revoked_at),
        replaced_by=row.replaced_by,
    )

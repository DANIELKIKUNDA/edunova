from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.sync.domain.model import (
    DeviceRegistration,
    MergePolicy,
    MutationOutcome,
    PullPage,
    SyncDisposition,
    SyncMutation,
    SyncOperation,
    SyncRecord,
    SyncDeviceView,
    merge_monotonic_progress,
    policy_for,
)
from app.shared.infrastructure.database import Base


class SyncDeviceRow(Base):
    __tablename__ = "sync_devices"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(160))
    platform: Mapped[str] = mapped_column(String(32))
    app_version: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acked_cursor: Mapped[int] = mapped_column(BigInteger, default=0)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class SyncAccountStateRow(Base):
    __tablename__ = "sync_account_state"
    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    retained_floor: Mapped[int] = mapped_column(BigInteger, default=0)
    last_compacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SyncRecordRow(Base):
    __tablename__ = "sync_records"
    __table_args__ = (UniqueConstraint("account_id", "entity_type", "entity_id", name="uq_sync_record_owner_entity"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    client_modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_device_id: Mapped[str] = mapped_column(String(128))
    server_seq: Mapped[int] = mapped_column(BigInteger, default=0, index=True)


class SyncChangeRow(Base):
    __tablename__ = "sync_changes"
    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(128))
    version: Mapped[int] = mapped_column(Integer)
    payload_json: Mapped[str] = mapped_column(Text)
    deleted: Mapped[bool] = mapped_column(Boolean)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SyncMutationInboxRow(Base):
    __tablename__ = "sync_mutation_inbox"
    __table_args__ = (UniqueConstraint("account_id", "mutation_id", name="uq_sync_mutation_owner_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    mutation_id: Mapped[str] = mapped_column(String(128), index=True)
    disposition: Mapped[str] = mapped_column(String(32))
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemySyncRepository:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def register_device(self, *, account_id: str, registration: DeviceRegistration, now: datetime) -> None:
        with self.session_factory() as session:
            row = session.get(SyncDeviceRow, registration.device_id)
            if row and row.account_id != account_id:
                raise ValueError("device_id_already_registered")
            if row is None:
                row = SyncDeviceRow(
                    id=registration.device_id, account_id=account_id, name=registration.name,
                    platform=registration.platform, app_version=registration.app_version,
                    created_at=now, last_seen_at=now,
                )
                session.add(row)
            else:
                if row.revoked_at is not None:
                    raise ValueError("sync_device_revoked")
                row.name = registration.name
                row.platform = registration.platform
                row.app_version = registration.app_version
                row.last_seen_at = now
            state = session.get(SyncAccountStateRow, account_id)
            if state is None:
                session.add(SyncAccountStateRow(account_id=account_id, retained_floor=0, last_compacted_at=None))
            session.commit()

    def assert_device_active(self, *, account_id: str, device_id: str, now: datetime) -> None:
        with self.session_factory() as session:
            row = session.get(SyncDeviceRow, device_id)
            if row is None or row.account_id != account_id:
                raise ValueError("sync_device_not_registered")
            if row.revoked_at is not None:
                raise ValueError("sync_device_revoked")
            row.last_seen_at = now
            session.commit()

    def list_devices(self, *, account_id: str) -> tuple[SyncDeviceView, ...]:
        with self.session_factory() as session:
            rows = session.scalars(select(SyncDeviceRow).where(SyncDeviceRow.account_id == account_id).order_by(SyncDeviceRow.last_seen_at.desc())).all()
            return tuple(SyncDeviceView(
                device_id=r.id, name=r.name, platform=r.platform, app_version=r.app_version,
                acked_cursor=int(r.acked_cursor or 0), created_at=_utc(r.created_at), last_seen_at=_utc(r.last_seen_at),
                last_sync_at=_utc(r.last_sync_at) if r.last_sync_at else None, revoked_at=_utc(r.revoked_at) if r.revoked_at else None,
            ) for r in rows)

    def revoke_device(self, *, account_id: str, device_id: str, now: datetime) -> None:
        with self.session_factory() as session:
            row = session.get(SyncDeviceRow, device_id)
            if row is None or row.account_id != account_id:
                raise ValueError("sync_device_not_registered")
            row.revoked_at = row.revoked_at or now
            session.commit()

    def acknowledge(self, *, account_id: str, device_id: str, cursor: int, now: datetime) -> int:
        with self.session_factory() as session:
            row = session.get(SyncDeviceRow, device_id)
            if row is None or row.account_id != account_id:
                raise ValueError("sync_device_not_registered")
            if row.revoked_at is not None:
                raise ValueError("sync_device_revoked")
            latest = int(session.scalar(select(func.max(SyncChangeRow.seq)).where(SyncChangeRow.account_id == account_id)) or 0)
            if cursor > latest:
                raise ValueError("sync_ack_cursor_ahead")
            row.acked_cursor = max(int(row.acked_cursor or 0), cursor)
            row.last_seen_at = now
            row.last_sync_at = now
            session.commit()
            return int(row.acked_cursor)

    def retained_floor(self, *, account_id: str) -> int:
        with self.session_factory() as session:
            row = session.get(SyncAccountStateRow, account_id)
            return int(row.retained_floor or 0) if row else 0

    def compact(self, *, account_id: str, now: datetime, inactive_days: int = 90, safety_window: int = 50) -> dict:
        with self.session_factory() as session:
            state = session.get(SyncAccountStateRow, account_id)
            if state is None:
                state = SyncAccountStateRow(account_id=account_id, retained_floor=0, last_compacted_at=None)
                session.add(state)
                session.flush()
            active_after = now - timedelta(days=max(7, inactive_days))
            devices = session.scalars(select(SyncDeviceRow).where(
                SyncDeviceRow.account_id == account_id, SyncDeviceRow.revoked_at.is_(None), SyncDeviceRow.last_seen_at >= active_after
            )).all()
            latest = int(session.scalar(select(func.max(SyncChangeRow.seq)).where(SyncChangeRow.account_id == account_id)) or 0)
            if devices:
                target = max(0, min(int(d.acked_cursor or 0) for d in devices) - max(0, safety_window))
            else:
                target = max(0, latest - max(0, safety_window))
            new_floor = max(int(state.retained_floor or 0), target)
            deleted_changes = 0
            if new_floor > int(state.retained_floor or 0):
                from sqlalchemy import delete
                result = session.execute(delete(SyncChangeRow).where(SyncChangeRow.account_id == account_id, SyncChangeRow.seq <= new_floor))
                deleted_changes = int(result.rowcount or 0)
                state.retained_floor = new_floor
            # Mutation inbox entries are retained long enough for replay protection, then pruned.
            from sqlalchemy import delete
            cutoff = now - timedelta(days=90)
            result = session.execute(delete(SyncMutationInboxRow).where(SyncMutationInboxRow.account_id == account_id, SyncMutationInboxRow.created_at < cutoff))
            deleted_inbox = int(result.rowcount or 0)
            state.last_compacted_at = now
            session.commit()
            return {"retained_floor": int(state.retained_floor or 0), "latest_cursor": latest, "deleted_changes": deleted_changes, "deleted_inbox": deleted_inbox}

    def apply_mutation(self, *, account_id: str, device_id: str, mutation: SyncMutation, now: datetime) -> MutationOutcome:
        with self.session_factory() as session:
            device = session.get(SyncDeviceRow, device_id)
            if device is None or device.account_id != account_id:
                raise ValueError("sync_device_not_registered")
            if device.revoked_at is not None:
                raise ValueError("sync_device_revoked")
            device.last_seen_at = now

            inbox = session.scalar(select(SyncMutationInboxRow).where(
                SyncMutationInboxRow.account_id == account_id,
                SyncMutationInboxRow.mutation_id == mutation.mutation_id,
            ))
            if inbox:
                parsed = json.loads(inbox.result_json)
                original = SyncDisposition(parsed.get("disposition", inbox.disposition))
                record = _record_from_dict(parsed.get("record")) if parsed.get("record") else None
                canonical = _record_from_dict(parsed.get("canonical")) if parsed.get("canonical") else None
                # Replaying the same mutation must reproduce its semantic result.
                # This is critical when the first HTTP response was lost after commit.
                return MutationOutcome(
                    mutation.mutation_id,
                    original if original is SyncDisposition.CONFLICT else SyncDisposition.DUPLICATE,
                    record=record,
                    canonical=canonical,
                    reason=(parsed.get("reason") or "mutation_already_applied"),
                )

            row = session.scalar(select(SyncRecordRow).where(
                SyncRecordRow.account_id == account_id,
                SyncRecordRow.entity_type == mutation.entity_type,
                SyncRecordRow.entity_id == mutation.entity_id,
            ))
            policy = policy_for(mutation.entity_type).policy

            if policy is MergePolicy.APPEND_ONLY and mutation.operation is SyncOperation.DELETE:
                outcome = MutationOutcome(mutation.mutation_id, SyncDisposition.REJECTED, reason="append_only_entity_cannot_delete")
                self._save_inbox(session, account_id, outcome, now)
                session.commit()
                return outcome

            if row is None and mutation.base_version not in (None, 0):
                outcome = MutationOutcome(mutation.mutation_id, SyncDisposition.REJECTED, reason="base_version_on_missing_entity")
                self._save_inbox(session, account_id, outcome, now)
                session.commit()
                return outcome

            if policy is MergePolicy.APPEND_ONLY and row is not None:
                current_payload = json.loads(row.payload_json)
                same = current_payload == mutation.payload and row.deleted == (mutation.operation is SyncOperation.DELETE)
                if same:
                    outcome = MutationOutcome(mutation.mutation_id, SyncDisposition.DUPLICATE, record=_to_record(row), reason="append_event_already_present")
                    self._save_inbox(session, account_id, outcome, now)
                    session.commit()
                    return outcome
                outcome = MutationOutcome(mutation.mutation_id, SyncDisposition.CONFLICT, canonical=_to_record(row), reason="append_only_entity_is_immutable")
                self._save_inbox(session, account_id, outcome, now)
                session.commit()
                return outcome

            if row is not None and policy is MergePolicy.OPTIMISTIC:
                if mutation.base_version is None or mutation.base_version != row.version:
                    outcome = MutationOutcome(mutation.mutation_id, SyncDisposition.CONFLICT, canonical=_to_record(row), reason="base_version_mismatch")
                    self._save_inbox(session, account_id, outcome, now)
                    session.commit()
                    return outcome

            if mutation.operation is SyncOperation.DELETE:
                payload = {}
                deleted = True
            elif row is not None and policy is MergePolicy.MONOTONIC_PROGRESS:
                payload = merge_monotonic_progress(json.loads(row.payload_json), mutation.payload)
                deleted = False
            else:
                payload = dict(mutation.payload)
                deleted = False

            if row is None:
                row = SyncRecordRow(
                    account_id=account_id, entity_type=mutation.entity_type, entity_id=mutation.entity_id,
                    version=1, payload_json=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                    deleted=deleted, client_modified_at=mutation.client_modified_at,
                    updated_at=now, last_device_id=device_id, server_seq=0,
                )
                session.add(row)
                session.flush()
            else:
                row.version += 1
                row.payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
                row.deleted = deleted
                row.client_modified_at = mutation.client_modified_at
                row.updated_at = now
                row.last_device_id = device_id

            change = SyncChangeRow(
                account_id=account_id, entity_type=row.entity_type, entity_id=row.entity_id,
                version=row.version, payload_json=row.payload_json, deleted=row.deleted, changed_at=now,
            )
            session.add(change)
            session.flush()
            row.server_seq = change.seq
            outcome = MutationOutcome(mutation.mutation_id, SyncDisposition.APPLIED, record=_to_record(row))
            self._save_inbox(session, account_id, outcome, now)
            session.commit()
            return outcome

    def pull(self, *, account_id: str, cursor: int, limit: int) -> PullPage:
        with self.session_factory() as session:
            rows = session.scalars(
                select(SyncChangeRow)
                .where(SyncChangeRow.account_id == account_id, SyncChangeRow.seq > cursor)
                .order_by(SyncChangeRow.seq.asc())
                .limit(limit + 1)
            ).all()
            has_more = len(rows) > limit
            rows = rows[:limit]
            changes = tuple(SyncRecord(
                entity_type=r.entity_type, entity_id=r.entity_id, version=r.version,
                payload=json.loads(r.payload_json), deleted=r.deleted,
                updated_at=_utc(r.changed_at), server_seq=r.seq,
            ) for r in rows)
            next_cursor = rows[-1].seq if rows else cursor
            return PullPage(changes=changes, next_cursor=next_cursor, has_more=has_more)

    def snapshot(self, *, account_id: str) -> PullPage:
        with self.session_factory() as session:
            rows = session.scalars(
                select(SyncRecordRow)
                .where(SyncRecordRow.account_id == account_id, SyncRecordRow.deleted.is_(False))
                .order_by(SyncRecordRow.entity_type.asc(), SyncRecordRow.entity_id.asc())
            ).all()
            cursor = int(session.scalar(select(func.max(SyncChangeRow.seq)).where(SyncChangeRow.account_id == account_id)) or 0)
            changes = tuple(_to_record(row) for row in rows)
            return PullPage(changes=changes, next_cursor=cursor, has_more=False)

    def latest_cursor(self, *, account_id: str) -> int:
        with self.session_factory() as session:
            value = session.scalar(select(func.max(SyncChangeRow.seq)).where(SyncChangeRow.account_id == account_id))
            return int(value or 0)

    @staticmethod
    def _save_inbox(session, account_id: str, outcome: MutationOutcome, now: datetime) -> None:
        data = {
            "disposition": outcome.disposition.value,
            "reason": outcome.reason,
            "record": _record_to_dict(outcome.record) if outcome.record else None,
            "canonical": _record_to_dict(outcome.canonical) if outcome.canonical else None,
        }
        session.add(SyncMutationInboxRow(
            account_id=account_id, mutation_id=outcome.mutation_id, disposition=outcome.disposition.value,
            result_json=json.dumps(data, ensure_ascii=False, separators=(",", ":")), created_at=now,
        ))


def _record_to_dict(r: SyncRecord) -> dict:
    return {
        "entity_type": r.entity_type, "entity_id": r.entity_id, "version": r.version,
        "payload": r.payload, "deleted": r.deleted, "updated_at": r.updated_at.isoformat(), "server_seq": r.server_seq,
    }


def _record_from_dict(data: dict) -> SyncRecord:
    return SyncRecord(
        entity_type=data["entity_type"], entity_id=data["entity_id"], version=int(data["version"]),
        payload=dict(data.get("payload", {})), deleted=bool(data.get("deleted", False)),
        updated_at=datetime.fromisoformat(data["updated_at"]), server_seq=int(data.get("server_seq", 0)),
    )


def _to_record(row: SyncRecordRow) -> SyncRecord:
    return SyncRecord(
        entity_type=row.entity_type, entity_id=row.entity_id, version=row.version,
        payload=json.loads(row.payload_json), deleted=row.deleted,
        updated_at=_utc(row.updated_at), server_seq=int(row.server_seq or 0),
    )


def _utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.database import Base


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(96), index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SqlAuditSink:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def write(self, *, actor_id: str | None, action: str, entity_type: str, entity_id: str | None = None, metadata: dict | None = None) -> None:
        with self.session_factory() as session:
            session.add(AuditEventRow(
                id=str(uuid4()),
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                metadata_json=json.dumps(metadata or {}, sort_keys=True),
                occurred_at=datetime.now(UTC),
            ))
            session.commit()

    def list_for_entity(self, *, entity_type: str, entity_id: str, limit: int = 100) -> tuple[dict, ...]:
        with self.session_factory() as session:
            rows = session.scalars(
                select(AuditEventRow)
                .where(AuditEventRow.entity_type == entity_type, AuditEventRow.entity_id == entity_id)
                .order_by(AuditEventRow.occurred_at.desc())
                .limit(max(1, min(int(limit), 500)))
            ).all()
            out = []
            for r in rows:
                try:
                    metadata = json.loads(r.metadata_json or "{}")
                except Exception:
                    metadata = {}
                out.append({
                    "id": r.id, "actor_id": r.actor_id, "action": r.action,
                    "entity_type": r.entity_type, "entity_id": r.entity_id,
                    "metadata": metadata,
                    "occurred_at": r.occurred_at if r.occurred_at.tzinfo else r.occurred_at.replace(tzinfo=UTC),
                })
            return tuple(out)

    def list_platform_events(self, *, limit: int = 50, offset: int = 0) -> dict:
        """Whitelisted central governance events only; no arbitrary audit metadata exposed."""
        from sqlalchemy import func
        allowed = ('platform.institution.state_changed', 'platform.role.granted',
                   'platform.role.deactivated', 'platform.institution.administrator_assigned',
                   'platform.institution.administrator_revoked', 'platform.support.ticket_created',
                   'platform.support.ticket_updated')
        with self.session_factory() as session:
            condition = AuditEventRow.action.in_(allowed)
            total = session.scalar(select(func.count()).select_from(AuditEventRow).where(condition)) or 0
            rows = session.scalars(select(AuditEventRow).where(condition)
                .order_by(AuditEventRow.occurred_at.desc(), AuditEventRow.id.desc())
                .limit(limit).offset(offset)).all()
            return {'total': total, 'limit': limit, 'offset': offset, 'items': [
                {'id': r.id, 'actor_id': r.actor_id, 'action': r.action,
                 'entity_type': r.entity_type, 'entity_id': r.entity_id,
                 'occurred_at': r.occurred_at.isoformat()} for r in rows]}

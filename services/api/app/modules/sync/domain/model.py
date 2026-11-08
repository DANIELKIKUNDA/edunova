from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class SyncOperation(StrEnum):
    UPSERT = "upsert"
    DELETE = "delete"


class SyncDisposition(StrEnum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    REJECTED = "rejected"


class MergePolicy(StrEnum):
    OPTIMISTIC = "optimistic"
    APPEND_ONLY = "append_only"
    MONOTONIC_PROGRESS = "monotonic_progress"
    LOCAL_ONLY = "local_only"
    SERVER_AUTHORITATIVE = "server_authoritative"


@dataclass(frozen=True)
class EntitySyncPolicy:
    entity_type: str
    policy: MergePolicy
    max_payload_bytes: int = 24_000


SYNC_POLICIES: dict[str, EntitySyncPolicy] = {
    "academic_profile": EntitySyncPolicy("academic_profile", MergePolicy.OPTIMISTIC, 8_000),
    "calendar_event": EntitySyncPolicy("calendar_event", MergePolicy.OPTIMISTIC, 12_000),
    "timetable_entry": EntitySyncPolicy("timetable_entry", MergePolicy.OPTIMISTIC, 8_000),
    "planning_preferences": EntitySyncPolicy("planning_preferences", MergePolicy.OPTIMISTIC, 8_000),
    "reading_progress": EntitySyncPolicy("reading_progress", MergePolicy.MONOTONIC_PROGRESS, 8_000),
    "objective_mastery": EntitySyncPolicy("objective_mastery", MergePolicy.OPTIMISTIC, 8_000),
    "course_follow": EntitySyncPolicy("course_follow", MergePolicy.OPTIMISTIC, 4_000),
    "quiz_attempt": EntitySyncPolicy("quiz_attempt", MergePolicy.APPEND_ONLY, 16_000),
    "quiz_answer": EntitySyncPolicy("quiz_answer", MergePolicy.APPEND_ONLY, 16_000),
    "flashcard_review": EntitySyncPolicy("flashcard_review", MergePolicy.APPEND_ONLY, 12_000),
    "study_session": EntitySyncPolicy("study_session", MergePolicy.APPEND_ONLY, 12_000),
    "plan_action": EntitySyncPolicy("plan_action", MergePolicy.APPEND_ONLY, 12_000),
    "error_event": EntitySyncPolicy("error_event", MergePolicy.APPEND_ONLY, 12_000),
    # Privacy boundary: these types never leave the device through Sync.
    "personal_document": EntitySyncPolicy("personal_document", MergePolicy.LOCAL_ONLY),
    "personal_document_chunk": EntitySyncPolicy("personal_document_chunk", MergePolicy.LOCAL_ONLY),
    "personal_assistant_message": EntitySyncPolicy("personal_assistant_message", MergePolicy.LOCAL_ONLY),
    # Financial/auth truth is server-owned and can only be pulled through dedicated APIs.
    "entitlement": EntitySyncPolicy("entitlement", MergePolicy.SERVER_AUTHORITATIVE),
    "payment": EntitySyncPolicy("payment", MergePolicy.SERVER_AUTHORITATIVE),
    "ai_wallet": EntitySyncPolicy("ai_wallet", MergePolicy.SERVER_AUTHORITATIVE),
}


@dataclass(frozen=True)
class DeviceRegistration:
    device_id: str
    name: str
    platform: str
    app_version: str


@dataclass(frozen=True)
class SyncMutation:
    mutation_id: str
    entity_type: str
    entity_id: str
    operation: SyncOperation
    payload: dict[str, Any]
    base_version: int | None
    client_modified_at: datetime


@dataclass(frozen=True)
class SyncRecord:
    entity_type: str
    entity_id: str
    version: int
    payload: dict[str, Any]
    deleted: bool
    updated_at: datetime
    server_seq: int


@dataclass(frozen=True)
class MutationOutcome:
    mutation_id: str
    disposition: SyncDisposition
    record: SyncRecord | None = None
    reason: str | None = None
    canonical: SyncRecord | None = None


@dataclass(frozen=True)
class PullPage:
    changes: tuple[SyncRecord, ...]
    next_cursor: int
    has_more: bool
    retained_floor: int = 0
    reset_required: bool = False


@dataclass(frozen=True)
class SyncDeviceView:
    device_id: str
    name: str
    platform: str
    app_version: str
    acked_cursor: int
    created_at: datetime
    last_seen_at: datetime
    last_sync_at: datetime | None = None
    revoked_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.revoked_at is None


def policy_for(entity_type: str) -> EntitySyncPolicy:
    try:
        return SYNC_POLICIES[entity_type]
    except KeyError as exc:
        raise ValueError("unsupported_sync_entity_type") from exc


def validate_payload_size(payload: dict[str, Any], policy: EntitySyncPolicy) -> None:
    import json
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > policy.max_payload_bytes:
        raise ValueError("sync_payload_too_large")


def merge_monotonic_progress(current: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge reading progress without regressing accidentally across devices.

    Explicit reset is allowed only when `reset=true`, otherwise position/progress are
    monotonic and last-known metadata fields are refreshed from the incoming record.
    """
    if incoming.get("reset") is True:
        out = dict(incoming)
        out.pop("reset", None)
        return out
    out = dict(current)
    out.update({k: v for k, v in incoming.items() if k not in {"page", "position", "progress"}})
    for key in ("page", "position"):
        if key in current or key in incoming:
            out[key] = max(int(current.get(key, 0) or 0), int(incoming.get(key, 0) or 0))
    if "progress" in current or "progress" in incoming:
        out["progress"] = max(float(current.get("progress", 0.0) or 0.0), float(incoming.get("progress", 0.0) or 0.0))
    return out


def utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

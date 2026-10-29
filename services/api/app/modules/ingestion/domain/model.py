from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class BatchState(StrEnum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    CANCELLED = "cancelled"


class DocumentState(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class JobState(StrEnum):
    PENDING = "pending"
    RETRY = "retry"
    LEASED = "leased"
    SUCCEEDED = "succeeded"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class PreflightStatus(StrEnum):
    PASSED = "passed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class BatchDefaults:
    content_kind: str
    faculty_domain: str
    program: str
    level: str
    semester: str | None
    risk: str
    rights_status: str
    rights_note: str = ""


@dataclass(frozen=True, slots=True)
class IngestionBatch:
    id: str
    name: str
    created_by: str
    state: BatchState
    defaults: BatchDefaults
    manifest_version: int
    manifest_sha256: str | None
    created_at: datetime
    updated_at: datetime
    frozen_at: datetime | None = None
    cancelled_at: datetime | None = None
    manifest_json: str | None = None


@dataclass(frozen=True, slots=True)
class IngestionDocument:
    id: str
    batch_id: str
    idempotency_key: str
    filename: str
    declared_mime_type: str | None
    detected_mime_type: str
    size_bytes: int
    checksum_sha256: str
    storage_key: str | None
    page_count: int | None
    width_px: int | None
    height_px: int | None
    state: DocumentState
    preflight_status: PreflightStatus
    rejection_code: str | None
    duplicate_of_document_id: str | None
    created_at: datetime
    updated_at: datetime
    editorial_item_id: str | None = None


@dataclass(frozen=True, slots=True)
class IngestionJob:
    id: str
    batch_id: str
    document_id: str
    state: JobState
    priority: int
    attempt: int
    max_attempts: int
    next_run_at: datetime
    lease_owner: str | None
    lease_expires_at: datetime | None
    heartbeat_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class IngestionResult:
    id: str
    batch_id: str
    document_id: str
    job_id: str
    artifact_key: str
    artifact_sha256: str
    pipeline_version: str
    page_count: int
    sections_count: int
    chunks_count: int
    questions_count: int
    mean_ocr_confidence: float | None
    usable_text_ratio: float
    warnings: tuple[str, ...]
    needs_human_verification: bool
    editorial_item_id: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PreflightReport:
    detected_mime_type: str
    size_bytes: int
    checksum_sha256: str
    page_count: int | None = None
    width_px: int | None = None
    height_px: int | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BatchMetrics:
    total_documents: int = 0
    accepted: int = 0
    rejected: int = 0
    queued: int = 0
    processing: int = 0
    succeeded: int = 0
    failed: int = 0
    dead_letter: int = 0
    cancelled: int = 0
    oldest_pending_seconds: int | None = None
    throughput_per_hour: float = 0.0
    success_rate: float = 0.0
    warnings: tuple[str, ...] = field(default_factory=tuple)

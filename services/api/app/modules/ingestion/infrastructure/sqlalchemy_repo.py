from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, and_, func, or_, select, update
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.database import Base
from ..domain.model import (
    BatchDefaults, BatchState, DocumentState, IngestionBatch, IngestionDocument,
    IngestionJob, IngestionResult, JobState, PreflightStatus,
)


class IngestionBatchRow(Base):
    __tablename__ = "ingestion_batches"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(240), index=True)
    created_by: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(40), index=True)
    defaults_json: Mapped[str] = mapped_column(Text)
    manifest_version: Mapped[int] = mapped_column(Integer, default=1)
    manifest_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manifest_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngestionDocumentRow(Base):
    __tablename__ = "ingestion_documents"
    __table_args__ = (
        UniqueConstraint("batch_id", "idempotency_key", name="uq_ingestion_document_idempotency"),
        UniqueConstraint("batch_id", "checksum_sha256", name="uq_ingestion_document_checksum"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160))
    filename: Mapped[str] = mapped_column(String(320))
    declared_mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    detected_mime_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_key: Mapped[str | None] = mapped_column(String(640), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str] = mapped_column(String(40), index=True)
    preflight_status: Mapped[str] = mapped_column(String(40), index=True)
    rejection_code: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    duplicate_of_document_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    editorial_item_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)


class IngestionJobRow(Base):
    __tablename__ = "ingestion_jobs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    document_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    state: Mapped[str] = mapped_column(String(40), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=50, index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    lease_owner: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class IngestionResultRow(Base):
    __tablename__ = "ingestion_results"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    document_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    artifact_key: Mapped[str] = mapped_column(String(640))
    artifact_sha256: Mapped[str] = mapped_column(String(64), index=True)
    pipeline_version: Mapped[str] = mapped_column(String(80), index=True)
    page_count: Mapped[int] = mapped_column(Integer)
    sections_count: Mapped[int] = mapped_column(Integer)
    chunks_count: Mapped[int] = mapped_column(Integer)
    questions_count: Mapped[int] = mapped_column(Integer)
    mean_ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    usable_text_ratio: Mapped[float] = mapped_column(Float)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    needs_human_verification: Mapped[int] = mapped_column(Integer, default=0, index=True)
    editorial_item_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


def _utc(value):
    return value if value is None or value.tzinfo else value.replace(tzinfo=UTC)


def _defaults(raw: str) -> BatchDefaults:
    return BatchDefaults(**json.loads(raw))


class SqlAlchemyIngestionRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_batch(self, b: IngestionBatch) -> None:
        with self.session_factory() as s:
            s.merge(IngestionBatchRow(
                id=b.id, name=b.name, created_by=b.created_by, state=b.state.value,
                defaults_json=json.dumps(asdict(b.defaults)), manifest_version=b.manifest_version,
                manifest_sha256=b.manifest_sha256, created_at=b.created_at, updated_at=b.updated_at,
                frozen_at=b.frozen_at, cancelled_at=b.cancelled_at, manifest_json=b.manifest_json,
            )); s.commit()

    def get_batch(self, batch_id: str):
        with self.session_factory() as s:
            r=s.get(IngestionBatchRow,batch_id); return self._batch(r) if r else None

    def list_batches(self, *, limit=50, offset=0):
        with self.session_factory() as s:
            rows=s.scalars(select(IngestionBatchRow).order_by(IngestionBatchRow.created_at.desc()).offset(offset).limit(limit)).all()
            return tuple(self._batch(r) for r in rows)

    def save_document(self, d: IngestionDocument) -> None:
        with self.session_factory() as s:
            s.merge(IngestionDocumentRow(**{
                "id":d.id,"batch_id":d.batch_id,"idempotency_key":d.idempotency_key,"filename":d.filename,
                "declared_mime_type":d.declared_mime_type,"detected_mime_type":d.detected_mime_type,"size_bytes":d.size_bytes,
                "checksum_sha256":d.checksum_sha256,"storage_key":d.storage_key,"page_count":d.page_count,"width_px":d.width_px,
                "height_px":d.height_px,"state":d.state.value,"preflight_status":d.preflight_status.value,"rejection_code":d.rejection_code,
                "duplicate_of_document_id":d.duplicate_of_document_id,"created_at":d.created_at,"updated_at":d.updated_at,
                "editorial_item_id":d.editorial_item_id,
            })); s.commit()

    def get_document(self, document_id: str):
        with self.session_factory() as s:
            r=s.get(IngestionDocumentRow,document_id); return self._document(r) if r else None

    def list_documents(self, batch_id: str):
        with self.session_factory() as s:
            rows=s.scalars(select(IngestionDocumentRow).where(IngestionDocumentRow.batch_id==batch_id).order_by(IngestionDocumentRow.created_at)).all()
            return tuple(self._document(r) for r in rows)

    def find_document_by_idempotency(self,batch_id,key):
        with self.session_factory() as s:
            r=s.scalar(select(IngestionDocumentRow).where(IngestionDocumentRow.batch_id==batch_id,IngestionDocumentRow.idempotency_key==key)); return self._document(r) if r else None

    def find_document_by_checksum(self,batch_id,checksum):
        with self.session_factory() as s:
            r=s.scalar(select(IngestionDocumentRow).where(IngestionDocumentRow.batch_id==batch_id,IngestionDocumentRow.checksum_sha256==checksum)); return self._document(r) if r else None

    def find_successful_document_by_checksum(self,checksum):
        with self.session_factory() as s:
            r=s.scalar(select(IngestionDocumentRow).where(IngestionDocumentRow.checksum_sha256==checksum,IngestionDocumentRow.state==DocumentState.SUCCEEDED.value,IngestionDocumentRow.editorial_item_id.is_not(None)).order_by(IngestionDocumentRow.created_at).limit(1)); return self._document(r) if r else None

    def save_job(self, j: IngestionJob) -> None:
        with self.session_factory() as s:
            s.merge(IngestionJobRow(**{
                "id":j.id,"batch_id":j.batch_id,"document_id":j.document_id,"state":j.state.value,"priority":j.priority,
                "attempt":j.attempt,"max_attempts":j.max_attempts,"next_run_at":j.next_run_at,"lease_owner":j.lease_owner,
                "lease_expires_at":j.lease_expires_at,"heartbeat_at":j.heartbeat_at,"started_at":j.started_at,"completed_at":j.completed_at,
                "last_error":j.last_error,"created_at":j.created_at,"updated_at":j.updated_at,
            })); s.commit()

    def get_job(self,job_id):
        with self.session_factory() as s:
            r=s.get(IngestionJobRow,job_id); return self._job(r) if r else None

    def list_jobs(self,batch_id):
        with self.session_factory() as s:
            rows=s.scalars(select(IngestionJobRow).where(IngestionJobRow.batch_id==batch_id).order_by(IngestionJobRow.created_at)).all()
            return tuple(self._job(r) for r in rows)

    def claim_next_job(self, *, worker_id, now, lease_seconds):
        for _ in range(5):
            with self.session_factory() as s:
                row=s.scalar(select(IngestionJobRow).where(
                    IngestionJobRow.state.in_([JobState.PENDING.value,JobState.RETRY.value]),
                    IngestionJobRow.next_run_at<=now,
                ).order_by(IngestionJobRow.priority.desc(),IngestionJobRow.created_at).limit(1))
                if row is None:return None
                result=s.execute(update(IngestionJobRow).where(
                    IngestionJobRow.id==row.id,
                    IngestionJobRow.state.in_([JobState.PENDING.value,JobState.RETRY.value]),
                ).values(state=JobState.LEASED.value,lease_owner=worker_id,lease_expires_at=now+timedelta(seconds=lease_seconds),heartbeat_at=now,started_at=row.started_at or now,attempt=row.attempt+1,updated_at=now))
                if result.rowcount==1:
                    s.commit(); fresh=s.get(IngestionJobRow,row.id); return self._job(fresh)
                s.rollback()
        return None

    def heartbeat(self, *, job_id, worker_id, now, lease_seconds):
        with self.session_factory() as s:
            result=s.execute(update(IngestionJobRow).where(IngestionJobRow.id==job_id,IngestionJobRow.state==JobState.LEASED.value,IngestionJobRow.lease_owner==worker_id).values(heartbeat_at=now,lease_expires_at=now+timedelta(seconds=lease_seconds),updated_at=now)); s.commit(); return result.rowcount==1

    def recover_expired_leases(self, *, now):
        with self.session_factory() as s:
            rows=s.scalars(select(IngestionJobRow).where(IngestionJobRow.state==JobState.LEASED.value,IngestionJobRow.lease_expires_at<now)).all()
            count=0
            for row in rows:
                row.state=JobState.RETRY.value if row.attempt < row.max_attempts else JobState.DEAD_LETTER.value
                row.lease_owner=None; row.lease_expires_at=None; row.heartbeat_at=None; row.next_run_at=now; row.updated_at=now; row.last_error="worker_lease_expired"; count+=1
            s.commit(); return count

    def save_result(self,r:IngestionResult):
        with self.session_factory() as s:
            s.merge(IngestionResultRow(id=r.id,batch_id=r.batch_id,document_id=r.document_id,job_id=r.job_id,artifact_key=r.artifact_key,artifact_sha256=r.artifact_sha256,pipeline_version=r.pipeline_version,page_count=r.page_count,sections_count=r.sections_count,chunks_count=r.chunks_count,questions_count=r.questions_count,mean_ocr_confidence=r.mean_ocr_confidence,usable_text_ratio=r.usable_text_ratio,warnings_json=json.dumps(list(r.warnings)),needs_human_verification=1 if r.needs_human_verification else 0,editorial_item_id=r.editorial_item_id,created_at=r.created_at)); s.commit()

    def get_result_for_document(self,document_id):
        with self.session_factory() as s:
            r=s.scalar(select(IngestionResultRow).where(IngestionResultRow.document_id==document_id)); return self._result(r) if r else None

    def list_results(self,batch_id):
        with self.session_factory() as s:
            rows=s.scalars(select(IngestionResultRow).where(IngestionResultRow.batch_id==batch_id).order_by(IngestionResultRow.created_at)).all(); return tuple(self._result(r) for r in rows)

    @staticmethod
    def _batch(r):
        return IngestionBatch(r.id,r.name,r.created_by,BatchState(r.state),_defaults(r.defaults_json),r.manifest_version,r.manifest_sha256,_utc(r.created_at),_utc(r.updated_at),_utc(r.frozen_at),_utc(r.cancelled_at),r.manifest_json)
    @staticmethod
    def _document(r):
        return IngestionDocument(r.id,r.batch_id,r.idempotency_key,r.filename,r.declared_mime_type,r.detected_mime_type,r.size_bytes,r.checksum_sha256,r.storage_key,r.page_count,r.width_px,r.height_px,DocumentState(r.state),PreflightStatus(r.preflight_status),r.rejection_code,r.duplicate_of_document_id,_utc(r.created_at),_utc(r.updated_at),r.editorial_item_id)
    @staticmethod
    def _job(r):
        return IngestionJob(r.id,r.batch_id,r.document_id,JobState(r.state),r.priority,r.attempt,r.max_attempts,_utc(r.next_run_at),r.lease_owner,_utc(r.lease_expires_at),_utc(r.heartbeat_at),_utc(r.started_at),_utc(r.completed_at),r.last_error,_utc(r.created_at),_utc(r.updated_at))
    @staticmethod
    def _result(r):
        return IngestionResult(r.id,r.batch_id,r.document_id,r.job_id,r.artifact_key,r.artifact_sha256,r.pipeline_version,r.page_count,r.sections_count,r.chunks_count,r.questions_count,r.mean_ocr_confidence,r.usable_text_ratio,tuple(json.loads(r.warnings_json or "[]")),bool(r.needs_human_verification),r.editorial_item_id,_utc(r.created_at))

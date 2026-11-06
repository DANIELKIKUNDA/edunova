from __future__ import annotations

import hashlib
import io
import json
import tempfile
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from PIL import Image
from uuid import uuid4

from app.modules.editorial.domain.model import EditorialRole
from app.modules.document_engine.application.pipeline import PremiumDocumentPipeline

from .ports import EditorialBridge, IngestionRepository, MalwareScanner, StagingStorage
from .preflight import PreflightValidator
from ..domain.model import (
    BatchDefaults, BatchMetrics, BatchState, DocumentState, IngestionBatch,
    IngestionDocument, IngestionJob, IngestionResult, JobState, PreflightStatus,
)


class IngestionService:
    def __init__(self, *, repository: IngestionRepository, storage: StagingStorage, scanner: MalwareScanner,
                 preflight: PreflightValidator, editorial, editorial_bridge: EditorialBridge, now=lambda: datetime.now(UTC),
                 max_batch_files: int = 1000, max_attempts: int = 3, lease_seconds: int = 180,
                 sla_pending_minutes: int = 30, processing_actor_id: str | None = None, audit=None) -> None:
        self.repo = repository
        self.storage = storage
        self.scanner = scanner
        self.preflight = preflight
        self.editorial = editorial
        self.bridge = editorial_bridge
        self.now = now
        self.max_batch_files = max_batch_files
        self.max_attempts = max_attempts
        self.lease_seconds = lease_seconds
        self.sla_pending_minutes = sla_pending_minutes
        self.processing_actor_id = processing_actor_id
        self.audit = audit

    def _member(self, actor_id: str, *roles: EditorialRole):
        m = self.editorial._member(actor_id)
        if roles and m.role not in roles and m.role != EditorialRole.OWNER:
            raise PermissionError("ingestion_role_required")
        return m

    def create_batch(self, *, actor_id: str, name: str, defaults: BatchDefaults) -> IngestionBatch:
        self._member(actor_id, EditorialRole.EDITOR)
        if len(name.strip()) < 3:
            raise ValueError("batch_name_too_short")
        now = self.now()
        batch = IngestionBatch(str(uuid4()), name.strip(), actor_id, BatchState.DRAFT, defaults, 1, None, now, now)
        self.repo.save_batch(batch)
        self._audit(actor_id,"ingestion.batch.created","ingestion_batch",batch.id,{"name":batch.name})
        return batch

    def batches(self, actor_id: str, *, limit: int = 50, offset: int = 0):
        self._member(actor_id)
        return self.repo.list_batches(limit=limit, offset=offset)

    def detail(self, actor_id: str, batch_id: str):
        self._member(actor_id)
        batch = self._batch(batch_id)
        docs = self.repo.list_documents(batch_id)
        jobs = self.repo.list_jobs(batch_id)
        results = self.repo.list_results(batch_id)
        audit=tuple(self.audit.list_for_entity(entity_type="ingestion_batch",entity_id=batch_id,limit=300)) if self.audit and hasattr(self.audit,"list_for_entity") else ()
        return {"batch": batch, "documents": docs, "jobs": jobs, "results": results, "metrics": self.metrics(actor_id, batch_id), "audit": audit}

    def add_file(self, *, actor_id: str, batch_id: str, filename: str, payload: bytes,
                 declared_mime_type: str | None, idempotency_key: str) -> IngestionDocument:
        self._member(actor_id, EditorialRole.EDITOR)
        batch = self._batch(batch_id)
        if batch.state != BatchState.DRAFT:
            raise ValueError("batch_manifest_frozen")
        existing = self.repo.find_document_by_idempotency(batch_id, idempotency_key)
        if existing:
            return existing
        if len(self.repo.list_documents(batch_id)) >= self.max_batch_files:
            raise ValueError("batch_file_limit_exceeded")
        now = self.now()
        try:
            report = self.preflight.inspect(payload, filename=filename, declared_mime_type=declared_mime_type)
            self.scanner.scan(payload, filename=filename)
        except (ValueError, RuntimeError) as exc:
            code = str(exc)
            checksum = hashlib.sha256(payload).hexdigest() if payload else "0" * 64
            duplicate = self.repo.find_document_by_checksum(batch_id, checksum)
            if duplicate:
                return duplicate
            doc = IngestionDocument(str(uuid4()), batch_id, idempotency_key, filename, declared_mime_type,
                                    "application/octet-stream", len(payload), checksum, None, None, None, None,
                                    DocumentState.REJECTED, PreflightStatus.REJECTED, code, None, now, now)
            # Rejected rows are audit evidence; identical rejected uploads by idempotency key replay safely.
            self.repo.save_document(doc)
            self._audit(actor_id,"ingestion.document.rejected","ingestion_batch",batch_id,{"document_id":doc.id,"filename":filename,"reason":code})
            return doc
        duplicate = self.repo.find_document_by_checksum(batch_id, report.checksum_sha256)
        if duplicate:
            return duplicate
        global_duplicate = self.repo.find_successful_document_by_checksum(report.checksum_sha256)
        if global_duplicate:
            previous_batch=self.repo.get_batch(global_duplicate.batch_id)
            same_context=bool(previous_batch and previous_batch.defaults==batch.defaults)
            if same_context:
                doc = IngestionDocument(str(uuid4()), batch_id, idempotency_key, filename, declared_mime_type,
                                        report.detected_mime_type, report.size_bytes, report.checksum_sha256, None,
                                        report.page_count, report.width_px, report.height_px, DocumentState.SUCCEEDED,
                                        PreflightStatus.PASSED, None, global_duplicate.id, now, now, global_duplicate.editorial_item_id)
                self.repo.save_document(doc)
                self._audit(actor_id,"ingestion.document.deduplicated","ingestion_batch",batch_id,{"document_id":doc.id,"duplicate_of":global_duplicate.id,"editorial_item_id":global_duplicate.editorial_item_id})
                return doc
            doc = IngestionDocument(str(uuid4()), batch_id, idempotency_key, filename, declared_mime_type,
                                    report.detected_mime_type, report.size_bytes, report.checksum_sha256, None,
                                    report.page_count, report.width_px, report.height_px, DocumentState.REJECTED,
                                    PreflightStatus.REJECTED, "duplicate_source_different_context", global_duplicate.id, now, now, None)
            self.repo.save_document(doc)
            self._audit(actor_id,"ingestion.document.rejected","ingestion_batch",batch_id,{"document_id":doc.id,"reason":"duplicate_source_different_context","duplicate_of":global_duplicate.id})
            return doc
        doc_id = str(uuid4())
        suffix = Path(filename).suffix.lower() or (".pdf" if report.detected_mime_type == "application/pdf" else ".bin")
        storage_key = f"batches/{batch_id}/source/{doc_id}{suffix}"
        self.storage.put(storage_key, payload, content_type=report.detected_mime_type)
        doc = IngestionDocument(doc_id, batch_id, idempotency_key, filename, declared_mime_type,
                                report.detected_mime_type, report.size_bytes, report.checksum_sha256, storage_key,
                                report.page_count, report.width_px, report.height_px, DocumentState.ACCEPTED,
                                PreflightStatus.PASSED, None, None, now, now)
        self.repo.save_document(doc)
        self._audit(actor_id,"ingestion.document.accepted","ingestion_batch",batch_id,{"document_id":doc.id,"filename":filename,"size_bytes":doc.size_bytes,"pages":doc.page_count})
        return doc

    def add_image_bundle(self, *, actor_id:str, batch_id:str, bundle_name:str, files:list[tuple[str,bytes,str|None]], idempotency_key:str) -> IngestionDocument:
        self._member(actor_id, EditorialRole.EDITOR)
        if not files: raise ValueError("image_bundle_empty")
        if len(files)>100: raise ValueError("image_bundle_page_limit_exceeded")
        images=[]
        for filename,payload,mime in files:
            report=self.preflight.inspect(payload,filename=filename,declared_mime_type=mime)
            if not report.detected_mime_type.startswith("image/"): raise ValueError("image_bundle_requires_images")
            self.scanner.scan(payload,filename=filename)
            with Image.open(io.BytesIO(payload)) as im:
                images.append(im.convert("RGB").copy())
        out=io.BytesIO(); first,*rest=images
        first.save(out,format="PDF",save_all=True,append_images=rest,resolution=150.0)
        safe=(bundle_name.strip() or "document-scanné").replace("/","-").replace("\\","-")
        return self.add_file(actor_id=actor_id,batch_id=batch_id,filename=f"{safe}.pdf",payload=out.getvalue(),declared_mime_type="application/pdf",idempotency_key=idempotency_key)

    def remove_file(self, *, actor_id: str, batch_id: str, document_id: str) -> None:
        self._member(actor_id, EditorialRole.EDITOR)
        batch = self._batch(batch_id)
        if batch.state != BatchState.DRAFT:
            raise ValueError("batch_manifest_frozen")
        doc = self._document(document_id)
        if doc.batch_id != batch_id:
            raise ValueError("document_not_in_batch")
        if doc.storage_key:
            self.storage.delete(doc.storage_key)
        self.repo.save_document(replace(doc, state=DocumentState.CANCELLED, updated_at=self.now()))
        self._audit(actor_id,"ingestion.document.removed","ingestion_batch",batch_id,{"document_id":document_id})

    def start_batch(self, *, actor_id: str, batch_id: str, priority: int = 50) -> IngestionBatch:
        self._member(actor_id, EditorialRole.EDITOR)
        batch = self._batch(batch_id)
        if batch.state != BatchState.DRAFT:
            return batch
        all_docs = self.repo.list_documents(batch_id)
        valid_docs = [d for d in all_docs if d.state in {DocumentState.ACCEPTED, DocumentState.SUCCEEDED}]
        docs = [d for d in valid_docs if d.state == DocumentState.ACCEPTED]
        if not valid_docs:
            raise ValueError("batch_has_no_accepted_documents")
        # Canonical immutable manifest: the hash alone is insufficient for reproducibility.
        # Persist the exact snapshot used to launch the batch, including academic/rights context
        # and pipeline/policy versions. Runtime states are deliberately excluded.
        manifest_payload = {
            "schema_version": 1,
            "pipeline_version": "document-engine-v1",
            "preflight_policy": {
                "max_file_bytes": self.preflight.policy.max_file_bytes,
                "max_pdf_pages": self.preflight.policy.max_pdf_pages,
                "max_image_pixels": self.preflight.policy.max_image_pixels,
                "allowed_mime_types": list(self.preflight.policy.allowed_mime_types),
            },
            "defaults": {
                "content_kind": batch.defaults.content_kind,
                "faculty_domain": batch.defaults.faculty_domain,
                "program": batch.defaults.program,
                "level": batch.defaults.level,
                "semester": batch.defaults.semester,
                "risk": batch.defaults.risk,
                "rights_status": batch.defaults.rights_status,
                "rights_note": batch.defaults.rights_note,
            },
            "documents": [
                {
                    "id": d.id, "filename": d.filename, "checksum_sha256": d.checksum_sha256,
                    "detected_mime_type": d.detected_mime_type, "size_bytes": d.size_bytes,
                    "page_count": d.page_count, "duplicate_of_document_id": d.duplicate_of_document_id,
                }
                for d in sorted(valid_docs, key=lambda x: (x.checksum_sha256, x.filename, x.id))
            ],
        }
        manifest_json = json.dumps(manifest_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        manifest_sha = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
        now = self.now()
        existing_document_jobs={j.document_id for j in self.repo.list_jobs(batch_id)}
        for d in docs:
            if d.id not in existing_document_jobs:
                self.repo.save_job(IngestionJob(str(uuid4()), batch_id, d.id, JobState.PENDING, max(0, min(priority,100)), 0,
                                                 self.max_attempts, now, None, None, None, None, None, None, now, now))
            self.repo.save_document(replace(d, state=DocumentState.QUEUED, updated_at=now))
        frozen = replace(batch, state=BatchState.RUNNING if docs else BatchState.COMPLETED, manifest_version=batch.manifest_version + 1,
                         manifest_sha256=manifest_sha, frozen_at=now, updated_at=now, manifest_json=manifest_json)
        self.repo.save_batch(frozen)
        self._audit(actor_id,"ingestion.batch.started","ingestion_batch",batch_id,{"manifest_sha256":manifest_sha,"queued_jobs":len(docs),"deduplicated":len(valid_docs)-len(docs)})
        return frozen

    def cancel_batch(self, *, actor_id: str, batch_id: str) -> IngestionBatch:
        self._member(actor_id, EditorialRole.OWNER)
        batch = self._batch(batch_id)
        if batch.state in {BatchState.COMPLETED, BatchState.COMPLETED_WITH_ERRORS, BatchState.CANCELLED}:
            return batch
        now = self.now()
        for job in self.repo.list_jobs(batch_id):
            if job.state in {JobState.PENDING, JobState.RETRY}:
                self.repo.save_job(replace(job,state=JobState.CANCELLED,updated_at=now,completed_at=now))
        for doc in self.repo.list_documents(batch_id):
            if doc.state in {DocumentState.ACCEPTED,DocumentState.QUEUED}:
                self.repo.save_document(replace(doc,state=DocumentState.CANCELLED,updated_at=now))
        out=replace(batch,state=BatchState.CANCELLED,updated_at=now,cancelled_at=now); self.repo.save_batch(out); self._audit(actor_id,"ingestion.batch.cancelled","ingestion_batch",batch_id); return out

    def claim_job(self, *, worker_id: str) -> IngestionJob | None:
        return self.repo.claim_next_job(worker_id=worker_id, now=self.now(), lease_seconds=self.lease_seconds)

    def heartbeat(self, *, worker_id: str, job_id: str) -> bool:
        return self.repo.heartbeat(job_id=job_id,worker_id=worker_id,now=self.now(),lease_seconds=self.lease_seconds)

    def process_job(self, *, worker_id: str, job_id: str, pipeline: PremiumDocumentPipeline | None = None) -> IngestionResult:
        job=self.repo.get_job(job_id)
        if not job or job.state != JobState.LEASED or job.lease_owner != worker_id:
            raise ValueError("job_not_leased_by_worker")
        doc=self._document(job.document_id); batch=self._batch(job.batch_id)
        if not doc.storage_key: raise ValueError("document_has_no_storage")
        now=self.now(); self.repo.save_document(replace(doc,state=DocumentState.PROCESSING,updated_at=now))
        payload=self.storage.read(doc.storage_key)
        try:
            suffix=Path(doc.filename).suffix or (".pdf" if doc.detected_mime_type=="application/pdf" else ".img")
            # PDF/OCR readers reopen the source by name. On Windows an open
            # NamedTemporaryFile denies that second handle; close the writer
            # before processing and still clean the file on every exit path.
            with tempfile.TemporaryDirectory(prefix='edunova-ingestion-') as directory:
                source = Path(directory) / f'source{suffix}'
                source.write_bytes(payload)
                processed=(pipeline or PremiumDocumentPipeline()).process(source,title=Path(doc.filename).stem)
            artifact_key=f"batches/{batch.id}/artifacts/{doc.id}.json"
            artifact={
                "document_id":processed.document_id,"fingerprint_sha256":processed.fingerprint_sha256,"title":processed.title,
                "pages":[{"number":p.number,"text":p.text,"method":p.method.value,"confidence":p.confidence} for p in processed.pages],
                "sections":[{"id":s.id,"title":s.title,"level":s.level,"start_page":s.start_page,"end_page":s.end_page,"parent_id":s.parent_id} for s in processed.sections],
                "chunks":[{"id":c.id,"section_id":c.section_id,"start_page":c.start_page,"end_page":c.end_page,"text":c.text,"ordinal":c.ordinal,"token_estimate":c.token_estimate} for c in processed.chunks],
                "questions":[{"id":q.id,"number_label":q.number_label,"text":q.text,"start_page":q.start_page,"end_page":q.end_page,"confidence":q.confidence} for q in processed.questions],
                "quality":{"page_count":processed.quality.page_count,"pages_native_text":processed.quality.pages_native_text,"pages_ocr":processed.quality.pages_ocr,"pages_hybrid":processed.quality.pages_hybrid,"empty_pages":processed.quality.empty_pages,"mean_chars_per_page":processed.quality.mean_chars_per_page,"mean_ocr_confidence":processed.quality.mean_ocr_confidence,"warnings":list(processed.quality.warnings)},
            }
            artifact["pipeline_version"]="document-engine-v1"
            artifact_text=json.dumps(artifact,ensure_ascii=False,sort_keys=True)
            artifact_sha=hashlib.sha256(artifact_text.encode("utf-8")).hexdigest()
            self.storage.put_text(artifact_key,artifact_text)
            editorial_item_id=self.bridge.create_from_processed_document(actor_id=self.processing_actor_id or batch.created_by,batch=batch,document=doc,processed=processed,artifact_key=artifact_key)
            needs_verification=bool(processed.quality.pages_ocr or processed.quality.pages_hybrid or processed.quality.warnings)
            result=IngestionResult(str(uuid4()),batch.id,doc.id,job.id,artifact_key,artifact_sha,"document-engine-v1",processed.quality.page_count,len(processed.sections),len(processed.chunks),len(processed.questions),processed.quality.mean_ocr_confidence,processed.quality.usable_text_ratio,processed.quality.warnings,needs_verification,editorial_item_id,self.now())
            self.repo.save_result(result)
            self._audit(self.processing_actor_id or batch.created_by,"ingestion.document.succeeded","ingestion_batch",batch.id,{"document_id":doc.id,"editorial_item_id":editorial_item_id,"pages":result.page_count,"questions":result.questions_count})
            end=self.now(); self.repo.save_document(replace(doc,state=DocumentState.SUCCEEDED,updated_at=end,editorial_item_id=editorial_item_id)); self.repo.save_job(replace(job,state=JobState.SUCCEEDED,lease_owner=None,lease_expires_at=None,heartbeat_at=None,completed_at=end,updated_at=end,last_error=None))
            self._refresh_batch(batch.id)
            return result
        except Exception as exc:
            self.fail_job(worker_id=worker_id,job_id=job.id,error=str(exc)); raise

    def fail_job(self, *, worker_id: str, job_id: str, error: str) -> IngestionJob:
        job=self.repo.get_job(job_id)
        if not job or job.lease_owner != worker_id or job.state != JobState.LEASED: raise ValueError("job_not_leased_by_worker")
        now=self.now(); exhausted=job.attempt>=job.max_attempts
        state=JobState.DEAD_LETTER if exhausted else JobState.RETRY
        delay=min(1800,30*(2**max(0,job.attempt-1)))
        out=replace(job,state=state,lease_owner=None,lease_expires_at=None,heartbeat_at=None,next_run_at=now+timedelta(seconds=delay),last_error=error[:4000],completed_at=now if exhausted else None,updated_at=now); self.repo.save_job(out)
        doc=self._document(job.document_id); self.repo.save_document(replace(doc,state=DocumentState.DEAD_LETTER if exhausted else DocumentState.FAILED,rejection_code="processing_failed",updated_at=now))
        self._audit(f"worker:{worker_id}"[:64],"ingestion.job.dead_letter" if exhausted else "ingestion.job.retry_scheduled","ingestion_batch",job.batch_id,{"job_id":job.id,"document_id":job.document_id,"attempt":job.attempt,"error":error[:500]})
        self._refresh_batch(job.batch_id); return out

    def retry_dead_letter(self, *, actor_id: str, job_id: str) -> IngestionJob:
        self._member(actor_id, EditorialRole.OWNER)
        job=self.repo.get_job(job_id)
        if not job or job.state != JobState.DEAD_LETTER: raise ValueError("dead_letter_job_required")
        now=self.now(); out=replace(job,state=JobState.RETRY,attempt=0,next_run_at=now,lease_owner=None,lease_expires_at=None,heartbeat_at=None,completed_at=None,last_error=None,updated_at=now); self.repo.save_job(out)
        doc=self._document(job.document_id); self.repo.save_document(replace(doc,state=DocumentState.QUEUED,rejection_code=None,updated_at=now)); batch=self._batch(job.batch_id)
        if batch.state in {BatchState.COMPLETED_WITH_ERRORS,BatchState.COMPLETED}: self.repo.save_batch(replace(batch,state=BatchState.RUNNING,updated_at=now))
        self._audit(actor_id,"ingestion.job.manual_retry","ingestion_batch",job.batch_id,{"job_id":job.id,"document_id":job.document_id})
        return out

    def recover_expired_leases_internal(self) -> int:
        count=self.repo.recover_expired_leases(now=self.now())
        if count:
            for batch in self.repo.list_batches(limit=500,offset=0):
                for job in self.repo.list_jobs(batch.id):
                    if job.last_error=="worker_lease_expired" and job.state in {JobState.RETRY,JobState.DEAD_LETTER}:
                        doc=self.repo.get_document(job.document_id)
                        if doc and doc.state==DocumentState.PROCESSING:
                            self.repo.save_document(replace(doc,state=DocumentState.QUEUED if job.state==JobState.RETRY else DocumentState.DEAD_LETTER,updated_at=self.now(),rejection_code="worker_lease_expired"))
                self._refresh_batch(batch.id)
        return count

    def recover_leases(self, *, actor_id: str) -> int:
        self._member(actor_id, EditorialRole.OWNER)
        return self.recover_expired_leases_internal()

    def preview(self, actor_id:str, document_id:str, page:int=1) -> dict:
        self._member(actor_id); doc=self._document(document_id); result=self.repo.get_result_for_document(document_id)
        if not result: raise ValueError("ingestion_result_not_found")
        raw=json.loads(self.storage.read(result.artifact_key).decode("utf-8"))
        pages=raw.get("pages",[]); selected=next((p for p in pages if int(p.get("number",0))==page),None)
        if selected is None: raise ValueError("preview_page_not_found")
        questions=[q for q in raw.get("questions",[]) if int(q.get("start_page",0))<=page<=int(q.get("end_page",0))]
        return {"document_id":doc.id,"filename":doc.filename,"page":selected,"questions":questions,"quality":raw.get("quality",{}),"editorial_item_id":result.editorial_item_id}

    def dashboard(self, actor_id:str) -> dict:
        self._member(actor_id); batches=self.repo.list_batches(limit=200,offset=0)
        states={s.value:0 for s in BatchState}; backlog=dead=0; oldest=None
        for b in batches:
            states[b.state.value]+=1
            jobs=self.repo.list_jobs(b.id)
            for j in jobs:
                if j.state in {JobState.PENDING,JobState.RETRY,JobState.LEASED}:
                    backlog+=1; oldest=j.created_at if oldest is None or j.created_at<oldest else oldest
                if j.state==JobState.DEAD_LETTER: dead+=1
        age=max(0,int((self.now()-oldest).total_seconds())) if oldest else None
        return {"batches":len(batches),"states":states,"backlog_jobs":backlog,"dead_letter_jobs":dead,"oldest_pending_seconds":age,"sla_breached":bool(age is not None and age>self.sla_pending_minutes*60)}

    def metrics(self, actor_id: str, batch_id: str) -> BatchMetrics:
        self._member(actor_id); self._batch(batch_id)
        docs=self.repo.list_documents(batch_id); jobs=self.repo.list_jobs(batch_id); now=self.now()
        counts={s:sum(1 for d in docs if d.state==s) for s in DocumentState}
        pending=[j for j in jobs if j.state in {JobState.PENDING,JobState.RETRY,JobState.LEASED}]
        oldest=min((j.created_at for j in pending),default=None)
        oldest_seconds=max(0,int((now-oldest).total_seconds())) if oldest else None
        completed=[j for j in jobs if j.state==JobState.SUCCEEDED and j.completed_at]
        if completed:
            span=max(1.0,(max(j.completed_at for j in completed)-min(j.created_at for j in completed)).total_seconds()/3600)
            throughput=round(len(completed)/span,2)
        else: throughput=0.0
        terminal=counts[DocumentState.SUCCEEDED]+counts[DocumentState.DEAD_LETTER]
        success_rate=round(counts[DocumentState.SUCCEEDED]/terminal,4) if terminal else 0.0
        warnings=[]
        if oldest_seconds is not None and oldest_seconds>self.sla_pending_minutes*60:warnings.append("pending_sla_breached")
        if counts[DocumentState.DEAD_LETTER]>0:warnings.append("dead_letter_present")
        return BatchMetrics(len(docs),counts[DocumentState.ACCEPTED],counts[DocumentState.REJECTED],counts[DocumentState.QUEUED],counts[DocumentState.PROCESSING],counts[DocumentState.SUCCEEDED],counts[DocumentState.FAILED],counts[DocumentState.DEAD_LETTER],counts[DocumentState.CANCELLED],oldest_seconds,throughput,success_rate,tuple(warnings))

    def verify_manifest(self, actor_id: str, batch_id: str) -> dict:
        self._member(actor_id)
        batch = self._batch(batch_id)
        if not batch.manifest_sha256 or not batch.manifest_json:
            raise ValueError("batch_manifest_not_frozen")
        calculated = hashlib.sha256(batch.manifest_json.encode("utf-8")).hexdigest()
        hash_valid = calculated == batch.manifest_sha256
        try:
            snapshot = json.loads(batch.manifest_json)
        except json.JSONDecodeError:
            return {"batch_id": batch.id, "valid": False, "hash_valid": False, "documents_valid": False, "reason": "manifest_json_invalid"}
        current = {d.id: d for d in self.repo.list_documents(batch_id)}
        mismatches = []
        for expected in snapshot.get("documents", []):
            doc = current.get(expected.get("id"))
            if doc is None:
                mismatches.append({"document_id": expected.get("id"), "reason": "document_missing"})
                continue
            for field in ("filename", "checksum_sha256", "detected_mime_type", "size_bytes", "page_count", "duplicate_of_document_id"):
                if getattr(doc, field) != expected.get(field):
                    mismatches.append({"document_id": doc.id, "field": field, "reason": "immutable_field_changed"})
        valid = hash_valid and not mismatches
        if not valid:
            self._audit(actor_id, "ingestion.manifest.integrity_failed", "ingestion_batch", batch.id, {"hash_valid": hash_valid, "mismatches": mismatches[:20]})
        return {"batch_id": batch.id, "valid": valid, "hash_valid": hash_valid, "documents_valid": not mismatches, "manifest_sha256": batch.manifest_sha256, "calculated_sha256": calculated, "schema_version": snapshot.get("schema_version"), "document_count": len(snapshot.get("documents", [])), "mismatches": mismatches}

    def retry_dead_letters_bulk(self, *, actor_id: str, batch_id: str) -> dict:
        self._member(actor_id, EditorialRole.OWNER)
        batch = self._batch(batch_id)
        jobs = [j for j in self.repo.list_jobs(batch_id) if j.state == JobState.DEAD_LETTER]
        retried = []
        for job in jobs:
            retried.append(self.retry_dead_letter(actor_id=actor_id, job_id=job.id).id)
        self._audit(actor_id, "ingestion.batch.dead_letters_retried", "ingestion_batch", batch.id, {"count": len(retried)})
        return {"batch_id": batch.id, "retried": len(retried), "job_ids": retried}

    def batch_report(self, actor_id: str, batch_id: str) -> dict:
        d=self.detail(actor_id,batch_id); batch=d["batch"]
        return {"batch_id":batch.id,"name":batch.name,"state":batch.state.value,"manifest_sha256":batch.manifest_sha256,"manifest_integrity":self.verify_manifest(actor_id,batch_id) if batch.manifest_sha256 else None,"metrics":d["metrics"].__dict__ if hasattr(d["metrics"],"__dict__") else {k:getattr(d["metrics"],k) for k in d["metrics"].__dataclass_fields__},"documents":[{"id":x.id,"filename":x.filename,"state":x.state.value,"checksum_sha256":x.checksum_sha256,"rejection_code":x.rejection_code,"editorial_item_id":x.editorial_item_id} for x in d["documents"]]}

    def _refresh_batch(self,batch_id:str)->None:
        batch=self._batch(batch_id)
        if batch.state==BatchState.CANCELLED:return
        jobs=self.repo.list_jobs(batch_id)
        if not jobs:return
        if any(j.state in {JobState.PENDING,JobState.RETRY,JobState.LEASED} for j in jobs):return
        docs=self.repo.list_documents(batch_id)
        state=BatchState.COMPLETED_WITH_ERRORS if (any(j.state==JobState.DEAD_LETTER for j in jobs) or any(d.state==DocumentState.REJECTED for d in docs)) else BatchState.COMPLETED
        self.repo.save_batch(replace(batch,state=state,updated_at=self.now()))

    def _audit(self, actor_id:str|None, action:str, entity_type:str, entity_id:str|None, metadata:dict|None=None) -> None:
        if self.audit:
            self.audit.write(actor_id=actor_id,action=action,entity_type=entity_type,entity_id=entity_id,metadata=metadata or {})

    def _batch(self,batch_id):
        b=self.repo.get_batch(batch_id)
        if not b: raise ValueError("ingestion_batch_not_found")
        return b
    def _document(self,document_id):
        d=self.repo.get_document(document_id)
        if not d: raise ValueError("ingestion_document_not_found")
        return d

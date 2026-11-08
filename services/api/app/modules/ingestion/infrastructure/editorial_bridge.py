from __future__ import annotations

from app.modules.editorial.domain.model import ContentKind, RiskLevel, RightsStatus


class EditorialIngestionBridge:
    """Idempotent bridge from an ingestion result to a Studio draft.

    Source fingerprint is the dedupe key. A worker retry completes any missing
    revision/source instead of creating a second editorial item.
    """
    def __init__(self, editorial_service) -> None:
        self.editorial = editorial_service

    def create_from_processed_document(self, *, actor_id, batch, document, processed, artifact_key: str) -> str:
        item = self.editorial.repo.find_item_by_source_fingerprint(document.checksum_sha256)
        if item is not None:
            expected=(batch.defaults.content_kind,batch.defaults.faculty_domain,batch.defaults.program,batch.defaults.level,batch.defaults.semester,batch.defaults.risk,batch.defaults.rights_status)
            actual=(item.kind.value,item.faculty_domain,item.program,item.level,item.semester,item.risk.value,item.rights_status.value)
            if actual!=expected:
                raise ValueError("duplicate_source_context_mismatch")
        if item is None:
            item = self.editorial.create_item(
                actor_id=actor_id,
                kind=ContentKind(batch.defaults.content_kind),
                title=processed.title or document.filename,
                faculty_domain=batch.defaults.faculty_domain,
                program=batch.defaults.program,
                level=batch.defaults.level,
                semester=batch.defaults.semester,
                risk=RiskLevel(batch.defaults.risk),
                rights_status=RightsStatus(batch.defaults.rights_status),
                rights_note=batch.defaults.rights_note,
                source_fingerprint=document.checksum_sha256,
            )
        revisions = self.editorial.repo.list_revisions(item.id)
        if not any(r.source_fingerprint == document.checksum_sha256 for r in revisions):
            payload = {
                "ingestion": {"batch_id": batch.id, "document_id": document.id, "artifact_key": artifact_key, "filename": document.filename},
                "quality": {
                    "page_count": processed.quality.page_count,
                    "pages_native_text": processed.quality.pages_native_text,
                    "pages_ocr": processed.quality.pages_ocr,
                    "pages_hybrid": processed.quality.pages_hybrid,
                    "empty_pages": processed.quality.empty_pages,
                    "mean_ocr_confidence": processed.quality.mean_ocr_confidence,
                    "warnings": list(processed.quality.warnings),
                },
                "sections": [{"id":s.id,"title":s.title,"level":s.level,"start_page":s.start_page,"end_page":s.end_page} for s in processed.sections],
                "question_candidates": [{"id":q.id,"number_label":q.number_label,"text":q.text,"start_page":q.start_page,"end_page":q.end_page,"confidence":q.confidence} for q in processed.questions],
            }
            current = self.editorial.repo.get_item(item.id)
            self.editorial.add_revision(actor_id=actor_id,item_id=item.id,payload=payload,source_fingerprint=document.checksum_sha256,ai_generated=False,prompt_version=None,note=f"Ingestion industrielle LOT 12 — {document.filename}",expected_version=current.row_version)
        if self.editorial.repo.find_source_by_checksum(document.checksum_sha256) is None:
            confidence = processed.quality.mean_ocr_confidence if (processed.quality.pages_ocr or processed.quality.pages_hybrid) else None
            self.editorial.add_source(actor_id=actor_id,item_id=item.id,filename=document.filename,checksum_sha256=document.checksum_sha256,mime_type=document.detected_mime_type,size_bytes=document.size_bytes,storage_locator=document.storage_key,ocr_confidence=confidence)
        return item.id

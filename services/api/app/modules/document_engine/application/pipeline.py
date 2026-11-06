from __future__ import annotations

import hashlib
import mimetypes
import uuid
from pathlib import Path

from ..domain.model import (
    DocumentKind,
    DocumentQualityReport,
    ExtractionMethod,
    ProcessedDocument,
)
from ..infrastructure.ocr import TesseractOcr
from ..infrastructure.pdf import PdfTextExtractor
from .chunking import build_chunks
from .structure import build_sections
from .questions import extract_question_candidates


class PremiumDocumentPipeline:
    """Deterministic document preparation before any generative AI step.

    The output is auditable and cacheable by SHA-256. Shared documents can be
    processed server-side; private documents use an equivalent local adapter.
    """

    def __init__(self, *, enable_ocr: bool = True, ocr_languages: str = "fra+eng") -> None:
        self.ocr = TesseractOcr(ocr_languages) if enable_ocr else None

    def process(self, path: Path, *, title: str | None = None) -> ProcessedDocument:
        path = path.resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(path)
        fingerprint = _sha256(path)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if mime == "application/pdf" or path.suffix.lower() == ".pdf":
            extractor = PdfTextExtractor(self.ocr)
            pages, metadata = extractor.extract(path)
            kind = DocumentKind.PDF
        elif mime.startswith("image/") or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}:
            if self.ocr is None:
                raise RuntimeError("OCR is disabled for image documents")
            pages = (self.ocr.extract(path, page_number=1),)
            metadata = {}
            kind = DocumentKind.IMAGE
        else:
            raise ValueError(f"Unsupported document type: {mime}")
        sections = build_sections(pages)
        chunks = build_chunks(pages, sections)
        questions = extract_question_candidates(pages)
        quality = _quality(pages)
        resolved_title = title or metadata.get("title") or path.stem
        doc_id = f"doc-{uuid.uuid5(uuid.NAMESPACE_URL, fingerprint).hex[:16]}"
        return ProcessedDocument(
            document_id=doc_id,
            fingerprint_sha256=fingerprint,
            title=resolved_title,
            kind=kind,
            pages=pages,
            sections=sections,
            chunks=chunks,
            questions=questions,
            quality=quality,
            metadata=metadata,
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _quality(pages) -> DocumentQualityReport:
    native = sum(p.method is ExtractionMethod.NATIVE_TEXT for p in pages)
    ocr = sum(p.method is ExtractionMethod.OCR for p in pages)
    hybrid = sum(p.method is ExtractionMethod.HYBRID for p in pages)
    empty = sum(not p.text.strip() for p in pages)
    confidences = [p.confidence for p in pages if p.confidence is not None]
    warnings: list[str] = []
    if pages and empty / len(pages) > 0.10:
        warnings.append("Plus de 10 % des pages ne contiennent pas de texte exploitable.")
    if confidences and sum(confidences) / len(confidences) < 0.70:
        warnings.append("La confiance OCR moyenne est faible; une vérification humaine est recommandée.")
    joined = "\n".join(p.text for p in pages)
    if any(symbol in joined for symbol in ("∫", "√", "∑", "≈", "≠")) and (ocr or hybrid):
        warnings.append("Le document contient des symboles mathématiques et de l’OCR; les formules doivent être vérifiées.")
    mean_chars = sum(len(p.text) for p in pages) / len(pages) if pages else 0.0
    return DocumentQualityReport(
        page_count=len(pages),
        pages_native_text=native,
        pages_ocr=ocr,
        pages_hybrid=hybrid,
        empty_pages=empty,
        mean_chars_per_page=round(mean_chars, 2),
        mean_ocr_confidence=round(sum(confidences) / len(confidences), 4) if confidences else None,
        warnings=tuple(warnings),
    )

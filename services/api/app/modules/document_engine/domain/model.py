from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable


class DocumentKind(StrEnum):
    PDF = "pdf"
    IMAGE = "image"


class ExtractionMethod(StrEnum):
    NATIVE_TEXT = "native_text"
    OCR = "ocr"
    HYBRID = "hybrid"


@dataclass(frozen=True, slots=True)
class TextSpan:
    text: str
    font_size: float
    is_bold: bool
    page_number: int
    y0: float = 0.0


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    number: int
    text: str
    spans: tuple[TextSpan, ...] = ()
    method: ExtractionMethod = ExtractionMethod.NATIVE_TEXT
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class DocumentSection:
    id: str
    title: str
    level: int
    start_page: int
    end_page: int
    parent_id: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    id: str
    section_id: str | None
    start_page: int
    end_page: int
    text: str
    ordinal: int
    token_estimate: int


@dataclass(frozen=True, slots=True)
class QuestionCandidate:
    id: str
    number_label: str
    text: str
    start_page: int
    end_page: int
    confidence: float


@dataclass(frozen=True, slots=True)
class DocumentQualityReport:
    page_count: int
    pages_native_text: int
    pages_ocr: int
    pages_hybrid: int
    empty_pages: int
    mean_chars_per_page: float
    mean_ocr_confidence: float | None
    warnings: tuple[str, ...] = ()

    @property
    def usable_text_ratio(self) -> float:
        if self.page_count == 0:
            return 0.0
        usable = self.page_count - self.empty_pages
        return usable / self.page_count


@dataclass(frozen=True, slots=True)
class ProcessedDocument:
    document_id: str
    fingerprint_sha256: str
    title: str
    kind: DocumentKind
    pages: tuple[ExtractedPage, ...]
    sections: tuple[DocumentSection, ...]
    chunks: tuple[DocumentChunk, ...]
    questions: tuple[QuestionCandidate, ...]
    quality: DocumentQualityReport
    metadata: dict[str, str] = field(default_factory=dict)

    def page_text(self, number: int) -> str:
        for page in self.pages:
            if page.number == number:
                return page.text
        raise KeyError(number)


def iter_text(pages: Iterable[ExtractedPage]) -> str:
    return "\n\n".join(page.text for page in pages if page.text.strip())

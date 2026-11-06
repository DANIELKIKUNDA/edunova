from __future__ import annotations

import statistics
import tempfile
from pathlib import Path

import fitz

from ..domain.model import ExtractedPage, ExtractionMethod, TextSpan
from .ocr import TesseractOcr
from .text import normalize_text, remove_repeating_page_margins


class PdfTextExtractor:
    def __init__(self, ocr: TesseractOcr | None = None, *, native_threshold_chars: int = 48) -> None:
        self.ocr = ocr
        self.native_threshold_chars = native_threshold_chars

    def extract(self, pdf_path: Path) -> tuple[tuple[ExtractedPage, ...], dict[str, str]]:
        document = fitz.open(pdf_path)
        try:
            pages: list[ExtractedPage] = []
            for index in range(document.page_count):
                page = document.load_page(index)
                native_text, spans = self._native(page, index + 1)
                if len(native_text.replace("\n", "").strip()) >= self.native_threshold_chars:
                    pages.append(ExtractedPage(index + 1, native_text, tuple(spans), ExtractionMethod.NATIVE_TEXT))
                    continue
                if self.ocr is None:
                    pages.append(ExtractedPage(index + 1, native_text, tuple(spans), ExtractionMethod.NATIVE_TEXT))
                    continue
                pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
                    pix.save(tmp.name)
                    ocr_page = self.ocr.extract(Path(tmp.name), page_number=index + 1)
                if native_text and ocr_page.text:
                    # Keep the richer OCR text but mark hybrid so quality reporting is honest.
                    chosen = ocr_page if len(ocr_page.text) >= len(native_text) else ExtractedPage(
                        index + 1,
                        native_text,
                        tuple(spans),
                        ExtractionMethod.HYBRID,
                        ocr_page.confidence,
                    )
                    if chosen.method is ExtractionMethod.OCR:
                        chosen = ExtractedPage(chosen.number, chosen.text, tuple(spans), ExtractionMethod.HYBRID, chosen.confidence)
                    pages.append(chosen)
                else:
                    pages.append(ocr_page)
            cleaned_texts = remove_repeating_page_margins([item.text for item in pages])
            pages = [
                ExtractedPage(
                    number=item.number,
                    text=cleaned_texts[index],
                    spans=item.spans,
                    method=item.method,
                    confidence=item.confidence,
                )
                for index, item in enumerate(pages)
            ]
            metadata = {k: str(v) for k, v in document.metadata.items() if v}
            return tuple(pages), metadata
        finally:
            document.close()

    @staticmethod
    def _native(page: fitz.Page, page_number: int) -> tuple[str, list[TextSpan]]:
        payload = page.get_text("dict")
        lines: list[str] = []
        spans: list[TextSpan] = []
        for block in payload.get("blocks", []):
            if "lines" not in block:
                continue
            for line in block["lines"]:
                parts: list[str] = []
                for span in line.get("spans", []):
                    value = (span.get("text") or "").strip()
                    if not value:
                        continue
                    parts.append(value)
                    font_name = str(span.get("font", "")).lower()
                    flags = int(span.get("flags", 0))
                    spans.append(
                        TextSpan(
                            text=value,
                            font_size=float(span.get("size", 0.0)),
                            is_bold=("bold" in font_name) or bool(flags & 16),
                            page_number=page_number,
                            y0=float(span.get("bbox", [0, 0, 0, 0])[1]),
                        )
                    )
                if parts:
                    lines.append(" ".join(parts))
        return normalize_text("\n".join(lines)), spans


def dominant_font_size(pages: tuple[ExtractedPage, ...]) -> float:
    sizes = [span.font_size for page in pages for span in page.spans if span.font_size > 0]
    return statistics.median(sizes) if sizes else 11.0

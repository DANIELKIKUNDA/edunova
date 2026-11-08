from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

import fitz
from PIL import Image

from ..domain.model import PreflightReport


@dataclass(frozen=True, slots=True)
class PreflightPolicy:
    max_file_bytes: int = 80 * 1024 * 1024
    max_pdf_pages: int = 600
    max_image_pixels: int = 70_000_000
    allowed_mime_types: tuple[str, ...] = (
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    )


class PreflightValidator:
    def __init__(self, policy: PreflightPolicy | None = None) -> None:
        self.policy = policy or PreflightPolicy()

    def inspect(self, payload: bytes, *, filename: str, declared_mime_type: str | None = None) -> PreflightReport:
        if not payload:
            raise ValueError("empty_file")
        if len(payload) > self.policy.max_file_bytes:
            raise ValueError("file_too_large")
        mime = self._detect(payload)
        if mime not in self.policy.allowed_mime_types:
            raise ValueError("unsupported_file_signature")
        if declared_mime_type and declared_mime_type not in {mime, "application/octet-stream"}:
            raise ValueError("declared_mime_mismatch")
        checksum = hashlib.sha256(payload).hexdigest()
        if mime == "application/pdf":
            return self._pdf(payload, checksum)
        return self._image(payload, mime, checksum)

    @staticmethod
    def _detect(payload: bytes) -> str:
        if payload.startswith(b"%PDF-"):
            return "application/pdf"
        if payload.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if payload.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if len(payload) >= 12 and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
            return "image/webp"
        return "application/octet-stream"

    def _pdf(self, payload: bytes, checksum: str) -> PreflightReport:
        try:
            doc = fitz.open(stream=payload, filetype="pdf")
        except Exception as exc:
            raise ValueError("invalid_pdf") from exc
        try:
            if doc.needs_pass:
                raise ValueError("encrypted_pdf_not_supported")
            pages = int(doc.page_count)
            if pages <= 0:
                raise ValueError("empty_pdf")
            if pages > self.policy.max_pdf_pages:
                raise ValueError("pdf_page_limit_exceeded")
            return PreflightReport(
                detected_mime_type="application/pdf",
                size_bytes=len(payload),
                checksum_sha256=checksum,
                page_count=pages,
            )
        finally:
            doc.close()

    def _image(self, payload: bytes, mime: str, checksum: str) -> PreflightReport:
        try:
            with Image.open(io.BytesIO(payload)) as image:
                image.verify()
            with Image.open(io.BytesIO(payload)) as image:
                width, height = image.size
        except Exception as exc:
            raise ValueError("invalid_image") from exc
        if width <= 0 or height <= 0:
            raise ValueError("invalid_image_dimensions")
        if width * height > self.policy.max_image_pixels:
            raise ValueError("image_pixel_limit_exceeded")
        return PreflightReport(
            detected_mime_type=mime,
            size_bytes=len(payload),
            checksum_sha256=checksum,
            page_count=1,
            width_px=width,
            height_px=height,
        )

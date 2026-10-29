from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pytesseract import Output

from ..domain.model import ExtractedPage, ExtractionMethod
from .text import normalize_text


class TesseractOcr:
    """OCR adapter for server/shared documents or explicit opt-in processing.

    Personal device-only files should use a device-local adapter in the Flutter app.
    """

    def __init__(self, languages: str = "fra+eng") -> None:
        self.languages = languages
        if shutil.which("tesseract") is None:
            raise RuntimeError("tesseract binary not found")

    def extract(self, image_path: Path, *, page_number: int) -> ExtractedPage:
        processed = self._preprocess(image_path)
        data = pytesseract.image_to_data(
            Image.fromarray(processed),
            lang=self.languages,
            config="--oem 1 --psm 3",
            output_type=Output.DICT,
        )
        words: list[str] = []
        confidences: list[float] = []
        previous_line: tuple[int, int, int] | None = None
        for i, raw in enumerate(data["text"]):
            text = (raw or "").strip()
            if not text:
                continue
            try:
                conf = float(data["conf"][i])
            except (TypeError, ValueError):
                conf = -1
            if conf >= 0:
                confidences.append(conf)
            line_key = (int(data["block_num"][i]), int(data["par_num"][i]), int(data["line_num"][i]))
            if previous_line is not None and line_key != previous_line:
                words.append("\n")
            elif words and words[-1] != "\n":
                words.append(" ")
            words.append(text)
            previous_line = line_key
        confidence = (sum(confidences) / len(confidences)) / 100 if confidences else None
        return ExtractedPage(
            number=page_number,
            text=normalize_text("".join(words)),
            method=ExtractionMethod.OCR,
            confidence=confidence,
        )

    @staticmethod
    def _preprocess(image_path: Path) -> np.ndarray:
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")
        h, w = image.shape[:2]
        longest = max(h, w)
        if longest < 1800:
            scale = 1800 / longest
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        image = cv2.fastNlMeansDenoising(image, None, 9, 7, 21)
        image = TesseractOcr._deskew(image)
        image = cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            13,
        )
        return image


    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        inverted = cv2.bitwise_not(image)
        _, threshold = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        points = np.column_stack(np.where(threshold > 0))
        if len(points) < 50:
            return image
        angle = cv2.minAreaRect(points.astype(np.float32))[-1]
        angle = -(90 + angle) if angle < -45 else -angle
        if abs(angle) < 0.15 or abs(angle) > 12:
            return image
        h, w = image.shape[:2]
        matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    def extract_bytes(self, payload: bytes, *, suffix: str, page_number: int) -> ExtractedPage:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(payload)
            tmp.flush()
            return self.extract(Path(tmp.name), page_number=page_number)

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..domain.model import ExtractedPage


class PageOcr(Protocol):
    def extract(self, image_path: Path, *, page_number: int) -> ExtractedPage: ...


class ArtifactWriter(Protocol):
    def write(self, document, destination: Path) -> None: ...

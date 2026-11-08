from typing import Protocol


class OcrProvider(Protocol):
    async def extract_text(self, *, image_bytes: bytes) -> str: ...

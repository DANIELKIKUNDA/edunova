from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from app.modules.pedagogy.domain.model import SourceRef


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    task: str
    instruction: str
    source_refs: tuple[SourceRef, ...]
    response_schema: str
    locale: str = "fr"


@dataclass(frozen=True, slots=True)
class GenerationResponse:
    payload: dict
    provider: str
    model_id: str
    input_units: int = 0
    output_units: int = 0


class PedagogyAiPort(Protocol):
    async def generate(self, request: GenerationRequest) -> GenerationResponse: ...


class PedagogyContentRepository(Protocol):
    async def save_summary(self, payload: dict) -> None: ...
    async def save_flashcards(self, payloads: Sequence[dict]) -> None: ...
    async def save_questions(self, payloads: Sequence[dict]) -> None: ...

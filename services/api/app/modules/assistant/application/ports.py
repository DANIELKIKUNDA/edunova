from __future__ import annotations

from typing import Protocol

from app.modules.assistant.domain.model import AssistantAnswer, ModelProfile, ProviderResult, SourceChunk


class KnowledgeRetriever(Protocol):
    def search(self, *, course_id: str, query: str, limit: int = 8) -> tuple[SourceChunk, ...]: ...


class LlmProvider(Protocol):
    name: str
    model: str
    def generate(self, *, system_prompt: str, user_prompt: str, max_output_tokens: int) -> ProviderResult: ...


class AssistantCache(Protocol):
    def get(self, key: str) -> AssistantAnswer | None: ...
    def set(self, key: str, answer: AssistantAnswer, ttl_seconds: int) -> None: ...


class CreditGate(Protocol):
    def reserve(self, *, account_id: str, credits: int): ...
    def commit(self, reservation_id: str) -> int: ...
    def release(self, reservation_id: str) -> int: ...


class GlobalAiBudgetGate(Protocol):
    def reserve(self, units: int) -> str: ...
    def commit(self, reservation_id: str) -> None: ...
    def release(self, reservation_id: str) -> None: ...


class ScientificSolver(Protocol):
    def solve(self, expression: str) -> str | None: ...


class ModelCatalog(Protocol):
    def list_profiles(self) -> tuple[ModelProfile, ...]: ...

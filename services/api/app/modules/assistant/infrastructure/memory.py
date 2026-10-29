from __future__ import annotations

from dataclasses import replace

from app.modules.assistant.domain.model import AssistantAnswer, ModelProfile, ProviderResult, SourceChunk
from app.modules.document_engine.application.search import search_chunks
from app.modules.document_engine.domain.model import DocumentChunk


class InMemoryKnowledgeRetriever:
    def __init__(self, chunks: tuple[SourceChunk, ...] = ()) -> None:
        self.chunks = list(chunks)

    def add(self, chunk: SourceChunk) -> None:
        self.chunks.append(chunk)

    def search(self, *, course_id: str, query: str, limit: int = 8) -> tuple[SourceChunk, ...]:
        scoped = [c for c in self.chunks if c.course_id == course_id]
        if not scoped:
            return ()
        doc_chunks = tuple(DocumentChunk(id=c.chunk_id, section_id=None, start_page=c.start_page, end_page=c.end_page, text=c.text, ordinal=i, token_estimate=max(1, len(c.text)//4)) for i, c in enumerate(scoped))
        hits = search_chunks(doc_chunks, query, limit=limit)
        by_id = {c.chunk_id: c for c in scoped}
        if not hits:
            return ()
        raw_max = max(h.score for h in hits) or 1.0
        out = []
        for hit in hits:
            base = by_id[hit.chunk_id]
            normalized = min(1.0, max(0.01, hit.score / raw_max))
            out.append(replace(base, score=normalized))
        return tuple(out)


class InMemoryAssistantCache:
    def __init__(self) -> None:
        self.items: dict[str, AssistantAnswer] = {}
    def get(self, key: str): return self.items.get(key)
    def set(self, key: str, answer: AssistantAnswer, ttl_seconds: int) -> None: self.items[key] = answer


class StaticModelCatalog:
    def __init__(self, profiles: tuple[ModelProfile, ...] | None = None) -> None:
        default = (
            ModelProfile(provider="sandbox-ai",model="flash",quality_tier=1,cost_units=1,max_context_tokens=8000,capabilities=frozenset({"chat"})),
            ModelProfile(provider="sandbox-ai",model="reasoning",quality_tier=2,cost_units=2,max_context_tokens=16000,capabilities=frozenset({"chat","reasoning","high_reliability"})),
        )
        self.profiles = default if profiles is None else profiles
    def list_profiles(self) -> tuple[ModelProfile, ...]: return self.profiles


class FakeLlmProvider:
    def __init__(self, name: str, model: str, *, fail: bool = False) -> None:
        self.name=name; self.model=model; self.fail=fail; self.calls=0
    def generate(self, *, system_prompt: str, user_prompt: str, max_output_tokens: int) -> ProviderResult:
        self.calls += 1
        if self.fail: raise RuntimeError("provider_failure")
        marker = "Question actuelle de l'étudiant:" if "Question actuelle de l'étudiant:" in user_prompt else "Question de l'étudiant:"
        question = user_prompt.split(marker,1)[-1].split("\n",1)[0].strip()
        return ProviderResult(text=f"Réponse pédagogique à : {question}",input_tokens=max(1,len(user_prompt)//4),output_tokens=24,provider_request_id=f"fake-{self.calls}")


class CommerceCreditGate:
    def __init__(self, commerce) -> None: self.commerce = commerce
    def reserve(self, *, account_id: str, credits: int): return self.commerce.reserve_ai_credits(account_id=account_id, credits=credits)
    def commit(self, reservation_id: str) -> int: return self.commerce.commit_ai_reservation(reservation_id)
    def release(self, reservation_id: str) -> int: return self.commerce.release_ai_reservation(reservation_id)

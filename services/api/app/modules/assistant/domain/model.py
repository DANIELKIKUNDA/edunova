from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256


class AssistantTask(StrEnum):
    EXPLAIN = "explain"
    SIMPLIFY = "simplify"
    COMPARE = "compare"
    QUIZ_COACH = "quiz_coach"
    CHECK_ANSWER = "check_answer"
    SOLVE_SCIENTIFIC = "solve_scientific"
    GENERAL_TUTOR = "general_tutor"


class PrivacyMode(StrEnum):
    SHARED_COURSE = "shared_course"
    PERSONAL_DOCUMENT = "personal_document"
    NO_DOCUMENT = "no_document"


@dataclass(frozen=True, slots=True)
class SourceChunk:
    chunk_id: str
    document_id: str
    course_id: str | None
    section_title: str | None
    start_page: int
    end_page: int
    text: str
    score: float
    source_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if self.start_page < 1 or self.end_page < self.start_page:
            raise ValueError("invalid_page_range")
        if not self.text.strip():
            raise ValueError("empty_source_chunk")


@dataclass(frozen=True, slots=True)
class Citation:
    chunk_id: str
    document_id: str
    section_title: str | None
    start_page: int
    end_page: int
    excerpt: str


@dataclass(frozen=True, slots=True)
class ModelProfile:
    provider: str
    model: str
    quality_tier: int
    cost_units: int
    max_context_tokens: int
    capabilities: frozenset[str] = frozenset()

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities


@dataclass(frozen=True, slots=True)
class ProviderResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    provider_request_id: str | None = None


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    role: str
    text: str

    def __post_init__(self) -> None:
        if self.role not in {"user", "assistant"}:
            raise ValueError("invalid_conversation_role")
        if not self.text.strip():
            raise ValueError("empty_conversation_turn")
        if len(self.text) > 2400:
            raise ValueError("conversation_turn_too_long")


@dataclass(frozen=True, slots=True)
class AssistantRequest:
    account_id: str
    question: str
    task: AssistantTask = AssistantTask.EXPLAIN
    privacy_mode: PrivacyMode = PrivacyMode.SHARED_COURSE
    course_id: str | None = None
    subject_domain: str = "general"
    local_context: tuple[SourceChunk, ...] = ()
    consent_to_remote_analysis: bool = False
    language: str = "fr"
    max_context_tokens: int = 6000
    allow_shared_cache: bool = True
    prompt_version: str = "lot6-v2.1"
    conversation_turns: tuple[ConversationTurn, ...] = ()
    explanation_depth: str = "standard"

    @property
    def requires_sources(self) -> bool:
        return self.privacy_mode in {PrivacyMode.SHARED_COURSE, PrivacyMode.PERSONAL_DOCUMENT} and self.task != AssistantTask.SOLVE_SCIENTIFIC

    def cache_key(self, source_fingerprints: tuple[str, ...]) -> str:
        normalized = " ".join(self.question.casefold().split())
        history = "|".join(f"{t.role}:{' '.join(t.text.casefold().split())}" for t in self.conversation_turns[-6:])
        raw = "|".join((self.prompt_version, self.language, self.explanation_depth, self.task.value, self.course_id or "", self.subject_domain, normalized, history, *sorted(source_fingerprints)))
        return sha256(raw.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class AssistantAnswer:
    text: str
    citations: tuple[Citation, ...]
    grounded: bool
    confidence: float
    abstained: bool
    provider: str | None = None
    model: str | None = None
    credits_charged: int = 0
    cache_hit: bool = False
    safety_flags: tuple[str, ...] = ()
    usage: dict[str, int] = field(default_factory=dict)
    route_reason: str | None = None
    grounding_coverage: float = 0.0
    source_count: int = 0
    prompt_version: str | None = None


@dataclass(frozen=True, slots=True)
class RouteDecision:
    profile: ModelProfile
    reason: str
    credits: int

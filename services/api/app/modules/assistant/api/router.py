from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.modules.assistant.domain.model import AssistantRequest, AssistantTask, PrivacyMode, SourceChunk, ConversationTurn
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
from app.shared.security.rate_limit import RateLimitExceeded

router = APIRouter()


class SourceChunkInput(BaseModel):
    chunk_id: str
    document_id: str
    section_title: str | None = None
    start_page: int = Field(ge=1)
    end_page: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=12000)
    source_fingerprint: str | None = None


class ConversationTurnInput(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    text: str = Field(min_length=1, max_length=2400)


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=6000)
    task: AssistantTask = AssistantTask.EXPLAIN
    privacy_mode: PrivacyMode = PrivacyMode.SHARED_COURSE
    course_id: str | None = None
    subject_domain: str = Field(default="general", max_length=80)
    local_context: list[SourceChunkInput] = Field(default_factory=list, max_length=8)
    consent_to_remote_analysis: bool = False
    language: str = Field(default="fr", max_length=12)
    max_context_tokens: int = Field(default=6000, ge=1000, le=16000)
    allow_shared_cache: bool = True
    conversation_turns: list[ConversationTurnInput] = Field(default_factory=list, max_length=6)
    explanation_depth: str = Field(default="standard", pattern="^(concise|standard|deep)$")


@router.get("/status")
def status(auth: AuthContext = Depends(current_auth)) -> dict:
    profiles = runtime.assistant_models.list_profiles()
    return {
        "configured": bool(profiles),
        "prompt_version": __import__("app.modules.assistant.application.prompts", fromlist=["PROMPT_VERSION"]).PROMPT_VERSION,
        "models": [
            {"provider": p.provider, "model": p.model, "quality_tier": p.quality_tier, "cost_units": p.cost_units, "capabilities": sorted(p.capabilities)}
            for p in profiles
        ],
        "privacy": {
            "shared_course_cache": True,
            "personal_document_cache": False,
            "personal_document_requires_explicit_consent": True,
            "personal_document_remote_enabled": runtime.assistant_personal_documents_allowed,
        },
    }


@router.post("/ask")
def ask(req: AskRequest, auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        runtime.rate_limiter.check(key=f"assistant:{auth.account_id}", limit=30, window_seconds=600)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="assistant_rate_limit") from exc

    total_context_chars = sum(len(c.text) for c in req.local_context)
    if total_context_chars > 40000:
        raise HTTPException(status_code=422, detail="local_context_too_large")
    chunks = tuple(SourceChunk(
        chunk_id=c.chunk_id,document_id=c.document_id,course_id=req.course_id,section_title=c.section_title,
        start_page=c.start_page,end_page=c.end_page,text=c.text,score=1.0,source_fingerprint=c.source_fingerprint,
    ) for c in req.local_context)
    request = AssistantRequest(
        account_id=auth.account_id, question=req.question, task=req.task, privacy_mode=req.privacy_mode,
        course_id=req.course_id, subject_domain=req.subject_domain, local_context=chunks,
        consent_to_remote_analysis=req.consent_to_remote_analysis, language=req.language,
        max_context_tokens=req.max_context_tokens, allow_shared_cache=req.allow_shared_cache,
        conversation_turns=tuple(ConversationTurn(role=t.role, text=t.text) for t in req.conversation_turns),
        explanation_depth=req.explanation_depth,
    )
    try:
        answer = runtime.assistant.answer(request)
    except ValueError as exc:
        code = str(exc)
        if code == "insufficient_ai_credits":
            raise HTTPException(status_code=402, detail=code) from exc
        if code in {"no_ai_provider_configured", "selected_ai_provider_unavailable", "no_compatible_ai_model", "ai_daily_budget_exhausted", "personal_document_ai_disabled"}:
            raise HTTPException(status_code=503, detail=code) from exc
        raise HTTPException(status_code=422, detail=code) from exc
    except Exception as exc:
        runtime.audit.write(actor_id=auth.account_id, action="assistant.provider.failure", entity_type="assistant", metadata={"error": type(exc).__name__})
        raise HTTPException(status_code=502, detail="assistant_provider_failure") from exc

    runtime.audit.write(
        actor_id=auth.account_id,
        action="assistant.answer",
        entity_type="assistant",
        metadata={"task": req.task.value, "privacy_mode": req.privacy_mode.value, "provider": answer.provider, "model": answer.model, "credits": answer.credits_charged, "cache_hit": answer.cache_hit, "abstained": answer.abstained, "input_tokens": int(answer.usage.get("input_tokens", 0)), "output_tokens": int(answer.usage.get("output_tokens", 0)), "route_reason": answer.route_reason, "grounding_coverage": answer.grounding_coverage, "source_count": answer.source_count, "prompt_version": answer.prompt_version},
    )
    return {
        "text": answer.text,
        "citations": [c.__dict__ if hasattr(c, "__dict__") else {"chunk_id":c.chunk_id,"document_id":c.document_id,"section_title":c.section_title,"start_page":c.start_page,"end_page":c.end_page,"excerpt":c.excerpt} for c in answer.citations],
        "grounded": answer.grounded,
        "confidence": answer.confidence,
        "abstained": answer.abstained,
        "provider": answer.provider,
        "model": answer.model,
        "credits_charged": answer.credits_charged,
        "cache_hit": answer.cache_hit,
        "safety_flags": list(answer.safety_flags),
        "usage": answer.usage,
        "route_reason": answer.route_reason,
        "grounding_coverage": answer.grounding_coverage,
        "source_count": answer.source_count,
        "prompt_version": answer.prompt_version,
    }

from __future__ import annotations

from app.modules.assistant.domain.model import AssistantRequest, AssistantTask, ModelProfile, RouteDecision


def rank_models(request: AssistantRequest, profiles: tuple[ModelProfile, ...]) -> tuple[RouteDecision, ...]:
    if not profiles:
        raise ValueError("no_ai_provider_configured")
    capability = "reasoning" if request.task in {AssistantTask.SOLVE_SCIENTIFIC, AssistantTask.CHECK_ANSWER, AssistantTask.COMPARE} else "chat"
    candidates = [p for p in profiles if p.supports(capability)]
    medical = request.subject_domain.casefold() in {"medicine", "medical", "médecine"}
    if medical:
        high_reliability = [p for p in candidates if p.supports("high_reliability")]
        if high_reliability:
            candidates = high_reliability
    if not candidates:
        raise ValueError("no_compatible_ai_model")
    min_quality = 2 if capability == "reasoning" or medical else 1
    eligible = [p for p in candidates if p.quality_tier >= min_quality] or candidates
    ordered = sorted(eligible, key=lambda p: (p.cost_units, -p.quality_tier, p.provider, p.model))
    return tuple(
        RouteDecision(
            profile=profile,
            reason=f"{capability};quality>={min_quality};cost-first;rank={index+1}",
            credits=max(1, profile.cost_units),
        )
        for index, profile in enumerate(ordered)
    )


def choose_model(request: AssistantRequest, profiles: tuple[ModelProfile, ...]) -> RouteDecision:
    return rank_models(request, profiles)[0]

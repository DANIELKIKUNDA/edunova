from __future__ import annotations

import re
from dataclasses import replace

from app.modules.assistant.application.context import (
    build_context,
    citations_for,
    detect_prompt_injection,
    evidence_confidence,
    evidence_conflicts,
    grounding_coverage,
    unsupported_numeric_claims,
)
from app.modules.assistant.application.prompts import PROMPT_VERSION, SYSTEM_PROMPT, max_output_tokens, user_prompt
from app.modules.assistant.application.routing import rank_models
from app.modules.assistant.application.ports import AssistantCache, CreditGate, GlobalAiBudgetGate, KnowledgeRetriever, LlmProvider, ModelCatalog, ScientificSolver
from app.modules.assistant.domain.model import AssistantAnswer, AssistantRequest, AssistantTask, PrivacyMode, SourceChunk


class AssistantService:
    def __init__(
        self,
        *,
        retriever: KnowledgeRetriever,
        providers: dict[tuple[str, str], LlmProvider],
        models: ModelCatalog,
        cache: AssistantCache,
        credits: CreditGate,
        scientific_solver: ScientificSolver,
        global_budget: GlobalAiBudgetGate | None = None,
        allow_personal_remote: bool = True,
    ) -> None:
        self.retriever = retriever
        self.providers = providers
        self.models = models
        self.cache = cache
        self.credits = credits
        self.scientific_solver = scientific_solver
        self.global_budget = global_budget
        self.allow_personal_remote = allow_personal_remote

    def answer(self, request: AssistantRequest) -> AssistantAnswer:
        question = request.question.strip()
        if len(question) < 2:
            raise ValueError("question_too_short")
        if len(question) > 6000:
            raise ValueError("question_too_long")

        # Force the deployed prompt contract into cache/audit identity.
        request = replace(request, prompt_version=PROMPT_VERSION)

        # Deterministic math first: no model, no AI credit.
        if request.task == AssistantTask.SOLVE_SCIENTIFIC:
            solved = self.scientific_solver.solve(question)
            if solved:
                return AssistantAnswer(
                    text=solved,
                    citations=(),
                    grounded=True,
                    confidence=0.99,
                    abstained=False,
                    provider="sympy",
                    model="deterministic",
                    credits_charged=0,
                    route_reason="deterministic_scientific_solver",
                    grounding_coverage=1.0,
                    source_count=0,
                    prompt_version=PROMPT_VERSION,
                )

        medical_domain = request.subject_domain.casefold() in {"medicine", "medical", "médecine"}
        if medical_domain and self._looks_like_personal_medical_advice(question):
            return AssistantAnswer(
                text="EduNova peut expliquer le contenu médical à des fins d’étude, mais ne fournit pas de diagnostic ni de traitement personnel. Reformule la question comme une notion de cours ou, pour un problème de santé réel, consulte un professionnel de santé.",
                citations=(), grounded=False, confidence=0.0, abstained=True, credits_charged=0,
                route_reason="personal_medical_advice_boundary", prompt_version=PROMPT_VERSION,
            )
        if medical_domain and request.privacy_mode == PrivacyMode.NO_DOCUMENT:
            return AssistantAnswer(
                text="Pour une question médicale, EduNova exige une source de cours ou un document explicite avant de produire une explication pédagogique.",
                citations=(), grounded=False, confidence=0.0, abstained=True, credits_charged=0,
                route_reason="medical_source_required", prompt_version=PROMPT_VERSION,
            )

        chunks = self._resolve_context(request)
        safety_flags = tuple((*detect_prompt_injection(chunks), *evidence_conflicts(chunks)))
        context, selected = build_context(chunks, max_tokens=request.max_context_tokens, query=question)
        confidence = evidence_confidence(selected)

        if request.requires_sources and not selected:
            return AssistantAnswer(
                text="Je n’ai pas assez d’éléments dans le cours sélectionné pour répondre de façon fiable. Ajoute le document concerné ou précise le chapitre.",
                citations=(), grounded=False, confidence=0.0, abstained=True,
                safety_flags=safety_flags, credits_charged=0, route_reason="abstain_no_evidence",
                grounding_coverage=0.0, source_count=0, prompt_version=PROMPT_VERSION,
            )
        if request.requires_sources and confidence < 0.08:
            return AssistantAnswer(
                text="Les passages retrouvés sont trop faibles pour produire une réponse fiable. Je préfère ne pas inventer.",
                citations=citations_for(selected), grounded=False, confidence=confidence, abstained=True,
                safety_flags=safety_flags, credits_charged=0, route_reason="abstain_low_evidence",
                grounding_coverage=0.0, source_count=len(selected), prompt_version=PROMPT_VERSION,
            )

        source_fingerprints = tuple(c.source_fingerprint or c.document_id for c in selected)
        cache_allowed = request.allow_shared_cache and request.privacy_mode == PrivacyMode.SHARED_COURSE
        cache_key = request.cache_key(source_fingerprints)
        if cache_allowed:
            cached = self.cache.get(cache_key)
            if cached:
                return replace(cached, cache_hit=True, credits_charged=0)

        decisions = rank_models(request, self.models.list_profiles())
        output_budget = max_output_tokens(request)
        last_error: Exception | None = None
        successful = None
        rejected_grounding = None

        for attempt_index, decision in enumerate(decisions, start=1):
            provider = self.providers.get((decision.profile.provider, decision.profile.model))
            if provider is None:
                last_error = ValueError("selected_ai_provider_unavailable")
                continue

            effective_context_tokens = min(
                request.max_context_tokens,
                max(1000, decision.profile.max_context_tokens - output_budget - 800),
            )
            attempt_context, attempt_selected = build_context(chunks, max_tokens=effective_context_tokens, query=question)
            attempt_confidence = evidence_confidence(attempt_selected)
            attempt_safety_flags = safety_flags

            budget_reservation = None
            if self.global_budget is not None:
                budget_reservation = self.global_budget.reserve(decision.credits)
            try:
                reservation = self.credits.reserve(account_id=request.account_id, credits=decision.credits)
            except Exception:
                if budget_reservation is not None:
                    self.global_budget.release(budget_reservation)
                raise

            try:
                result = provider.generate(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt(request, attempt_context),
                    max_output_tokens=output_budget,
                )
                answer_text = result.text.strip()
                if not answer_text:
                    raise RuntimeError("empty_ai_response")

                numeric_flags = unsupported_numeric_claims(answer_text, question, attempt_selected) if request.requires_sources else ()
                coverage = grounding_coverage(answer_text, question, attempt_selected) if request.requires_sources else 1.0
                if numeric_flags:
                    attempt_safety_flags = tuple((*attempt_safety_flags, "unsupported_numeric_claim:" + ",".join(numeric_flags)))
                    attempt_confidence = min(attempt_confidence, 0.55)
                if request.requires_sources and coverage < 0.22:
                    attempt_safety_flags = tuple((*attempt_safety_flags, f"low_grounding_coverage:{coverage:.3f}"))
                    attempt_confidence = min(attempt_confidence, max(0.15, coverage))

                # Premium behavior: reject a badly grounded answer and refund the
                # student's credits. Vendor spend is still counted globally because
                # the external call actually happened.
                if request.requires_sources and coverage < 0.10:
                    self.credits.release(reservation.id)
                    if budget_reservation is not None:
                        # Vendor spend happened even though the user is not charged.
                        self.global_budget.commit(budget_reservation)
                    rejected_grounding = (
                        decision, result, attempt_selected, attempt_confidence,
                        attempt_safety_flags, attempt_index, coverage,
                    )
                    last_error = RuntimeError("low_grounding_response")
                    continue

                self.credits.commit(reservation.id)
                if budget_reservation is not None:
                    self.global_budget.commit(budget_reservation)
                successful = (
                    decision,
                    result,
                    answer_text,
                    attempt_selected,
                    attempt_confidence,
                    attempt_safety_flags,
                    attempt_index,
                    coverage,
                )
                break
            except Exception as exc:
                last_error = exc
                try:
                    self.credits.release(reservation.id)
                finally:
                    if budget_reservation is not None:
                        self.global_budget.release(budget_reservation)
                continue

        if successful is None:
            if rejected_grounding is not None:
                decision, result, selected, confidence, safety_flags, attempt_index, coverage = rejected_grounding
                return AssistantAnswer(
                    text="La réponse générée n’est pas suffisamment soutenue par les passages du cours. EduNova préfère l’écarter plutôt que te présenter une explication potentiellement inventée. Aucun crédit IA n’a été consommé.",
                    citations=citations_for(selected), grounded=False, confidence=confidence, abstained=True,
                    provider=decision.profile.provider, model=decision.profile.model, credits_charged=0, cache_hit=False,
                    safety_flags=safety_flags, usage={"input_tokens": result.input_tokens, "output_tokens": result.output_tokens},
                    route_reason=f"post_generation_grounding_reject;attempt={attempt_index}", grounding_coverage=coverage,
                    source_count=len(selected), prompt_version=PROMPT_VERSION,
                )
            if isinstance(last_error, ValueError) and str(last_error) == "selected_ai_provider_unavailable":
                raise last_error
            if last_error is not None:
                raise last_error
            raise ValueError("selected_ai_provider_unavailable")

        decision, result, answer_text, selected, confidence, safety_flags, attempt_index, coverage = successful

        answer = AssistantAnswer(
            text=answer_text,
            citations=citations_for(selected),
            grounded=bool(selected) or request.privacy_mode == PrivacyMode.NO_DOCUMENT,
            confidence=max(confidence, 0.55 if request.privacy_mode == PrivacyMode.NO_DOCUMENT else confidence),
            abstained=False,
            provider=decision.profile.provider,
            model=decision.profile.model,
            credits_charged=decision.credits,
            cache_hit=False,
            safety_flags=safety_flags,
            usage={"input_tokens": result.input_tokens, "output_tokens": result.output_tokens},
            route_reason=f"{decision.reason};attempt={attempt_index}",
            grounding_coverage=coverage,
            source_count=len(selected),
            prompt_version=PROMPT_VERSION,
        )
        if cache_allowed:
            self.cache.set(cache_key, answer, ttl_seconds=86400 * 7)
        return answer

    @staticmethod
    def _looks_like_personal_medical_advice(question: str) -> bool:
        q = " ".join(question.casefold().split())
        patterns = (
            "mes symptômes", "mon symptôme", "je souffre", "j'ai mal", "jai mal",
            "quel médicament dois-je", "quel medicament dois-je", "que dois-je prendre",
            "diagnostique-moi", "quel traitement pour moi", "est-ce que j'ai", "est ce que j'ai",
        )
        return any(p in q for p in patterns)

    @staticmethod
    def _retrieval_queries(question: str, task: AssistantTask) -> tuple[str, ...]:
        """Small deterministic multi-query expansion without an extra paid model call."""
        normalized = " ".join(question.split()).strip()
        queries = [normalized]
        if task == AssistantTask.COMPARE:
            parts = re.split(r"\b(?:versus|vs\.?|et|avec|contre|différence entre|difference entre)\b", normalized, flags=re.I)
            for part in parts:
                part = part.strip(" ?,:;-")
                if len(part) >= 4 and part.casefold() != normalized.casefold():
                    queries.append(part)
        quoted = re.findall(r'["“”«»]([^"“”«»]{4,120})["“”«»]', normalized)
        queries.extend(quoted[:2])
        # Preserve order and bound retrieval fan-out.
        out = []
        for q in queries:
            if q and q.casefold() not in {x.casefold() for x in out}:
                out.append(q)
        return tuple(out[:3])

    def _resolve_context(self, request: AssistantRequest) -> tuple[SourceChunk, ...]:
        if request.privacy_mode == PrivacyMode.PERSONAL_DOCUMENT:
            if not self.allow_personal_remote:
                raise ValueError("personal_document_ai_disabled")
            if not request.consent_to_remote_analysis:
                raise ValueError("remote_analysis_consent_required")
            # Context is supplied ephemerally by the client and is never persisted by this service.
            return tuple(request.local_context[:8])
        if request.privacy_mode == PrivacyMode.SHARED_COURSE:
            if not request.course_id:
                raise ValueError("course_id_required")
            merged: dict[str, SourceChunk] = {}
            for query in self._retrieval_queries(request.question, request.task):
                for chunk in self.retriever.search(course_id=request.course_id, query=query, limit=8):
                    current = merged.get(chunk.chunk_id)
                    if current is None or chunk.score > current.score:
                        merged[chunk.chunk_id] = chunk
            return tuple(sorted(merged.values(), key=lambda c: (-c.score, c.chunk_id))[:16])
        return ()

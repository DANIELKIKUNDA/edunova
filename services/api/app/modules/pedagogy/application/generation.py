from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from uuid import uuid4

from app.modules.pedagogy.application.context import ContextBuilder
from app.modules.pedagogy.application.ports import GenerationRequest, PedagogyAiPort
from app.modules.pedagogy.application.quality import PedagogyQualityGate
from app.modules.pedagogy.domain.advanced import QuestionQualityValidator
from app.modules.pedagogy.domain.model import (
    ContentStatus,
    Flashcard,
    GeneratedContentMeta,
    QuestionKind,
    QuestionOption,
    QuizQuestion,
    Summary,
    SummaryKind,
)
from app.modules.document_engine.domain.model import DocumentChunk
from app.shared.domain.errors import ValidationError


class PedagogyGenerator:
    """Application service. AI is a replaceable adapter, provenance is mandatory."""

    def __init__(self, ai: PedagogyAiPort, *, context_builder: ContextBuilder | None = None) -> None:
        self.ai = ai
        self.context_builder = context_builder or ContextBuilder()
        self.quality_gate = PedagogyQualityGate()
        self.question_quality = QuestionQualityValidator()

    @staticmethod
    def _identity(task: str, prompt_version: str, refs) -> tuple[str, str]:
        source_material = "|".join(
            f"{ref.document_id}:{ref.chunk_id}:{ref.start_page}:{ref.end_page}:{ref.excerpt}" for ref in refs
        )
        source_fingerprint = hashlib.sha256(source_material.encode("utf-8")).hexdigest()
        generation_key = hashlib.sha256(f"{task}|{prompt_version}|{source_fingerprint}".encode("utf-8")).hexdigest()
        return source_fingerprint, generation_key

    @staticmethod
    def _select_refs(all_refs, raw_indexes):
        if raw_indexes is None:
            if len(all_refs) == 1:
                return all_refs
            raise ValidationError("generated item must explicitly identify its source_indexes")
        try:
            indexes = tuple(dict.fromkeys(int(value) for value in raw_indexes))
        except (TypeError, ValueError) as exc:
            raise ValidationError("source_indexes must be integer indexes") from exc
        if not indexes:
            raise ValidationError("generated item must keep at least one source index")
        if any(index < 0 or index >= len(all_refs) for index in indexes):
            raise ValidationError("generated source index is outside the provided context")
        return tuple(all_refs[index] for index in indexes)

    async def generate_summary(
        self,
        *,
        document_id: str,
        course_id: str,
        section_id: str | None,
        title: str,
        kind: SummaryKind,
        chunks: list[DocumentChunk],
        is_medical: bool = False,
    ) -> Summary:
        context = self.context_builder.build(document_id=document_id, chunks=chunks)
        instruction = {
            SummaryKind.EXPRESS: "Résume en lecture de 3 à 5 minutes, sans perdre les idées structurantes.",
            SummaryKind.COMPLETE: "Produis un résumé approfondi, structuré, fidèle au document et sans ajouter de faits externes.",
            SummaryKind.KEY_POINTS: "Extrais définitions, mécanismes, formules, étapes, pièges et points essentiels à retenir.",
        }[kind]
        response = await self.ai.generate(
            GenerationRequest(
                task=f"summary:{kind.value}",
                instruction=f"{instruction}\n\n{context.text}",
                source_refs=context.source_refs,
                response_schema="{title:string, body_markdown:string, estimated_minutes:int, cited_claim_count:int, factual_claim_count:int, source_indexes:[int]}",
            )
        )
        body = str(response.payload.get("body_markdown", "")).strip()
        if not body:
            raise ValidationError("AI summary payload missing body_markdown")
        quality = self.quality_gate.assess(
            source_count=len(context.source_refs),
            body=body,
            factual_claim_count=int(response.payload.get("factual_claim_count", 0)),
            cited_claim_count=int(response.payload.get("cited_claim_count", 0)),
            is_medical=is_medical,
        )
        summary_refs = self._select_refs(context.source_refs, response.payload.get("source_indexes"))
        prompt_version = "pedagogy.summary.v2"
        source_fingerprint, generation_key = self._identity(f"summary:{kind.value}", prompt_version, summary_refs)
        meta = GeneratedContentMeta(
            source_refs=summary_refs, model_id=f"{response.provider}:{response.model_id}", prompt_version=prompt_version,
            created_at=datetime.now(timezone.utc), status=quality.status, source_fingerprint=source_fingerprint, generation_key=generation_key,
        )
        return Summary(
            id=str(uuid4()),
            course_id=course_id,
            section_id=section_id,
            kind=kind,
            title=str(response.payload.get("title") or title).strip(),
            body_markdown=body,
            estimated_minutes=max(1, int(response.payload.get("estimated_minutes", 5))),
            meta=meta,
        )

    async def generate_flashcards(
        self,
        *,
        document_id: str,
        course_id: str,
        section_id: str | None,
        chunks: list[DocumentChunk],
        count: int = 12,
    ) -> tuple[Flashcard, ...]:
        if not 3 <= count <= 50:
            raise ValidationError("flashcard count must be between 3 and 50")
        context = self.context_builder.build(document_id=document_id, chunks=chunks)
        response = await self.ai.generate(
            GenerationRequest(
                task="flashcards",
                instruction=(
                    f"Crée {count} flashcards atomiques. Une carte = une notion vérifiable. "
                    "Évite les questions vagues et n'ajoute aucun savoir externe.\n\n" + context.text
                ),
                source_refs=context.source_refs,
                response_schema="{cards:[{front:string, back:string, difficulty:int, source_indexes:[int]}]}"
            )
        )
        cards = response.payload.get("cards") or []
        if not isinstance(cards, list) or len(cards) < count:
            raise ValidationError("AI flashcard payload returned fewer cards than requested")
        result: list[Flashcard] = []
        normalized_fronts: set[str] = set()
        for card in cards[:count]:
            front = str(card.get("front", "")).strip()
            back = str(card.get("back", "")).strip()
            normalized = self.question_quality.normalize(front)
            if not normalized or normalized in normalized_fronts:
                raise ValidationError("generated flashcards must be non-empty and non-duplicate")
            normalized_fronts.add(normalized)
            refs = self._select_refs(context.source_refs, card.get("source_indexes"))
            prompt_version = "pedagogy.flashcards.v2"
            source_fingerprint, generation_key = self._identity("flashcards", prompt_version, refs)
            meta = GeneratedContentMeta(
                source_refs=refs, model_id=f"{response.provider}:{response.model_id}", prompt_version=prompt_version,
                created_at=datetime.now(timezone.utc), status=ContentStatus.REVIEW_REQUIRED,
                source_fingerprint=source_fingerprint, generation_key=generation_key,
            )
            result.append(Flashcard(
                id=str(uuid4()), course_id=course_id, section_id=section_id,
                front=front, back=back, difficulty=int(card.get("difficulty", 3)), meta=meta,
            ))
        return tuple(result)

    async def generate_quiz(
        self,
        *,
        document_id: str,
        course_id: str,
        section_id: str | None,
        chunks: list[DocumentChunk],
        count: int = 10,
    ) -> tuple[QuizQuestion, ...]:
        if not 3 <= count <= 50:
            raise ValidationError("quiz count must be between 3 and 50")
        context = self.context_builder.build(document_id=document_id, chunks=chunks)
        response = await self.ai.generate(
            GenerationRequest(
                task="quiz",
                instruction=(
                    f"Crée {count} QCM à choix unique. Chaque question doit avoir 4 options, "
                    "une seule correcte et une explication pédagogique fondée exclusivement sur les sources.\n\n"
                    + context.text
                ),
                source_refs=context.source_refs,
                response_schema="{questions:[{prompt:string, options:[string,string,string,string], correct_index:int, explanation:string, difficulty:int, source_indexes:[int]}]}"
            )
        )
        payloads = response.payload.get("questions") or []
        if not isinstance(payloads, list) or len(payloads) < count:
            raise ValidationError("AI quiz payload returned fewer questions than requested")
        questions: list[QuizQuestion] = []
        for raw in payloads[:count]:
            options_raw = list(raw.get("options") or [])
            if len(options_raw) != 4:
                raise ValidationError("generated single-choice question must have exactly 4 options")
            options = tuple(QuestionOption(id=chr(65 + idx), text=str(value).strip()) for idx, value in enumerate(options_raw))
            correct_index = int(raw.get("correct_index", -1))
            if correct_index not in range(4):
                raise ValidationError("generated correct_index must be between 0 and 3")
            refs = self._select_refs(context.source_refs, raw.get("source_indexes"))
            prompt_version = "pedagogy.quiz.v2"
            source_fingerprint, generation_key = self._identity("quiz", prompt_version, refs)
            meta = GeneratedContentMeta(
                source_refs=refs, model_id=f"{response.provider}:{response.model_id}", prompt_version=prompt_version,
                created_at=datetime.now(timezone.utc), status=ContentStatus.REVIEW_REQUIRED,
                source_fingerprint=source_fingerprint, generation_key=generation_key,
            )
            question = QuizQuestion(
                id=str(uuid4()), course_id=course_id, section_id=section_id,
                kind=QuestionKind.SINGLE_CHOICE, prompt=str(raw.get("prompt", "")).strip(),
                options=options, correct_option_ids=(chr(65 + correct_index),),
                explanation=str(raw.get("explanation", "")).strip(),
                difficulty=int(raw.get("difficulty", 3)), meta=meta,
            )
            quality = self.question_quality.validate(question)
            if not quality.valid:
                raise ValidationError("generated question failed quality gate: " + ",".join(quality.warnings))
            questions.append(question)
        duplicates = self.question_quality.find_duplicates(questions)
        if duplicates:
            raise ValidationError("generated quiz contains duplicate prompts")
        return tuple(questions)

    async def generate_mixed_quiz(
        self,
        *,
        document_id: str,
        course_id: str,
        section_id: str | None,
        chunks: list[DocumentChunk],
        count: int = 10,
        allowed_kinds: tuple[QuestionKind, ...] = (
            QuestionKind.SINGLE_CHOICE,
            QuestionKind.MULTIPLE_CHOICE,
            QuestionKind.TRUE_FALSE,
            QuestionKind.NUMERIC,
            QuestionKind.FREE_TEXT,
        ),
    ) -> tuple[QuizQuestion, ...]:
        """Generate a pedagogically mixed quiz while keeping every item source-bound.

        The AI only proposes structured items. Deterministic validation decides whether
        an item may enter the local repository.
        """
        if not 3 <= count <= 50:
            raise ValidationError("quiz count must be between 3 and 50")
        if not allowed_kinds:
            raise ValidationError("at least one question kind must be allowed")
        context = self.context_builder.build(document_id=document_id, chunks=chunks)
        allowed = ",".join(kind.value for kind in allowed_kinds)
        response = await self.ai.generate(
            GenerationRequest(
                task="mixed_quiz",
                instruction=(
                    f"Crée {count} questions variées parmi [{allowed}]. "
                    "Chaque item doit être autonome, non ambigu, avec explication et sources explicites. "
                    "Pour les choix, évite les distracteurs manifestement absurdes. "
                    "Pour le numérique, fournis une tolérance. Pour le texte libre, fournis des variantes acceptées.\n\n"
                    + context.text
                ),
                source_refs=context.source_refs,
                response_schema=(
                    "{questions:[{kind:string,prompt:string,options:[string],correct_indexes:[int],"
                    "expected_numeric:number|null,numeric_tolerance:number,relative_tolerance:number,"
                    "expected_text:string|null,accepted_text_answers:[string],explanation:string,"
                    "difficulty:int,source_indexes:[int],learning_objective_id:string|null,tags:[string]}]}"
                ),
            )
        )
        payloads = response.payload.get("questions") or []
        if not isinstance(payloads, list) or len(payloads) < count:
            raise ValidationError("AI mixed quiz payload returned fewer questions than requested")

        questions: list[QuizQuestion] = []
        for raw in payloads[:count]:
            kind = QuestionKind(str(raw.get("kind", "")))
            if kind not in allowed_kinds:
                raise ValidationError("AI returned a question kind outside allowed_kinds")
            refs = self._select_refs(context.source_refs, raw.get("source_indexes"))
            options_raw = list(raw.get("options") or [])
            options = tuple(QuestionOption(id=chr(65 + idx), text=str(value).strip()) for idx, value in enumerate(options_raw))
            correct_indexes = tuple(int(value) for value in (raw.get("correct_indexes") or []))
            if any(index < 0 or index >= len(options) for index in correct_indexes):
                raise ValidationError("generated correct index outside options")
            correct_ids = tuple(chr(65 + index) for index in correct_indexes)
            expected_text = raw.get("expected_text")
            accepted_text = tuple(str(value).strip() for value in (raw.get("accepted_text_answers") or []) if str(value).strip())
            expected_numeric = raw.get("expected_numeric")
            prompt_version = "pedagogy.mixed_quiz.v1"
            source_fingerprint, generation_key = self._identity("mixed_quiz", prompt_version, refs)
            meta = GeneratedContentMeta(
                source_refs=refs, model_id=f"{response.provider}:{response.model_id}", prompt_version=prompt_version,
                created_at=datetime.now(timezone.utc), status=ContentStatus.REVIEW_REQUIRED,
                source_fingerprint=source_fingerprint, generation_key=generation_key,
            )
            question = QuizQuestion(
                id=str(uuid4()),
                course_id=course_id,
                section_id=section_id,
                kind=kind,
                prompt=str(raw.get("prompt", "")).strip(),
                options=options,
                correct_option_ids=correct_ids,
                expected_numeric=None if expected_numeric is None else float(expected_numeric),
                expected_text=None if expected_text is None else str(expected_text).strip(),
                numeric_tolerance=float(raw.get("numeric_tolerance", 0) or 0),
                numeric_relative_tolerance=float(raw.get("relative_tolerance", 0) or 0),
                accepted_text_answers=accepted_text,
                explanation=str(raw.get("explanation", "")).strip(),
                difficulty=int(raw.get("difficulty", 3)),
                learning_objective_id=(str(raw.get("learning_objective_id")).strip() if raw.get("learning_objective_id") else None),
                tags=tuple(str(value).strip() for value in (raw.get("tags") or []) if str(value).strip()),
                meta=meta,
            )
            report = self.question_quality.validate(question)
            if not report.valid:
                raise ValidationError("generated question failed quality gate: " + ",".join(report.warnings))
            questions.append(question)

        duplicates = self.question_quality.find_duplicates(questions)
        if duplicates:
            raise ValidationError("generated mixed quiz contains duplicate prompts")
        return tuple(questions)

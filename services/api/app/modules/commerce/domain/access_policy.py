from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessPolicy:
    # Local personal files are intentionally not capped: they cost EduNova no server storage.
    free_local_personal_documents: int | None = None
    free_quiz_questions_per_day: int = 10
    free_flashcard_reviews_per_day: int = 20
    free_ai_trial_credits: int = 3
    premium_ai_credits_per_cycle: int = 25
    free_features: tuple[str, ...] = (
        "local_document_library",
        "pdf_reader",
        "personal_calendar",
        "local_notifications",
        "basic_progress",
        "summary_preview",
    )
    premium_features: tuple[str, ...] = (
        "full_summaries",
        "audio_summaries",
        "unlimited_prepared_quizzes",
        "unlimited_flashcards",
        "detailed_solutions",
        "advanced_readiness",
        "adaptive_planning",
        "emergency_revision",
        "premium_offline_content",
        "advanced_analytics",
        "ai_assistant_quota",
    )

    def as_dict(self) -> dict:
        return {
            "free_local_personal_documents": self.free_local_personal_documents,
            "free_quiz_questions_per_day": self.free_quiz_questions_per_day,
            "free_flashcard_reviews_per_day": self.free_flashcard_reviews_per_day,
            "free_ai_trial_credits": self.free_ai_trial_credits,
            "premium_ai_credits_per_cycle": self.premium_ai_credits_per_cycle,
            "free_features": list(self.free_features),
            "premium_features": list(self.premium_features),
        }

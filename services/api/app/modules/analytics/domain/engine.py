from __future__ import annotations

from statistics import mean

from .model import (
    AnalyticsEvidence,
    AnalyticsReport,
    AnalyticsSnapshot,
    CourseAnalyticsSignal,
    CourseInsight,
    RecommendationKind,
    StudyRecommendation,
    TrendDirection,
    TrendMetric,
)


def _trend(current: float, previous: float, *, epsilon: float) -> TrendMetric:
    delta = current - previous
    if delta > epsilon:
        direction = TrendDirection.IMPROVING
    elif delta < -epsilon:
        direction = TrendDirection.DECLINING
    else:
        direction = TrendDirection.STABLE
    return TrendMetric(current=current, previous=previous, delta=delta, direction=direction)


def _readiness(course: CourseAnalyticsSignal) -> int | None:
    weighted = []
    if course.coverage is not None:
        weighted.append((course.coverage, .30))
    if course.quiz_mastery is not None:
        weighted.append((course.quiz_mastery, .40))
    if course.flashcard_mastery is not None:
        weighted.append((course.flashcard_mastery, .15))
    if course.weakness_recovery is not None:
        weighted.append((course.weakness_recovery, .15))
    if not weighted:
        return None
    total = sum(weight for _, weight in weighted)
    return round(sum(value * weight for value, weight in weighted) / total * 100)


def _course_direction(course: CourseAnalyticsSignal) -> TrendDirection:
    delta = course.mastery_delta_7d
    if delta is None or abs(delta) < .03:
        return TrendDirection.STABLE
    return TrendDirection.IMPROVING if delta > 0 else TrendDirection.DECLINING


def _risk_level(course: CourseAnalyticsSignal, readiness: int | None) -> tuple[str, str]:
    urgent = course.days_to_next_assessment is not None and course.days_to_next_assessment <= 3
    if urgent and (course.next_assessment_readiness or readiness or 0) < 60:
        return "high", "Évaluation proche avec préparation encore insuffisante."
    if course.open_errors >= 8 or (readiness is not None and readiness < 45):
        return "high", "Plusieurs difficultés restent ouvertes dans ce cours."
    if course.overdue_flashcards >= 12 or (readiness is not None and readiness < 70):
        return "medium", "Une révision ciblée peut consolider ce cours."
    return "low", "Progression régulière ; maintenir le rythme."


def _recommendations(snapshot: AnalyticsSnapshot) -> tuple[StudyRecommendation, ...]:
    candidates: list[StudyRecommendation] = []
    for course in snapshot.courses:
        readiness = course.next_assessment_readiness
        if readiness is None:
            readiness = _readiness(course)

        if course.days_to_next_assessment is not None and course.days_to_next_assessment <= 7:
            gap = max(0, 80 - (readiness or 0))
            urgency = max(0, 8 - course.days_to_next_assessment) * 8
            score = min(100, 45 + urgency + gap // 2)
            minutes = 45 if course.days_to_next_assessment <= 2 else 30
            candidates.append(StudyRecommendation(
                id=f"assessment:{course.course_id}", kind=RecommendationKind.ASSESSMENT_FOCUS,
                course_id=course.course_id, course_title=course.title,
                title=f"Préparer {course.title}",
                reason=f"Évaluation dans {course.days_to_next_assessment} jour(s) ; préparation estimée à {readiness if readiness is not None else '—'} %.",
                recommended_minutes=minutes, priority_score=score,
                deep_link=f"/revision?course={course.course_id}",
            ))

        if course.open_errors > 0:
            score = min(96, 45 + course.open_errors * 4 + (15 if course.days_to_next_assessment is not None and course.days_to_next_assessment <= 5 else 0))
            candidates.append(StudyRecommendation(
                id=f"errors:{course.course_id}", kind=RecommendationKind.RECOVER_ERRORS,
                course_id=course.course_id, course_title=course.title,
                title=f"Revoir tes erreurs en {course.title}",
                reason=f"{course.open_errors} erreur(s) restent à récupérer.",
                recommended_minutes=min(30, max(10, course.open_errors * 3)), priority_score=score,
                deep_link=f"/pedagogy?course={course.course_id}&tab=errors",
            ))

        if course.overdue_flashcards >= 5:
            score = min(88, 35 + course.overdue_flashcards * 3)
            candidates.append(StudyRecommendation(
                id=f"flashcards:{course.course_id}", kind=RecommendationKind.FLASHCARD_REVIEW,
                course_id=course.course_id, course_title=course.title,
                title=f"Rattraper les flashcards de {course.title}",
                reason=f"{course.overdue_flashcards} carte(s) sont arrivées à échéance.",
                recommended_minutes=min(25, max(8, course.overdue_flashcards)), priority_score=score,
                deep_link=f"/pedagogy?course={course.course_id}&tab=flashcards",
            ))

        if course.quiz_mastery is not None and course.quiz_mastery < .65:
            score = min(84, 40 + round((.65 - course.quiz_mastery) * 80))
            candidates.append(StudyRecommendation(
                id=f"quiz:{course.course_id}", kind=RecommendationKind.QUIZ_DRILL,
                course_id=course.course_id, course_title=course.title,
                title=f"Faire un quiz ciblé en {course.title}",
                reason=f"Maîtrise quiz actuelle : {round(course.quiz_mastery * 100)} %.",
                recommended_minutes=15, priority_score=score,
                deep_link=f"/pedagogy?course={course.course_id}&tab=quiz",
            ))

        if (course.coverage or 0) < .55 and course.study_minutes_7d < 30:
            candidates.append(StudyRecommendation(
                id=f"continue:{course.course_id}", kind=RecommendationKind.CONTINUE_COURSE,
                course_id=course.course_id, course_title=course.title,
                title=f"Continuer {course.title}",
                reason="Le cours reste peu couvert cette semaine.",
                recommended_minutes=20, priority_score=45,
                deep_link=f"/courses/{course.course_id}",
            ))

    if snapshot.plan_adherence_7d is not None and snapshot.plan_adherence_7d < .50:
        candidates.append(StudyRecommendation(
            id="plan:recovery", kind=RecommendationKind.PLAN_RECOVERY,
            course_id=None, course_title=None,
            title="Alléger ton plan de révision",
            reason=f"Tu as réalisé {round(snapshot.plan_adherence_7d * 100)} % du planning récent. Un plan plus réaliste sera plus durable.",
            recommended_minutes=5, priority_score=80,
            deep_link="/revision/preferences",
        ))

    candidates.sort(key=lambda r: (-r.priority_score, r.recommended_minutes, r.id))
    # Diversify: at most two recommendations per course in the top five.
    selected: list[StudyRecommendation] = []
    per_course: dict[str, int] = {}
    for item in candidates:
        key = item.course_id or "__global__"
        if per_course.get(key, 0) >= 2:
            continue
        selected.append(item)
        per_course[key] = per_course.get(key, 0) + 1
        if len(selected) == 5:
            break
    return tuple(selected)


class AnalyticsEngine:
    """Deterministic, explainable analytics. Never predicts grades or exam outcomes."""

    def build(self, snapshot: AnalyticsSnapshot) -> AnalyticsReport:
        study_time = _trend(float(snapshot.study_minutes_7d), float(snapshot.study_minutes_prev_7d), epsilon=20)
        quiz = None
        if snapshot.quiz_accuracy_7d is not None and snapshot.quiz_accuracy_prev_7d is not None:
            quiz = _trend(snapshot.quiz_accuracy_7d, snapshot.quiz_accuracy_prev_7d, epsilon=.04)

        directions = [study_time.direction]
        if quiz is not None:
            directions.append(quiz.direction)
        course_deltas = [c.mastery_delta_7d for c in snapshot.courses if c.mastery_delta_7d is not None]
        if course_deltas:
            avg = mean(course_deltas)
            directions.append(TrendDirection.IMPROVING if avg > .03 else TrendDirection.DECLINING if avg < -.03 else TrendDirection.STABLE)

        evidence = AnalyticsEvidence.STRONG if snapshot.active_days_7d >= 5 else AnalyticsEvidence.MODERATE if snapshot.active_days_7d >= 3 else AnalyticsEvidence.LIMITED
        score = sum(1 if d == TrendDirection.IMPROVING else -1 if d == TrendDirection.DECLINING else 0 for d in directions)
        momentum = TrendDirection.IMPROVING if score > 0 else TrendDirection.DECLINING if score < 0 else TrendDirection.STABLE
        if evidence is AnalyticsEvidence.LIMITED:
            momentum = TrendDirection.STABLE

        insights = []
        for course in snapshot.courses:
            readiness = course.next_assessment_readiness if course.next_assessment_readiness is not None else _readiness(course)
            risk, reason = _risk_level(course, readiness)
            insights.append(CourseInsight(
                course_id=course.course_id, title=course.title, readiness=readiness,
                risk_level=risk, focus_reason=reason, mastery_direction=_course_direction(course),
            ))
        risk_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: (risk_order[x.risk_level], x.readiness if x.readiness is not None else 101, x.title.casefold()))

        explanation = "Indicateurs basés sur tes activités récentes. Ils décrivent ta progression ; ils ne prédisent pas ta note ni ta réussite."
        return AnalyticsReport(
            momentum=momentum, evidence=evidence, study_time=study_time, quiz_accuracy=quiz,
            active_days_7d=snapshot.active_days_7d, streak_days=snapshot.streak_days,
            plan_adherence_7d=snapshot.plan_adherence_7d,
            course_insights=tuple(insights), recommendations=_recommendations(snapshot),
            explanation=explanation,
        )

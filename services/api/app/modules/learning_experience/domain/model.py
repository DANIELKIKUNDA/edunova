from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class StudyMode(StrEnum):
    READ='read'; QUICK_REVIEW='quick_review'; FLASHCARDS='flashcards'; QUIZ='quiz'; EXERCISES='exercises'; FOCUS='focus'; EXAM='exam'
class SessionState(StrEnum):
    ACTIVE='active'; PAUSED='paused'; COMPLETED='completed'; ABANDONED='abandoned'
class MasteryStage(StrEnum):
    NOT_STARTED='not_started'; VIEWED='viewed'; STUDIED='studied'; PRACTICED='practiced'; ASSESSED='assessed'; MASTERED='mastered'

_STAGE_RANK={x:i for i,x in enumerate(MasteryStage)}
@dataclass(frozen=True)
class StudySession:
    id:str; account_id:str; course_id:str; chapter_id:str|None; mode:StudyMode; state:SessionState
    started_at:datetime; updated_at:datetime; ended_at:datetime|None; active_seconds:int; last_position:str|None
    objective:str|None; row_version:int=1
@dataclass(frozen=True)
class LearningProgress:
    account_id:str; course_id:str; chapter_id:str; stage:MasteryStage; completion_ratio:float
    practice_attempts:int; assessment_attempts:int; correct_answers:int; total_answers:int; updated_at:datetime
    @property
    def accuracy(self)->float: return 0.0 if self.total_answers == 0 else self.correct_answers/self.total_answers
    def promote(self, target:MasteryStage)->MasteryStage:
        return target if _STAGE_RANK[target] > _STAGE_RANK[self.stage] else self.stage
@dataclass(frozen=True)
class ErrorItem:
    id:str; account_id:str; course_id:str; chapter_id:str|None; source_type:str; source_id:str; prompt:str
    correct_answer:str|None; attempts:int; resolved:bool; next_review_at:datetime|None; created_at:datetime; updated_at:datetime
@dataclass(frozen=True)
class ReviewCard:
    account_id:str; card_id:str; course_id:str; chapter_id:str|None; repetitions:int; interval_days:int; ease_factor:float; due_at:datetime; updated_at:datetime

def next_spaced_review(card:ReviewCard|None, *, quality:int, now:datetime, account_id:str, card_id:str, course_id:str, chapter_id:str|None)->ReviewCard:
    if quality < 0 or quality > 5: raise ValueError('quality_out_of_range')
    reps=0 if card is None else card.repetitions
    ease=2.5 if card is None else card.ease_factor
    interval=0 if card is None else card.interval_days
    if quality < 3: reps=0; interval=1
    else:
        reps += 1
        interval = 1 if reps == 1 else 6 if reps == 2 else max(1, round(interval*ease))
    ease=max(1.3, ease + (0.1-(5-quality)*(0.08+(5-quality)*0.02)))
    from datetime import timedelta
    return ReviewCard(account_id,card_id,course_id,chapter_id,reps,interval,ease,now+timedelta(days=interval),now)


class ExamPlanState(StrEnum):
    ACTIVE='active'; COMPLETED='completed'; CANCELLED='cancelled'
@dataclass(frozen=True)
class ExamPlan:
    id:str; account_id:str; title:str; exam_at:datetime; daily_minutes:int; course_ids:tuple[str,...]; state:ExamPlanState; created_at:datetime; updated_at:datetime; row_version:int=1
@dataclass(frozen=True)
class StudyRecommendation:
    kind:str; priority:int; label:str; reason:str; course_id:str|None=None; chapter_id:str|None=None

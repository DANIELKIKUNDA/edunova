from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class QuestionType(StrEnum): SINGLE='single'; MULTIPLE='multiple'; TRUE_FALSE='true_false'; SHORT='short'; EXERCISE='exercise'
class AttemptState(StrEnum): ACTIVE='active'; SUBMITTED='submitted'; GRADED='graded'; ABANDONED='abandoned'
class BloomLevel(StrEnum): REMEMBER='remember'; UNDERSTAND='understand'; APPLY='apply'; ANALYZE='analyze'; EVALUATE='evaluate'; CREATE='create'
@dataclass(frozen=True)
class ExamQuestion:
 id:str; bank_id:str; course_id:str; chapter_id:str|None; kind:QuestionType; prompt:str; choices:tuple[str,...]; correct:tuple[str,...]; explanation:str; source_pages:tuple[int,...]; provenance_sha256:str; difficulty:int=2; approved:bool=True; points:int=1
 bloom_level:BloomLevel=BloomLevel.UNDERSTAND; learning_objective:str=''; cognitive_steps:tuple[str,...]=(); distractor_rationales:tuple[str,...]=(); quality_score:int=0; clinical_vignette:bool=False
@dataclass(frozen=True)
class ExamBlueprint:
 id:str; title:str; course_id:str; duration_minutes:int; question_count:int; pass_percent:int=60; shuffle:bool=True; approved_only:bool=True; row_version:int=1
 bloom_distribution:dict[str,int]|None=None; min_quality_score:int=0
@dataclass(frozen=True)
class AttemptAnswer:
 question_id:str; values:tuple[str,...]; marked_for_review:bool=False
@dataclass(frozen=True)
class ExamAttempt:
 id:str; account_id:str; blueprint_id:str; question_ids:tuple[str,...]; started_at:datetime; expires_at:datetime; state:AttemptState=AttemptState.ACTIVE; answers:tuple[AttemptAnswer,...]=(); submitted_at:datetime|None=None; row_version:int=1
@dataclass(frozen=True)
class QuestionResult:
 question_id:str; earned:int; possible:int; correct:bool; explanation:str; source_pages:tuple[int,...]; chapter_id:str|None; bloom_level:str='understand'; learning_objective:str=''
@dataclass(frozen=True)
class ExamResult:
 attempt_id:str; earned:int; possible:int; percent:int; passed:bool; by_chapter:dict[str,int]; questions:tuple[QuestionResult,...]; by_bloom:dict[str,int]|None=None
@dataclass(frozen=True)
class QuestionQualityReport:
 score:int; bloom_level:str; higher_order:bool; blocking_issues:tuple[str,...]; warnings:tuple[str,...]; strengths:tuple[str,...]

class ImportFormat(StrEnum): GIFT='gift'; MOODLE_XML='moodle_xml'; PLAIN='plain'
class ReviewStatus(StrEnum): IMPORTED='imported'; ANALYZED='analyzed'; NEEDS_REVIEW='needs_review'; APPROVED='approved'; REJECTED='rejected'
@dataclass(frozen=True)
class QuestionOrigin:
 id:str; question_id:str; source_document_id:str; source_format:ImportFormat; external_id:str|None; original_text:str; import_sha256:str; duplicate_fingerprint:str; inferred_bloom:BloomLevel; bloom_confidence:int; review_status:ReviewStatus=ReviewStatus.IMPORTED; recurrent_theme:str|None=None
@dataclass(frozen=True)
class QuestionImportReport:
 source_document_id:str; source_format:str; imported:int; duplicates:int; rejected:int; question_ids:tuple[str,...]; warnings:tuple[str,...]=()
@dataclass(frozen=True)
class VariantSpecification:
 source_question_id:str; target_bloom:str; target_difficulty:int; preserve_learning_objective:str; must_change:tuple[str,...]; must_preserve:tuple[str,...]; forbidden:tuple[str,...]; generation_contract_version:str='question-variant-v1'

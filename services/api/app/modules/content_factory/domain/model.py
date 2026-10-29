from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class FactoryState(StrEnum):
    QUEUED='queued'; PROCESSING='processing'; READY_FOR_REVIEW='ready_for_review'; FAILED='failed'; CANCELLED='cancelled'
class AssetKind(StrEnum):
    OUTLINE='outline'; SUMMARY_EXPRESS='summary_express'; SUMMARY_DETAILED='summary_detailed'; FLASHCARD='flashcard'; QUIZ='quiz'; EXERCISE='exercise'; RAG_CHUNK='rag_chunk'; CONCEPT='concept'
class GateSeverity(StrEnum):
    BLOCKING='blocking'; WARNING='warning'; INFO='info'

@dataclass(frozen=True, slots=True)
class FactoryRun:
    id:str; ingestion_document_id:str; editorial_item_id:str|None; requested_by:str; state:FactoryState; pipeline_version:str; prompt_version:str; source_sha256:str; academic_context_json:str; requested_assets_json:str; created_at:datetime; updated_at:datetime; started_at:datetime|None=None; completed_at:datetime|None=None; lease_owner:str|None=None; lease_expires_at:datetime|None=None; attempt:int=0; max_attempts:int=3; last_error:str|None=None; quality_score:int|None=None
@dataclass(frozen=True, slots=True)
class FactoryAsset:
    id:str; run_id:str; kind:AssetKind; ordinal:int; title:str; payload_json:str; content_sha256:str; confidence:float; status:str; created_at:datetime
@dataclass(frozen=True, slots=True)
class EvidenceLink:
    id:str; run_id:str; asset_id:str; source_document_id:str; page_start:int; page_end:int; quote:str; quote_sha256:str; created_at:datetime
@dataclass(frozen=True, slots=True)
class QualityGate:
    id:str; run_id:str; code:str; severity:GateSeverity; passed:bool; detail:str; created_at:datetime

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class NodeKind(StrEnum): COURSE='course'; CHAPTER='chapter'; CONCEPT='concept'; SUBCONCEPT='subconcept'; COMPETENCY='competency'; LEARNING_OBJECTIVE='learning_objective'
class RelationKind(StrEnum): PREREQUISITE_OF='prerequisite_of'; PART_OF='part_of'; DEPENDS_ON='depends_on'; CONTRASTS_WITH='contrasts_with'; CAUSES='causes'; EXPLAINS='explains'; ASSESSED_BY='assessed_by'; REMEDIATED_BY='remediated_by'
class GovernanceState(StrEnum): CANDIDATE='candidate'; VALIDATED='validated'; PUBLISHED='published'; REJECTED='rejected'; RETIRED='retired'
class Origin(StrEnum): HUMAN='human'; SOURCE_EXTRACTION='source_extraction'; AI_PROPOSAL='ai_proposal'; IMPORT='import'
class ExtractionState(StrEnum): DRAFT='draft'; IN_REVIEW='in_review'; ACCEPTED='accepted'; REJECTED='rejected'
@dataclass(frozen=True)
class KnowledgeNode:
 id:str; tenant_id:str; kind:NodeKind; label:str; description:str; course_id:str|None; source_revision_id:str|None; source_locator:str|None; provenance_sha256:str|None; state:GovernanceState; origin:Origin; version:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True)
class KnowledgeRelation:
 id:str; tenant_id:str; source_id:str; target_id:str; kind:RelationKind; rationale:str; confidence:int; state:GovernanceState; origin:Origin; source_revision_id:str|None; provenance_sha256:str|None; version:int; created_by:str; validated_by:str|None; created_at:datetime; updated_at:datetime
@dataclass(frozen=True)
class LearningDependency:
 concept_id:str; distance:int; path:tuple[str,...]; relation_path:tuple[str,...]
@dataclass(frozen=True)
class ExtractionBatch:
 id:str; tenant_id:str; source_revision_id:str; source_sha256:str; course_id:str|None; state:ExtractionState; created_by:str; reviewed_by:str|None; candidate_count:int; created_at:datetime; updated_at:datetime
@dataclass(frozen=True)
class ExtractionCandidate:
 id:str; batch_id:str; tenant_id:str; candidate_type:str; label:str; source_label:str|None; target_label:str|None; kind:str; rationale:str; source_locator:str; confidence:int; fingerprint:str; state:ExtractionState; created_node_id:str|None; created_relation_id:str|None; created_at:datetime; updated_at:datetime

class SnapshotState(StrEnum): ACTIVE='active'; SUPERSEDED='superseded'
@dataclass(frozen=True)
class GraphSnapshot:
 id:str; tenant_id:str; sequence:int; content_sha256:str; node_count:int; relation_count:int; reason:str; created_by:str; state:SnapshotState; created_at:datetime
@dataclass(frozen=True)
class GraphImpact:
 id:str; tenant_id:str; relation_id:str; change_kind:str; affected_concept_id:str; distance:int; path:tuple[str,...]; snapshot_id:str|None; created_at:datetime

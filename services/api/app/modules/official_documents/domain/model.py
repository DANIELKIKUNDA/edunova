from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class DocumentState(StrEnum): ISSUED='issued'; REVOKED='revoked'
@dataclass(frozen=True)
class OfficialDocument:
 id:str; institution_id:str; student_id:str; service_request_id:str; serial_number:str; kind:str; title:str; sha256_hex:str; pdf_bytes:bytes; verification_token_hash:str; state:DocumentState; issued_by:str; issued_at:datetime; revoked_by:str|None=None; revoked_at:datetime|None=None; revocation_reason:str|None=None; source_evidence_hash:str|None=None; source_jury_outcome_id:str|None=None; replaces_document_id:str|None=None; issuer_name:str|None=None; issuer_legal_name:str|None=None; issuer_country_code:str|None=None; template_version:str='official-v1'

@dataclass(frozen=True)
class OfficialDocumentEvent:
 id:str; institution_id:str; document_id:str; actor_id:str; event_type:str; reason:str|None; created_at:datetime

class TemplateState(StrEnum): DRAFT='draft'; PUBLISHED='published'; RETIRED='retired'
@dataclass(frozen=True)
class OfficialDocumentTemplate:
 id:str; institution_id:str; kind:str; version:str; name:str; state:TemplateState; created_by:str; created_at:datetime; published_by:str|None=None; published_at:datetime|None=None; retired_by:str|None=None; retired_at:datetime|None=None

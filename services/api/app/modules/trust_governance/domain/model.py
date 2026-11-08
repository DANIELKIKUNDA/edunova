from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class ConsentState(StrEnum):
    GRANTED='granted'; WITHDRAWN='withdrawn'
class PrivacyRequestKind(StrEnum):
    EXPORT='export'; DELETE='delete'; ANONYMIZE='anonymize'
class PrivacyRequestState(StrEnum):
    REQUESTED='requested'; PROCESSING='processing'; COMPLETED='completed'; REJECTED='rejected'

@dataclass(frozen=True)
class ConsentRecord:
    id:str; account_id:str; purpose:str; policy_version:str; state:ConsentState; recorded_at:datetime; source:str='user'
@dataclass(frozen=True)
class PrivacyRequest:
    id:str; account_id:str; kind:PrivacyRequestKind; state:PrivacyRequestState; requested_at:datetime; completed_at:datetime|None=None
@dataclass(frozen=True)
class SecurityLedgerEvent:
    id:str; actor_id:str|None; action:str; resource_type:str; resource_id:str; occurred_at:datetime; previous_hash:str; event_hash:str; metadata_json:str='{}'
@dataclass(frozen=True)
class RetentionPolicy:
    id:str; institution_id:str; data_class:str; retention_days:int; policy_version:str; updated_at:datetime; updated_by:str
@dataclass(frozen=True)
class MfaCredential:
    account_id:str; encrypted_secret:str; enabled:bool; created_at:datetime; verified_at:datetime|None=None

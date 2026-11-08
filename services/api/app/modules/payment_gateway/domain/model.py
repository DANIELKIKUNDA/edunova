from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
class PaymentStatus(StrEnum): PENDING='pending';SUCCEEDED='succeeded';FAILED='failed';EXPIRED='expired';CANCELLED='cancelled'
@dataclass(frozen=True)
class PaymentIntent:
 id:str;institution_id:str;student_id:str;amount_minor:int;currency:str;provider:str;payer_msisdn:str;idempotency_key:str;merchant_reference:str;provider_reference:str|None;status:PaymentStatus;created_by:str;created_at:datetime;updated_at:datetime;expires_at:datetime;failure_code:str|None;receipt_id:str|None
@dataclass(frozen=True)
class ProviderEvent:
 id:str;provider:str;provider_event_id:str;payment_intent_id:str;provider_reference:str|None;status:str;payload_sha256:str;received_at:datetime;processed:bool

@dataclass(frozen=True)
class PaymentAttempt:
 id:str;payment_intent_id:str;provider:str;kind:str;attempt_no:int;outcome:str;detail:str|None;created_at:datetime
@dataclass(frozen=True)
class ReconciliationRecord:
 id:str;payment_intent_id:str;provider:str;provider_reference:str|None;provider_status:str;local_status:str;matched:bool;note:str|None;checked_by:str;checked_at:datetime

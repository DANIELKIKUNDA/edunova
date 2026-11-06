from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class LicenseState(StrEnum): ACTIVE='active'; GRACE='grace'; SUSPENDED='suspended'; EXPIRED='expired'; CANCELED='canceled'
class LedgerKind(StrEnum): PAYMENT='payment'; REFUND='refund'; LICENSE='license'; PARTNER_SHARE='partner_share'; SETTLEMENT='settlement'; ADJUSTMENT='adjustment'
class PartnerState(StrEnum): ACTIVE='active'; SUSPENDED='suspended'
class SettlementState(StrEnum): CALCULATED='calculated'; CLOSED='closed'; PAID='paid'; VOID='void'

@dataclass(frozen=True, slots=True)
class CampusLicense:
    id:str; institution_id:str; plan_code:str; state:LicenseState; seats:int; price_cdf:int; starts_at:datetime; ends_at:datetime; grace_until:datetime|None; created_by:str; created_at:datetime
    def __post_init__(self):
        if (self.seats < 1 or self.price_cdf < 0 or self.ends_at <= self.starts_at
            or (self.grace_until is not None and self.grace_until < self.ends_at)):
            raise ValueError('invalid_campus_license')
    def effective_state(self, now:datetime) -> LicenseState:
        if self.state in {LicenseState.SUSPENDED,LicenseState.CANCELED}: return self.state
        if now < self.starts_at:return LicenseState.EXPIRED
        if now < self.ends_at:return LicenseState.ACTIVE
        if self.grace_until and now < self.grace_until:return LicenseState.GRACE
        return LicenseState.EXPIRED
    def permits(self, now:datetime, active_students:int) -> bool:
        return self.effective_state(now) in {LicenseState.ACTIVE,LicenseState.GRACE} and active_students <= self.seats

@dataclass(frozen=True, slots=True)
class CommercialLedgerEntry:
    id:str; institution_id:str|None; account_id:str|None; partner_id:str|None; kind:LedgerKind; reference_type:str; reference_id:str; amount_cdf:int; created_at:datetime; metadata_json:str='{}'
    def __post_init__(self):
        if self.amount_cdf == 0: raise ValueError('zero_ledger_entry')

@dataclass(frozen=True, slots=True)
class RevenuePartner:
    id:str; name:str; share_bps:int; state:PartnerState; created_at:datetime
    def __post_init__(self):
        if not 0 <= self.share_bps <= 10000: raise ValueError('invalid_partner_share')

@dataclass(frozen=True, slots=True)
class RevenueShareRule:
    id:str; partner_id:str; institution_id:str|None; product_code:str|None; share_bps:int; starts_at:datetime; ends_at:datetime|None
    def __post_init__(self):
        if not 0 <= self.share_bps <= 10000: raise ValueError('invalid_revenue_share')

@dataclass(frozen=True, slots=True)
class PartnerSettlement:
    id:str; partner_id:str; period_start:datetime; period_end:datetime; gross_cdf:int; partner_cdf:int; platform_cdf:int; status:str; created_at:datetime
    def __post_init__(self):
        if self.period_end <= self.period_start: raise ValueError('invalid_settlement_period')

@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    provider:str; expected_count:int; matched_count:int; missing_provider_refs:tuple[str,...]; amount_mismatch_refs:tuple[str,...]; unknown_provider_refs:tuple[str,...]
    @property
    def clean(self)->bool:return not (self.missing_provider_refs or self.amount_mismatch_refs or self.unknown_provider_refs)

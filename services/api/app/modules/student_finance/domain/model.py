from dataclasses import dataclass
from datetime import date,datetime
from enum import StrEnum
class ScheduleState(StrEnum): DRAFT='draft';PUBLISHED='published';RETIRED='retired'
class ChargeState(StrEnum): OPEN='open';PARTIAL='partial';PAID='paid';VOID='void'
class TxKind(StrEnum): CHARGE='charge';PAYMENT='payment';SCHOLARSHIP='scholarship';DISCOUNT='discount';SPONSOR='sponsor';REFUND='refund';REVERSAL='reversal'
class CashState(StrEnum): OPEN='open';CLOSED='closed'
class SponsorState(StrEnum): DRAFT='draft';ACTIVE='active';CLOSED='closed'
@dataclass(frozen=True)
class FeeSchedule:
 id:str;institution_id:str;program_unit_id:str;academic_year_id:str;name:str;currency:str;state:ScheduleState;row_version:int;created_by:str;created_at:datetime;published_at:datetime|None
@dataclass(frozen=True)
class FeeItem:
 id:str;schedule_id:str;code:str;label:str;amount_minor:int;due_on:date|None;mandatory:bool;installment_no:int
@dataclass(frozen=True)
class StudentCharge:
 id:str;institution_id:str;student_id:str;registration_id:str;fee_item_id:str;code:str;label:str;amount_minor:int;paid_minor:int;currency:str;due_on:date|None;state:ChargeState;created_at:datetime
@dataclass(frozen=True)
class LedgerEntry:
 id:str;institution_id:str;student_id:str;kind:TxKind;amount_minor:int;currency:str;reference:str;charge_id:str|None;actor_id:str;note:str|None;created_at:datetime
@dataclass(frozen=True)
class FinanceReceipt:
 id:str;institution_id:str;student_id:str;reference:str;amount_minor:int;currency:str;payment_method:str;external_reference:str|None;issued_by:str;issued_at:datetime;reversed:bool=False
@dataclass(frozen=True)
class CashSession:
 id:str;institution_id:str;cashier_id:str;currency:str;opening_float_minor:int;state:CashState;opened_at:datetime;closed_at:datetime|None;expected_minor:int|None;counted_minor:int|None;variance_minor:int|None;close_note:str|None
@dataclass(frozen=True)
class SponsorAgreement:
 id:str;institution_id:str;name:str;reference:str;currency:str;ceiling_minor:int;used_minor:int;valid_from:date;valid_until:date;state:SponsorState;created_by:str;created_at:datetime
@dataclass(frozen=True)
class PaymentPlan:
 id:str;institution_id:str;student_id:str;registration_id:str;name:str;approved_by:str;reason:str;created_at:datetime
@dataclass(frozen=True)
class PaymentPlanLine:
 id:str;plan_id:str;sequence_no:int;amount_minor:int;due_on:date

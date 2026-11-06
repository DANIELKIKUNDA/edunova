"""Physical library circulation. Separate from the EduNova digital learning library."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PhysicalBook:
    id: str
    institution_id: str
    title: str
    author: str
    isbn: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PhysicalCopy:
    id: str
    institution_id: str
    book_id: str
    barcode: str
    active: bool
    created_at: datetime
    condition: str = 'serviceable'  # serviceable, damaged, lost, withdrawn
    row_version: int = 1


@dataclass(frozen=True, slots=True)
class PhysicalLoan:
    id: str
    institution_id: str
    copy_id: str
    borrower_account_id: str
    borrowed_at: datetime
    due_at: datetime
    returned_at: datetime | None
    row_version: int
    renewal_count: int = 0
    last_renewed_at: datetime | None = None
    closure_reason: str | None = None  # returned, damaged, lost; NULL = open


@dataclass(frozen=True, slots=True)
class PhysicalLibraryPolicy:
    institution_id: str
    loan_days: int = 21
    max_open_loans: int = 3
    max_renewals: int = 2
    renewal_days: int = 14
    row_version: int = 0  # 0 = effective default, no custom policy row
    updated_at: datetime | None = None

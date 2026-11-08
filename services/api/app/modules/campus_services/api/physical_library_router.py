"""Physical books, copies and loans, with identity inferred from the bearer token."""
from datetime import datetime
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime

router = APIRouter()


def call(fn):
    try:
        return fn()
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        message = str(exc)
        code = 409 if any(s in message for s in (
            'unavailable', 'concurrent', 'already_exists', 'quota',
            'overdue', 'renewal_limit', 'policy_concurrent', 'concurrent_modification', 'not_restorable')) else 400
        raise HTTPException(code, message) from exc


def encode(value):
    result = asdict(value)
    return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in result.items()}


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    author: str = Field(min_length=1, max_length=180)
    isbn: str = Field(default='', max_length=32)


class CopyIn(BaseModel):
    book_id: str = Field(min_length=1, max_length=64)
    barcode: str = Field(min_length=1, max_length=64)


class BorrowIn(BaseModel):
    copy_id: str = Field(min_length=1, max_length=64)


class ReturnIn(BaseModel):
    expected_version: int = Field(ge=1)


class RenewIn(BaseModel):
    expected_version: int = Field(ge=1)


class PolicyIn(BaseModel):
    expected_version: int = Field(ge=0)
    loan_days: int = Field(ge=1, le=60)
    max_open_loans: int = Field(ge=1, le=10)
    max_renewals: int = Field(ge=0, le=2)
    renewal_days: int = Field(ge=1, le=30)


@router.get('/institutions/{institution_id}/library/policy')
def get_policy(institution_id: str, user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.physical_library.policy(user.account_id, institution_id)))


@router.put('/institutions/{institution_id}/library/policy')
def put_policy(institution_id: str, data: PolicyIn, user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.physical_library.update_policy(
        user.account_id, institution_id, **data.model_dump())))


@router.get('/institutions/{institution_id}/library/books')
def list_books(institution_id: str, user: AuthContext = Depends(current_auth)):
    return [encode(v) for v in call(lambda: runtime.physical_library.books(user.account_id, institution_id))]


@router.post('/institutions/{institution_id}/library/books')
def create_book(institution_id: str, data: BookIn, user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.physical_library.add_book(
        user.account_id, institution_id, **data.model_dump())))


@router.get('/institutions/{institution_id}/library/copies')
def list_copies(institution_id: str, book_id: str | None = None, user: AuthContext = Depends(current_auth)):
    copies = call(lambda: runtime.physical_library.copies(
        user.account_id, institution_id, book_id=book_id))
    available = call(lambda: runtime.physical_library.available_copy_ids(user.account_id, institution_id))
    return [{**encode(v), 'available': v.id in available} for v in copies]


@router.post('/institutions/{institution_id}/library/copies')
def create_copy(institution_id: str, data: CopyIn, user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.physical_library.add_copy(
        user.account_id, institution_id, **data.model_dump())))


@router.get('/institutions/{institution_id}/library/loans')
def list_loans(institution_id: str, user: AuthContext = Depends(current_auth)):
    loans = call(lambda: runtime.physical_library.loans(user.account_id, institution_id))
    now = runtime.physical_library.now()
    eligible = call(lambda: runtime.physical_library.eligible_renewal_ids(
        user.account_id, institution_id))
    return [{**encode(v),
             'overdue': v.returned_at is None and v.due_at <= now,
             'can_renew': v.id in eligible}
            for v in loans]


@router.post('/institutions/{institution_id}/library/loans')
def checkout(institution_id: str, data: BorrowIn, user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.physical_library.borrow(
        user.account_id, institution_id, copy_id=data.copy_id)))


@router.post('/institutions/{institution_id}/library/loans/{loan_id}/renew')
def renew(institution_id: str, loan_id: str, data: RenewIn,
          user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.physical_library.renew_loan(
        user.account_id, institution_id, loan_id=loan_id,
        expected_version=data.expected_version)))


@router.post('/institutions/{institution_id}/library/loans/{loan_id}/return')
def checkin(institution_id: str, loan_id: str, data: ReturnIn,
            user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.physical_library.return_loan(
        user.account_id, institution_id, loan_id=loan_id,
        expected_version=data.expected_version)))


class IncidentIn(BaseModel):
    expected_version: int = Field(ge=1)
    condition: str = Field(pattern=r'^(lost|damaged)$')


@router.post('/institutions/{institution_id}/library/loans/{loan_id}/incident')
def incident(institution_id: str, loan_id: str, data: IncidentIn,
             user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.physical_library.report_loan_incident(
        user.account_id, institution_id, loan_id=loan_id,
        expected_version=data.expected_version, condition=data.condition)))


@router.post('/institutions/{institution_id}/library/copies/{copy_id}/restore')
def restore_copy(institution_id: str, copy_id: str, data: ReturnIn,
                 user: AuthContext = Depends(current_auth)):
    return encode(call(lambda: runtime.physical_library.restore_damaged_copy(
        user.account_id, institution_id, copy_id=copy_id,
        expected_version=data.expected_version)))

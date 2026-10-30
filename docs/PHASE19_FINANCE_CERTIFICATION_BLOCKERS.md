# EduNova Phase 19 — Financial certification blockers

Status: **NOT CERTIFIED**. This document records code-reviewed risks, not executed test results.

## Confirmed architecture risks

1. `SqlStudentFinanceRepository.add_receipt`, `update_charge_paid`, and `add_ledger` each open their own SQLAlchemy session and commit independently. A failure between these calls can leave a receipt, charge balances, and ledger out of sync.
2. `SqlPaymentGatewayRepository.add_event`, `add_attempt`, `save`, and `mark_event` also commit independently. A callback interrupted after the finance receipt is created can leave a provider event unprocessed or the payment intent pending.
3. Concurrent provider callbacks for the same intent can both read `pending` before either commits. The unique constraints on provider/event IDs and external references are useful but do **not** establish a single atomic settlement transaction.
4. `StudentFinanceService.payment` currently checks for an existing external reference before inserting a receipt. Under concurrency, the database unique constraint may reject the losing request, but callers must recover deterministically rather than treating an `IntegrityError` as a settled payment.

## Required production-grade implementation

- Execute provider event claim, intent state transition, receipt creation, charge allocations, and ledger entries in **one database transaction**.
- Lock the intent row (`SELECT ... FOR UPDATE`) and relevant student charge rows in a deterministic order; verify pending state and outstanding balance while locks are held.
- Enforce uniqueness of provider/event IDs, institution/idempotency keys, and institution/external receipt references in PostgreSQL.
- Return the existing settlement for exact retries; reject conflicting payloads, students, amounts, currencies, or providers. Handle unique constraint races by rolling back and re-reading the committed result.
- Avoid network calls or external audit I/O inside the transaction. Publish notifications via a transactional outbox if needed.
- Preserve a recoverable audit trail for signed callbacks that arrive after terminal states without creating duplicate receipts.

## Required evidence before Phase 19 sign-off

1. PostgreSQL integration test: injected failure after receipt insert leaves **zero** new receipt/ledger/charge updates.
2. PostgreSQL integration test: injected failure after charge update leaves **zero** changes.
3. Concurrent callbacks with distinct provider event IDs for the same intent yield exactly **one** receipt and correct total allocation.
4. Concurrent callbacks with the same provider event ID yield exactly **one** processed event.
5. A crash/retry after settlement returns the original receipt, with no new ledger entries.
6. Cross-institution access, reversed receipt replay, conflicting external references, expired/cancelled intent behavior.
7. Full backend pytest, Flutter student/admin analyze and tests, Android/web builds where supported.

## GitHub Actions

Run the above after CI minutes become available. Existing isolated tests in `services/api/tests/test_phase19_payment_hardening.py` are **not** substitutes for real PostgreSQL concurrency tests.

Do not merge the draft import PR or mark Phase 19 certified solely because isolated unit tests pass.

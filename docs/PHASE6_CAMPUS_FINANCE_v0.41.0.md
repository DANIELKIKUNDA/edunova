# EduNova v0.41.0 RC — Phase 6 Campus Finance

Phase 6 introduces a tenant-scoped student receivables core: immutable published fee schedules, installments/due dates, idempotent assessment, student charges, cashier receipts, deterministic oldest-due allocation, scholarships/discounts/sponsor credits, append-only ledger semantics, refunds by compensating entries, self-service statements, and explicit overpayment rejection until a credit-balance policy is configured.

Design benchmark: mature SIS finance products separate tuition/fee assessment, student accounts/receivables, payment plans, sponsorship, cashiering, refunds and GL/reconciliation boundaries. EduNova deliberately implements the student-account boundary here while keeping provider Mobile Money confirmation in Phase 7 and full enterprise accounting outside EduNova 1.0.

Certification boundary: backend/static certification only. Real PostgreSQL concurrency, payment provider callbacks, production cashier hardware/processes, Flutter runtimes and external reconciliation remain machine/provider certification items.

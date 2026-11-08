# EduNova v0.41.1 — Phase 6 Campus Finance Maximum Depth

## Scope closed in this checkpoint
This hardening pass deepens the student-finance boundary before provider payments: cashier sessions and reconciliation, governed sponsor agreements with validity and ceilings, approved payment plans, receivables aging, and strict currency isolation.

## Controls added
- Cash payments require an open cashier session in the same currency.
- Cash closure computes expected cash from opening float plus non-reversed cash receipts; non-zero variance requires a reason and is audited.
- Sponsor agreements have institution scope, unique reference, currency, validity interval, ceiling and consumed amount. Credits cannot exceed either sponsor ceiling or student debt.
- One governed payment plan per registration; lines must be positive, ordered chronologically and total exactly the current outstanding receivable.
- Statements expose balances by currency; credits cannot offset debt in another currency.
- Aging buckets: current, 1–30, 31–60, 61–90 and 90+ days.

## Certification executed
- Backend suite: 537/537 PASS.
- Phase 6 targeted tests: 11/11 PASS.
- Migration contract isolated: PASS.
- Migration chain: 0001–0063 contiguous.
- compileall: PASS.
- LOT32 global audit: 17/17 PASS.

## Certification boundary
This checkpoint certifies backend behavior in the current execution environment. It does not certify Flutter builds/devices, real PostgreSQL concurrency/locking behavior, production object storage, provider Mobile Money callbacks, or production cashier hardware. Those remain machine/external certification work.

# EduNova v0.42.0 — Phase 7 Mobile Money & External Payments

## Scope
Provider-neutral payment intent state machine integrated with Campus Finance. A provider request is never treated as collected money before a verified terminal success callback.

## Controls
- PENDING / SUCCEEDED / FAILED / EXPIRED / CANCELLED lifecycle.
- Institution-scoped idempotency key with conflict detection.
- Unique merchant reference and provider transaction reference.
- Student debt/currency validation before initiation.
- Provider event inbox with unique event IDs and SHA-256 payload evidence.
- HMAC callback verification over the complete canonical callback envelope.
- Duplicate callbacks are idempotent; contradictory terminal callbacks are rejected.
- Only verified SUCCEEDED callbacks post a Mobile Money receipt into the student-finance ledger.
- Failed/expired attempts never credit the student account.
- 30-minute intent expiry foundation.
- Provider adapter boundary includes sandbox, Orange Money and Airtel Money identifiers; only sandbox secret is configured in this checkpoint. Real provider credentials/contracts remain external certification work.

## Standards/research alignment
Architecture was checked against GSMA Mobile Money API asynchronous callback/polling model and transaction/reversal concepts, and Orange Money Web Payment public documentation. No claim of real Orange/Airtel provider certification is made.

## Certification
- Backend: 541/541 PASS.
- Phase 7 targeted tests: 4/4 PASS.
- LOT32 global audit: 17/17 PASS.
- compileall: PASS.
- Migration chain: 0001..0064.
- Flutter/device/provider live certification: not performed in this environment.

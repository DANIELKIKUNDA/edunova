# EduNova v0.46.0 — Phase 11 Digital Student Service Desk

Phase 11 introduces a tenant-scoped digital student service desk integrated with the canonical student record rather than a parallel student identity.

## Scope
- Requests: attestation, transcript, duplicate, administrative correction, appeal, other.
- Student-owned submission and tracking.
- Staff assignment and governed state machine: submitted → in review → action required / approved / rejected; approved → fulfilled; controlled cancellation.
- Mandatory reason for rejection or action-required decisions.
- Fulfillment records a document reference and SHA-256 integrity proof; document generation itself remains the responsibility of the existing document/publication engines and Phase 12 official-document work.
- Optimistic locking and immutable request-event timeline.
- Tenant/student isolation and role enforcement.

## Certification
- Backend: 581/581 tests PASS.
- Phase 11 targeted: 5/5 PASS.
- compileall: PASS.
- Migration contract in full suite: PASS; migrations 0001–0071.
- LOT32 global audit: 17/17 PASS.

## Boundary
This checkpoint does not claim legal e-signature, Flutter device certification, or complete official diploma/transcript generation. Phase 12 will govern official document issuance and public verification.

# EduNova v0.47.2 — Phase 12 Academic Provenance

## Scope
This checkpoint closes the provenance gap between published Gradebook results, canonical StudentCourseRegistration records and official transcript issuance.

## Implemented
- Immutable `PublishedCourseResult` ledger for published course outcomes.
- Gradebook publication records gradebook ID, offering, canonical course registration, percentage, pass/fail outcome, component summary hash, actor and publication timestamp.
- Migration 0074 creates `academic_published_course_results` with tenant/student/course/gradebook indexes and one immutable published result per canonical course registration.
- Official transcripts now consume the published-results ledger rather than inferring marks from `VALIDATED` / `FAILED` states.
- Transcript issuance fails closed when a canonical validated/failed course lacks published grade provenance or when canonical state conflicts with recorded pass/fail evidence.
- Transcript PDF lines include percentage and outcome, and the official document source evidence hash is derived from the exact published result provenance.
- Existing diploma jury/completed-registration controls from v0.47.1 remain intact.

## Certification executed in this environment
- Backend suite: 598/598 PASS.
- Targeted academic-delivery + Phase 12 + migration tests: 19/19 PASS.
- Migration contract isolated: PASS.
- Python compileall: PASS.
- LOT32 global structural audit: 17/17 PASS.
- Migration chain: 0001 through 0074 contiguous.

## Explicit boundary
This checkpoint does not claim qualified electronic signatures, legal equivalence of a SHA-256 digest to an e-signature, device QR scanning certification, Flutter build certification, or production PostgreSQL/object-storage certification. Those remain machine/provider/external certification concerns.

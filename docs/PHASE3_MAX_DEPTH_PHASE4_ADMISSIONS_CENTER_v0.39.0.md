# EduNova v0.39.0 — Phase 3 Maximum Depth + Phase 4 Admissions Center

## Phase 3 hardening
- Explicit privacy and application-declaration consent evidence with policy version and SHA-256 evidence hash.
- Submission integrity snapshot hashes the candidate payload and active-document manifest.
- Candidate application listing, draft document deletion, withdrawal, and status surface.
- Existing resumable/chunked upload, MIME/signature verification, malware boundary, replacement history and tenant privacy retained.
- Submission now requires mandatory documents plus both consent classes.
- Correction workflow can reopen a submitted application without fabricating a new application identity.

## Phase 4 Admissions Center
- Idempotent institutional intake of submitted applications.
- Institution-scoped review queues and reviewer assignment with optimistic locking.
- Per-document ACCEPTED / REJECTED / CORRECTION_REQUIRED verification with reviewer identity, note and timestamp.
- Completeness gate: a file cannot be declared complete until every active submitted document has an accepted review.
- Formal correction request reopens the candidate dossier for controlled remediation.
- Decision states: COMPLETE, ELIGIBLE, WAITLISTED, ADMITTED, REFUSED.
- Refusal requires a reason; final decisions are restricted to Owner/Rector/Admin/Academic Admin, while Faculty Admin can participate in review but cannot take final decisions.
- Candidate status endpoint exposes workflow state without exposing internal reviewer data.
- Tenant isolation and audit events are enforced at service boundaries.

## Database
Migration 0058 adds consent evidence, immutable submission snapshots, admission review cases, and per-document reviews with indexes and uniqueness constraints.

## Certification executed in this environment
- Full backend suite: 513/513 PASS.
- Targeted Phase 3 + Phase 4 tests are included in the full suite.
- Python compileall: PASS.
- LOT32 global audit: 17/17 PASS.
- Migration contract includes 0001..0058 and passed.

## Certification boundary
Flutter SDK/device compilation, PostgreSQL/Redis/MinIO production runtime, ClamAV network integration and real provider/infrastructure tests remain machine/external certification items. This checkpoint does not claim those proofs.

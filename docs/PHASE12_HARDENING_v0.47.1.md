# EduNova v0.47.1 — Phase 12 Official Documents Hardening

## Scope implemented
- Diploma issuance gated by a published PASS jury outcome and a COMPLETED academic registration in the exact jury scope.
- Academic evidence provenance persisted on issued documents (`source_evidence_hash`, `source_jury_outcome_id`).
- Transcript output derived from canonical student course registrations with deterministic evidence hashing; no numeric marks are fabricated where a canonical grade-to-ECUE mapping is unavailable.
- Duplicate documents require an existing source document belonging to the same student and retain replacement provenance.
- QR verification marker rendered into generated PDFs; public verification remains privacy-minimal.
- Issuance/revocation audit events wired to the existing audit service.
- Service desk document kinds extended with diploma and certificate.

## Certification executed
- Backend: 596/596 PASS.
- Phase 12 + migration contract targeted: 10/10 PASS.
- Migration contract isolated: PASS.
- Python compileall: PASS.
- LOT32 global audit: 17/17 PASS.
- Migration chain: 0001 through 0073.

## Boundary still open
This checkpoint does not claim a fully regulatory transcript with numeric grades because the repository does not yet expose a certified canonical mapping from published gradebook results to every StudentCourseRegistration/ECUE. It intentionally prints canonical course registration/validation states instead of inventing marks. Institution-specific diploma templates, qualified/legal electronic signatures, real device QR scanning, and external trust-provider validation remain outside this backend/static certification.

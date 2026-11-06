# EduNova v0.37.0 — Phase 2 Public Catalog & Admission Campaigns

Phase 2 turns the institutional academic foundation into a controlled public admissions surface.

## Implemented
- Institution-scoped admission campaigns tied to a PROGRAM, ACADEMIC_YEAR and a PUBLISHED curriculum.
- Draft -> Published -> Closed lifecycle with optimistic locking.
- Public, shareable slugs per institution; draft/closed campaigns are never returned by public detail.
- Campaign metadata: opening/closing timestamps, capacity, application fee in minor units, ISO-style 3-letter currency, contact address.
- Ordered configurable admission requirements, including whether a supporting document is required.
- Public endpoints expose institution/program/year/curriculum/campaign/requirements without membership or private student data.
- Institutional writes remain Campus-RBAC protected and audited.
- Tenant isolation and curriculum-publication preconditions are tested.
- Migration 0054 adds admission_campaigns and admission_requirements with uniqueness/check/index constraints.

## Certification evidence in this environment
- Backend: 494/494 pytest PASS.
- Phase 2 targeted tests: 5/5 PASS.
- LOT32 global audit: 17/17 PASS.
- compileall: PASS.
- Migrations contiguous 0001..0054.

## Explicitly not claimed
Flutter/device builds, real weak-network behavior, production PostgreSQL migration timing, external payment providers, and human UX acceptance require machine/device/external certification later.

## Next roadmap phase
Phase 3: candidate identity and resumable digital application dossier, including draft persistence and document intake workflow. Phase 2 intentionally does not collect candidate personal documents yet.

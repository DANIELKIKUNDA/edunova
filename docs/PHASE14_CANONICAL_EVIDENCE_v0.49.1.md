# EduNova v0.49.1 — Phase 14 Canonical Pedagogical Evidence

This checkpoint deepens pedagogical intelligence by connecting teacher-facing recommendations to canonical EduNova evidence rather than caller-supplied aggregates.

## Implemented
- Read-only evidence projection over immutable published course results and attendance records belonging only to closed attendance sessions.
- Offering must have an Academic Delivery curriculum-course link; no guessed curriculum mapping.
- Teacher/admin RBAC and institution/offering scope checks.
- Deterministic explainable recommendation reuses `deterministic_pedagogical_rules_v1`.
- Explicit limitation: the current canonical grade publication model is course-scoped, not learning-objective-scoped. The API therefore labels the report `curriculum_course` and does not fabricate objective-level mastery.
- Evidence identifiers/hashes are returned for traceability. No grades, jury decisions, Student Success cases or learner records are mutated.

## Certification executed
- Phase 14 targeted: 6/6 PASS.
- Full backend: 627/627 PASS.
- No migration: this is a read-only projection over existing canonical tables.

## Remaining Phase 14 work
Canonical objective-level assessment mapping, common-error aggregation, longitudinal comparisons, persisted teacher acknowledgement/action feedback, and UI/device certification.

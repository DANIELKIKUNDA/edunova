# EduNova v0.43.1 — Phase 8 canonical integrity hardening / Phase 9 readiness

## Verified changes
- Publication of gradebooks now checks canonical course registration eligibility for all students **before** changing the gradebook state.
- When Academic Delivery is attached, retraction of a published gradebook is blocked until a governed reversal workflow exists for canonical student course results. This prevents contradictory student transcript states.
- Two new adversarial tests exercise the preflight and protected retraction.

## Important remaining risk
- Gradebook publication and the per-student canonical result updates must ultimately be one atomic database transaction, with row-level concurrency protection and durable outbox events where needed. The preflight reduces but does not eliminate a write failure after publication. This has **not** been certified here.
- Academic jury/deliberations are **not yet implemented** in this checkpoint. Do not use a gradebook lock as proof of formal jury approval.

## Phase 9 implementation contract (next)
1. Jury sessions scoped by institution, cohort, curriculum version, semester and exam session; role-based committee membership and quorum.
2. Immutable snapshot of published ECUE results, source version/hash, attendance/exemptions and credits; no duplicate results or cross-tenant records.
3. Versioned academic rules approved by institution: thresholds, compensation, retakes, missing grades, credits, progression. Never invent official local rules.
4. Explicit proposal -> committee review -> votes/quorum -> approved minutes -> signed publication; separation of preparation and approval.
5. Student appeal, rectification and superseding decision with preserved prior signed minutes; never overwrite historical outcomes.
6. Transactional gradebook/canonical-record locking and tests against concurrent committee decisions.

## Certification boundary
Backend tests, compileall and static audits are not substitutes for Flutter device builds, PostgreSQL concurrency, signatures infrastructure or institution-specific regulatory approval.

# EduNova v0.50.0 — Phase 15 / Institutional Intelligence Foundation

Source: EduNova v0.49.13 — clôture locale du backend Phase 14. Phase 15 begins here; **it is not declared complete**.

## Scope

The existing `institutional_analytics` module (Lot 27, migrations 0045–0047) is reused. No new parallel analytics module and no mutation of gradebook, Student Success, jury, or pedagogical intelligence. This increment adds a read-only, governed decision brief.

- Route: `GET /v1/institutional-analytics/institutions/{iid}/intelligence/decision-brief` (registered in `app/main.py`; local router path: `/institutions/{iid}/intelligence/decision-brief`).
- Parameters: `academic_period_id`, `academic_unit_id`, `cohort_id`, `offering_id` (optional, with strict compatibility checks).
- Roles: owner, rector, admin, academic_admin, auditor; faculty_admin only for its institutionally assigned academic-unit subtree. Teachers/students/nonmembers are denied.
- Observables: teaching session completion, syllabus coverage, attendance, assignments, published/validated gradebook pass rates. Weak-value signals are **recommendations to review**, never individual automatic decisions.
- Referential checks: period, unit, cohort, offering exist under the current institution; incompatible filters rejected; cross-university membership never authorizes access.
- Read-only projected data: attendance records must match tenant, active enrollment and a closed session, with review state `clear`; submissions must match active enrollment, and gradebook marks must be validated, tenant-matched, from an active enrollee, and belong to a **published** gradebook. Legacy Lot-27 projections remain unchanged (versioned source semantics).
- Disclosure: at least **three distinct actively enrolled learners** in the reporting scope. Counts use `COUNT(DISTINCT student_account_id)`, preventing the same student enrolled in multiple cohorts from bypassing minimum population. Rates also require at least 3 observations of their declared denominator; attendance and gradebook rates separately require 3 **distinct contributing students**. If suppressed, neither numerator nor denominator, percentage nor derived weak-value flag is disclosed.
- Privacy: no row-level accounts, Student Success cases, raw student grades, tutor transcripts, private documents, or jury decisions are released. Internal contributor metadata remains server-side and is never returned. A `policy` flag indicates that the result is observational, non-authoritative, and makes no automatic decisions.
- Audit: authorized brief viewing emits `institutional_intelligence.brief.viewed` when an audit writer is configured.

## Known limits and non-certifications

- The source projections are observational; completeness is not universal, and a weak rate does not establish causality.
- The `data_quality` minimum release guard is a **small-cell protection**, not a universal anonymization or inference-proof privacy claim. Combining disclosures across overlapping scopes can still lead to differencing attacks; formal anti-differencing budgets are not implemented in v0.50.0. Consequently, this is staff-only, not a public statistics API.
- Group thresholds do not certify legal/privacy compliance or formal statistical anonymization.
- Gradebook comparisons and deliberations from Phase 14 remain **informative**, not official grade/jury synchronization.
- No PostgreSQL/Redis, Flutter/mobile, object storage, external providers, or real-device certification is claimed in this package.
- No migration needed; last SQL migration remains 0084.
- Future Phase 15 iterations should strengthen snapshot temporal comparability, protected cross-scope rollups, anti-differencing, provenance indicators, and administrative briefing UX before declaring the phase complete.

## Testing

Dedicated integration suite: `services/api/tests/test_phase15_institutional_intelligence.py` using true SQLite tables and malicious cross-tenant/inconsistent rows. Includes positive and adversarial role, institution, scope, small cohort, repeated attendance, repeated gradebook evidence, unpublished grades, and exclusion of foreign/un-enrolled marks.

Global regression command: `PYTHONPATH=services/api python -m pytest -q services/api/tests`.
Evidence and SHA-256 are written into `docs/certification/` in the released ZIP. Do not treat static/memory/SQLite tests as infrastructure/device certification.

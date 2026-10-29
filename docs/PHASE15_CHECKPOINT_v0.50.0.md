# EduNova v0.50.0 — Phase 15 Foundation checkpoint

- Previous canonical archive: `EduNova_v0.49.13_RC_PHASE14_BACKEND_CLOSURE.zip`
- Previous canonical SHA-256: `ab8aed8c45a9a788266ffc23b02a73d4dda6f6cdb3113a605ead40a79cfdbb43` (verified locally).
- Phase 14 remains closed for local backend implementation as documented in v0.49.13.
- Phase 15 is **started, not completed**.
- Existing institutional analytics Lot 27 is extended in place; no parallel module rebuilt.
- New authenticated endpoint: `/v1/institutional-analytics/institutions/{iid}/intelligence/decision-brief`.
- Decision-support signals, data-quality contract, RBAC hierarchy, tenant isolation, cohort/period/offer validity and suppression of small disclosure groups.
- Tenant and active-enrollment validation for attendance, submissions and published/validated gradebook inputs; malformed foreign/un-enrolled inputs are not used for governed rates.
- Rates are withheld for fewer than three distinct active learners, fewer than three denominator observations, or fewer than three individual attendance/gradebook contributors.
- New test suite: `services/api/tests/test_phase15_institutional_intelligence.py` (15 cases, positive and adversarial).
- No SQL migration; last migration is 0084.
- No change to official notes, academic jury decisions, private documents or Student Success case records.

See `docs/PHASE15_INSTITUTIONAL_INTELLIGENCE_FOUNDATION_v0.50.0.md` for assumptions and limitations; `docs/certification/PHASE15_v0.50.0_EXECUTION.txt` for command outputs and execution evidence.

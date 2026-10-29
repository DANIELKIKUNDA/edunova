# EduNova v0.46.1 — Phase 11 Service Desk Hardening

## Verified changes
- Institution-scoped staff queue with state/assignee filtering, deterministic ordering, bounded pagination.
- Institution-scoped service request dashboard with counts by status.
- Role protection on staff-only queue/dashboard.
- Assignee validation now requires a service-desk staff role (not merely any non-student Campus membership).
- Student timeline redacts internal assignment metadata while retaining student-visible correction reasons.
- No second student identity or parallel document engine introduced.

## Tests
- Full backend: 585/585 PASS.
- Targeted Phase 11 + isolated migration contract: 10/10 PASS.
- Python compileall PASS.
- LOT32 global audit: 17/17 PASS.
- No new migration required (repository queries and application/API contract changes only).

## Remaining limitations
- The existing fulfillment endpoint records a supplied document reference and SHA-256; it does NOT cryptographically validate the bytes against the official document engine. Do not claim official issuance or qualified signature.
- Event persistence and request state update are not a single database transaction; atomic outbox/transactional event handling remains to be completed.
- Flutter Android/Web/Windows and production infrastructure are not certified here.
- Student request pages and complete staff workflow UI remain to be verified.

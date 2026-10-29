# LOT 22 — EduNova Campus Core v0.23.0

## Purpose
Campus Core turns the former EduConnect direction into EduNova's institutional foundation without creating a second identity system or a separate application account.

## Delivered bounded context
- institution tenant with immutable id, unique slug, branding metadata, lifecycle and optimistic version;
- academic hierarchy: campus, faculty, department, program;
- academic year / semester / term hierarchy with date containment validation;
- institution-scoped memberships and roles;
- invitation and explicit acceptance workflow;
- suspension/revocation without deletion of the personal EduNova identity;
- cohorts/promotions and student enrollment;
- tenant overview counters;
- audit events for institution, structure, membership and enrollment mutations;
- REST surface under `/v1/campus`;
- mobile entry point **Mon université · Campus** and explicit Personal/Campus separation.

## Security invariants
1. Cross-tenant access is denied before resource disclosure.
2. Tenant-scoped repositories require `institution_id` for resource lookup.
3. Faculty admins cannot escalate users into global institution administration.
4. The tenant never owns the personal EduNova account.
5. Revoking Campus membership does not delete personal data.
6. Owner revocation is blocked until a future explicit ownership-transfer workflow exists.
7. Optimistic locking protects institution and membership state changes.

## Intentionally reserved for later lots
LOT 23 owns course delivery; LOT 24 assignments/submissions/grading; LOT 25 gradebook/results; LOT 26 attendance/communications/operations; LOT 27 institutional analytics. LOT 22 only establishes durable references those modules can depend on.

## Machine certification still required
Real PostgreSQL migration/concurrency, Flutter analyze/test/build, Android/PWA/Windows rendering, accessibility/device testing and production tenancy penetration testing remain OPEN-machine.

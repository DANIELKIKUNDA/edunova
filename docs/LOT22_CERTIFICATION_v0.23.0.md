# LOT 22 certification — v0.23.0

Date: 2026-09-25
Scope: EduNova Campus Core, ChatGPT execution environment.

## Automated evidence
- backend regression partition A: 187 PASS;
- backend regression partition B: 179 PASS;
- total non-overlapping backend suite: 366 PASS;
- targeted Campus + API + migration contract: 13 PASS;
- Python `compileall app`: PASS;
- `scripts/audit_lot22.py`: 14/14 PASS;
- archive integrity test: required before delivery.

## Product invariants certified here
- authenticated personal identity is separate from Campus membership;
- cross-tenant read/write is denied by application authorization and tenant-scoped repository lookups;
- institution creator becomes owner;
- invitations require explicit acceptance;
- role escalation by faculty admin is rejected;
- owner revocation is rejected;
- academic hierarchy and academic-period containment are validated;
- enrollment requires an active student membership;
- optimistic version checks cover mutable institution/member lifecycle;
- audit events are emitted for Campus mutations.

## OPEN-machine
PostgreSQL migration execution and concurrent-write race tests; Flutter analyze/test/build; Android/PWA/Windows UI validation; real device accessibility; production reverse-proxy/auth deployment; penetration tests and high-volume tenant/load tests.

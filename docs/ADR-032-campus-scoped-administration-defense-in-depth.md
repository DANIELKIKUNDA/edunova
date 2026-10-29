# ADR-032 — Scoped Campus administration and defense in depth

## Decision
Campus authorization is tenant-scoped first and academic-unit-scoped second. `faculty_admin` must carry a unit scope and may only mutate or enumerate resources in that subtree. Role assignment follows an explicit privilege matrix; owner is never assignable through the generic invitation/role-change paths.

Suspended/archived institutions are readable by existing authorized members but mutation is denied. Database constraints mirror domain enums and structural references so a bypass of application code cannot trivially create cross-structure or invalid-state rows.

## Rationale
A single-role RBAC implementation without scope checks allows a faculty administrator to become an institution-wide administrator in practice. Campus is intended for multiple real universities, so tenant isolation alone is insufficient: delegated administration must also respect organizational boundaries.

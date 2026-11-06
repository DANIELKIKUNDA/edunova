# ADR-031 — EduNova Campus multi-tenant boundary

Status: accepted for LOT 22 / v0.23.0.

EduNova Campus is a bounded context attached to the existing personal EduNova identity. An institution is a tenant, not the owner of an EduNova account. Membership can be invited, suspended or revoked without deleting or transferring the personal account.

Every Campus aggregate that can expose institutional data carries `institution_id`. Application services authorize membership before repository reads/writes exposed by the API. Repository lookup methods for units, periods and cohorts additionally require the tenant id, preventing accidental cross-tenant object lookup. Future LOTs must preserve this rule rather than accepting naked resource ids at trust boundaries.

Roles are institution-scoped. `owner`, `rector`, `admin`, `academic_admin`, `faculty_admin`, `teacher`, `student`, and `auditor` are distinct from EduNova Studio editorial roles. A faculty administrator cannot promote another account into institution-wide administrative roles. The owner cannot be revoked in LOT 22; ownership transfer is intentionally deferred until a dedicated audited workflow exists.

Campus data must never imply access to private student documents, private Tutor conversations, or personal learning history. Later institutional analytics may consume explicitly defined institutional/aggregate signals only.

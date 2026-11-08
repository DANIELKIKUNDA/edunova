# EduNova v0.39.1 — Phase 4 Maximum Depth

Phase 4 admissions-center hardening adds durable admissions committees, voting/quorum, an immutable operational event timeline, admissions dashboard counts, and campaign-capacity enforcement at final admission.

## Governance
- Committee is institution + campaign scoped.
- Chair is always a voting member; duplicate members are collapsed.
- Quorum must be positive and cannot exceed voting membership.
- Only committee voting members may vote.
- One current vote per voter/review/committee; a revote replaces the prior recommendation instead of double-counting.
- Committee/review campaign mismatch is rejected.

## Operational integrity
- Intake, assignment, completion, correction request and final decisions create persistent admission events.
- Institution dashboard exposes state counts and unassigned workload.
- Final `admitted` transition checks campaign capacity and refuses over-admission.
- Existing optimistic locking, tenant isolation, document-by-document verification and final-decision RBAC remain enforced.

## Certification boundary
Backend/static tests in this checkpoint do not constitute Flutter/device, production PostgreSQL/Redis/object-storage, external provider or production-load certification.

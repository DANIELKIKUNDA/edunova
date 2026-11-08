# ADR-016 — Publication boundary integrity
Status: Accepted — v0.15.1

Decision: revalidate editorial governance at publish-time, enforce distribution invariants at application + PostgreSQL layers, and make every catalog snapshot independently SHA-256 verifiable. This prevents stale approvals from becoming releases and makes distributed catalog state auditable.

# EduNova v0.47.5 — Phase 12 Document Lifecycle

## Scope
Hardening of official-document lifecycle governance. This checkpoint adds an append-only institutional lifecycle ledger for issue and revocation events and makes lifecycle-event persistence part of the same database transaction as the document mutation.

## Changes
- `official_document_events` append-only lifecycle table (migration 0076).
- Issuance writes the official document, service-request fulfillment, service-request event, and document `issued` event atomically.
- Revocation writes the state mutation and document `revoked` event atomically.
- Revocation reasons are mandatory and constrained to 5–1000 characters.
- Staff-only, institution-scoped document history endpoint.
- Regression tests for atomic lifecycle events, reason validation, RBAC, and tenant scoping.

## Certification executed
- Full backend: 604/604 PASS.
- Phase 12 + migration contract targeted: 17/17 PASS.
- `compileall`: PASS.
- LOT32 global audit: 17/17 PASS.
- Migration chain: through 0076.

## Certification boundary
This is backend/static certification. It does not certify qualified electronic signatures/PKI, Flutter/device QR scanning, real production PostgreSQL/object storage, or external provider/legal compliance.

# EduNova v0.47.6 — Phase 12 Maximum Depth

## Scope
This checkpoint closes the remaining backend governance gaps identified for official documents before Phase 13.

## Institutional template governance
- New `official_document_templates` registry with institution, document kind, immutable version, lifecycle state and publisher provenance.
- Lifecycle: `draft -> published -> retired`.
- Database partial unique index guarantees at most one published template for a document kind in an institution.
- Publishing a new template retires the previous active version transactionally.
- Official issuance is refused when no published template exists.
- The exact published template version is snapshotted into the issued document and remains stable after later template changes.

## Controlled correction / replacement
- `admin_correction` requests may now produce a corrected official document from an existing active document belonging to the same student.
- The corrected document preserves the original document type and records `replaces_document_id` plus the source SHA-256.
- Fulfillment of the correction request, insertion of the new document, and supersession/revocation of the prior document are one database transaction.
- The old document receives a `superseded` lifecycle event; its public verification consequently becomes invalid.
- Ordinary `duplicate` issuance remains distinct and does not silently revoke the source document.

## Migration
`0077_official_document_template_governance_v0_47_6.sql`.

## Verification executed
- Full backend: 607 passed.
- Phase 12 + migration contract targeted: 20 passed.
- Migration contract isolated: 1 passed.
- LOT32 global certification test module: 6 passed (the module contains multiple contract assertions).
- Python compileall: PASS.

## Certification boundary
This is backend/static certification in the available environment. It does not certify qualified electronic signatures/PKI, legal recognition in a jurisdiction, Flutter builds, physical-device QR scanning, external object storage, or production PostgreSQL/Redis/provider infrastructure.

# EduNova v0.47.3 — Phase 12, document integrity hardening

## Actual changes
- Fixed an ORM mapping defect: three fields already defined in SQL migration 0073 and the domain model were missing from the SQLAlchemy `OfficialDocumentRow` mapping: `source_evidence_hash`, `source_jury_outcome_id`, `replaces_document_id`. Previously, actual database issuance of documents containing provenance metadata could fail because the repository attempted to pass unmapped fields to the row constructor. The mapping now persists and reads those fields.
- Disallowed duplicate-of-duplicate issuance, avoiding ambiguous chains of document ancestry.
- Disallowed issuance of a duplicate referencing a revoked original. A separate replacement/reissuance policy for revoked documents remains to be designed and validated with university rules.
- Added two regression tests for ORM mapping and duplicate source status/chain.
- No new migration: migration 0073 already contains all three columns.

## Executed tests
- Targeted Phase 12 and migration tests: 13 PASS.
- Complete backend test suite: 600 PASS, 0 FAIL.
- Python compileall: PASS.
- Device, Flutter build, production PostgreSQL, public QR scans and legal e-signatures: NOT certified.

## Caution
This checkpoint is a hardening increment, not final certification of Phase 12. Institution-specific templates, regulatory diploma validation, replacement workflows and device/provider checks remain open.

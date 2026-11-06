# EduNova v0.47.5 — Phase 12 Issuer Provenance

Phase 12 hardening focused on long-lived institutional document authenticity.

## Changes
- Official documents now snapshot the issuer's institution name, legal name and country code at issuance time.
- Each document stores an immutable template version (`official-v2`) so later template changes do not rewrite historical provenance.
- PDF rendering uses the issuer snapshot rather than the internal institution UUID as the displayed university identity.
- Public verification returns issuer identity and template version without exposing student personal data.
- Migration 0075 persists issuer provenance fields on `official_documents`.
- Regression tests prove issuer provenance survives a later institution rename.

## Certification executed on this tree
- Backend: 602/602 PASS.
- Targeted Phase 12 + migration contract: 15/15 PASS.
- Migration contract isolated: 1/1 PASS.
- Python compileall: PASS.
- LOT32 structural audit: 17/17 PASS.
- Migration chain: 0001 through 0075 contiguous.

## Boundary
This is backend/static certification. It is not legal certification of electronic signatures, production PKI, device QR scanning, Flutter builds, PostgreSQL/Redis/object-storage production runtime, or external providers.

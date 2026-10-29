# EduNova v0.35.0 — Medicine Curriculum Canonical Integration

This release integrates the received 2025–2026 LMD Medicine curriculum as a source-faithful, read-only canonical reference for the content ingestion pipeline.

## Contract
- 14 semesters, Bachelier 1 through Master 4.
- Source-declared semester totals are preserved: 750 hours / 30 credits per semester.
- UE/ECUE codes, titles, CMI, TP+TD, TPE, totals, credits and percentages are preserved when visible in the source.
- Missing/irregular source data is represented explicitly; it is never guessed or silently repaired.
- Editorial suggestions from source page 7 are stored separately and are **not applied** to canonical rows.
- Search and audit endpoints prepare later mapping of real course/interrogation ZIPs to the curriculum.

## API
- `GET /v1/curricula/medicine`
- `GET /v1/curricula/medicine/semesters`
- `GET /v1/curricula/medicine/semesters/{semester}`
- `GET /v1/curricula/medicine/search?q=...`
- `GET /v1/curricula/medicine/audit`

## Known source review items preserved
- Semester 2 UE4:PDS declared credits conflict with visible ECUE credit sum.
- `NRP113 5` source code spacing irregularity.
- `CHI1448` row is incomplete in parsed source and is not reconstructed.
- `NEP1447` is repeated in semester 9.
- Semester 14 stage codes ending `14713` are preserved as received.

## Automated source arithmetic review
The canonical audit deliberately compares visible ECUE rows with source-declared semester totals. It currently surfaces additional source-level discrepancies instead of repairing them:
- Semester 7: visible rows compute to 775 hours / 31 credits while source declares 750 / 30.
- Semester 9: visible rows compute to 800 hours / 32 credits while source declares 750 / 30.
These are review flags, not EduNova corrections.

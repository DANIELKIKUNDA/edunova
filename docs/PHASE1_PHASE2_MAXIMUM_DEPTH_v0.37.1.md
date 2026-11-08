# EduNova v0.37.1 — Phase 1 & 2 Maximum-Depth Hardening

This checkpoint deliberately deepens Phase 1 (institutional academic foundation) and Phase 2 (public admissions catalog) before Phase 3 candidate PII/document ingestion.

## Phase 1 hardening
- Source-faithful Medicine import now preserves cycle, level, UE declared credits, CMI, TP/TD, TPE and percentage in the institutional curriculum rows.
- Curriculum pre-publication validation report with blocking vs source-review findings.
- Published curriculum remains immutable; controlled clone-to-new-version workflow copies courses and prerequisite graph with new identities.
- Explicit retirement lifecycle for superseded published curricula.
- Cohort-to-curriculum binding with one curriculum per cohort and program compatibility enforcement.
- Prerequisite statuses are constrained and prerequisite cycles remain rejected.
- Active program and active academic year are mandatory for new curricula.

## Phase 2 hardening
- Draft campaign editing with optimistic locking.
- Explicit validation report before publication.
- Requirement uniqueness, deletion and deterministic resequencing while draft.
- Timezone-aware admission windows are mandatory.
- Public availability is computed as upcoming/open/deadline_passed; lifecycle state remains institution-controlled.
- Rich public campaign metadata: instructions, study mode, campus label, intake label and eligibility summary.
- Campaign closure and archival lifecycle; archived campaigns disappear from public catalog.
- Active program/year and published matching curriculum remain mandatory.
- Slug uniqueness is checked at service boundary as well as database boundary.

## Verification
- Full backend: 499/499 PASS.
- LOT32 global audit: 17/17 PASS.
- Python compileall: PASS.
- Migration chain: 0001..0055.
- Flutter runtime build: not claimed in this environment.

## Deliberate boundary
Phase 3 remains responsible for candidate identities, applications, uploads, document verification and submission workflows. No candidate PII/document store was prematurely added to Phase 2.

# EduNova v0.48.1 — Phase 13 Student Success Early Warning

## Scope
This checkpoint deepens Phase 13 with deterministic, evidence-backed early-warning rules. It does not claim predictive AI, diagnosis, or causal inference.

## Implemented
- Staff-only student scan endpoint.
- Academic signal from immutable published course-result provenance: one published failure => medium; two or more => high.
- Attendance signal from records belonging to closed attendance sessions: minimum 3 records; attendance below 75% => medium, below 60% => high.
- Evidence SHA-256 and deterministic source key on automatically detected cases.
- Deduplication: rescanning unchanged evidence does not create duplicate cases.
- Automatic event explicitly records deterministic-rule provenance and absence of predictive/diagnostic claim.
- Tenant and student boundaries reuse the Phase 13 service controls.
- Migration 0079 adds provenance columns and a partial unique institutional source index.

## Certification executed
- Full backend suite: 612/612 PASS.
- Phase 13 + migration contract targeted: 6/6 PASS.
- Migration contract isolated: 1/1 PASS.
- Python compileall: PASS.
- LOT32 global audit script: 17/17 PASS.
- LOT32 pytest module: 6/6 PASS.

## Boundary
This is deterministic early warning, not a machine-learning risk score. It intentionally does not infer wellbeing, medical conditions, socioeconomic status, or dropout probability. Notification orchestration, intervention plans/outcome measurement, UI/device certification and production infrastructure remain later work.

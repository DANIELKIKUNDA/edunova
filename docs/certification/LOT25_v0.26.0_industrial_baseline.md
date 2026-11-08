# LOT 25 — v0.26.0 Industrial Baseline

Scope: institutional assessments, weighted gradebook and academic results. This bounded context intentionally differs from LOT 18 personal exam simulation and consumes only officially published LOT 24 assignment grades.

Guarantees: tenant/enrollment checks; staff-only mark mutation; component weights exactly 100% before opening; score bounds; explicit publication before student visibility; complete cohort results required before publication; audited retraction; optimistic row versions; no AI proposal is silently promoted to an official academic result.

OPEN-machine: PostgreSQL migration 0039 on a real instance and concurrent mark races; Flutter analyze/test/build; device accessibility; large-cohort load/endurance; university validation of local grading regulations and official transcript rules.

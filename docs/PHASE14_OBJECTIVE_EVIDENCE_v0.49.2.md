# EduNova v0.49.2 — Phase 14 Objective Evidence

This checkpoint adds an explicit canonical bridge from assessment evidence to learning objectives.

- Institutional learning-objective registry scoped to the curriculum course.
- Explicit question → objective mapping; no inference from free-text labels.
- Explicit assessment blueprint → teaching offering binding, preventing results from another offering/year being silently mixed.
- Objective reports use graded attempts only and aggregate question points per learner before calculating group mastery signals.
- Teacher/admin RBAC is enforced by the existing teaching assignment and Campus membership checks.
- The engine remains deterministic and non-predictive; it does not change grades or jury decisions.

Migration: `0082_pedagogical_objective_evidence_v0_49_2.sql`.

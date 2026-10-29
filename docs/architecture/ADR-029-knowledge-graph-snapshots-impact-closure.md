# ADR-029 — Knowledge Graph snapshots, impact analysis & industrial closure

Status: Accepted — EduNova 0.21.2.

## Decision
Published academic graph state is reproducibly fingerprinted into immutable snapshots. Dependency retirement uses optimistic version checks and produces persisted downstream impact records before the relation is retired. Learning orchestration consumes only published dependency edges and exposes an ordered prerequisite plan with explicit mastery evidence.

## Safety
A snapshot is evidence of graph state, not scientific truth. Candidate/unvalidated edges remain excluded from learning decisions. High-stakes provenance/review rules from ADR-027/028 remain mandatory. Impact analysis identifies potentially affected concepts; it does not silently rewrite assessments, remediation plans or mastery.

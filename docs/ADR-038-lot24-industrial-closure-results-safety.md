# ADR-038 — LOT24 industrial closure: official result visibility

## Decision
Assignment grades remain private grading records until the assignment reaches `results_published`. Publication is explicit and is rejected while any received submission lacks a human-validated final score. Retraction returns the assignment to `grading`, requires a reason, and is audited.

Automated/deterministic grading remains a proposal. It never bypasses human validation for the institutional final score.

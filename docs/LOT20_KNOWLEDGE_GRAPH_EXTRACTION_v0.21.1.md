# LOT 20 v0.21.1 — Knowledge Graph Extraction, Governance & Orchestration

This hardening adds source-to-graph extraction batches, candidate fingerprints, exact source locators, confidence, independent review, high-stakes gates, node/relation materialization, graph-health diagnostics and prerequisite learning sequences. It is designed for validated course revisions: extraction output is always candidate data. The existing Candidate → Validated → Published relation governance remains authoritative.

## Cross-lot orchestration
- LOT16 may consume published prerequisite structure to contextualize mastery evidence.
- LOT17 may consume `learning_sequence` to place deep prerequisites before a target concept.
- LOT18 may consume `assessment_context`; the graph selects concepts but cannot supply an unsourced answer key.
- LOT19 may combine observed weak concepts with published prerequisite paths for explainable root-cause candidates.

## Machine-open
PostgreSQL migration/concurrency, very-large-graph benchmarks, Flutter analyze/test/build and device UX/accessibility remain OPEN-machine. Domain-expert validation remains mandatory for medical/high-stakes graphs.

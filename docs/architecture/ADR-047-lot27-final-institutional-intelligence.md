# ADR-047 — LOT 27 final institutional intelligence

EduNova institutional analytics is a read-only projection over Campus, Teaching, Assignments, Gradebook, Campus Operations, Assessment and institution-scoped Knowledge Graph data.

## Decisions
- Metrics are versioned and snapshots immutable with SHA-256 content fingerprints.
- Hierarchical rollups follow academic-unit descendants and never silently widen a faculty administrator's scope.
- Bloom analytics are aggregate-only and derived from submitted institutional assessment results through blueprint → course.
- Knowledge Graph analytics include only institution-tenant, published nodes/relations for courses in scope.
- Early-warning signals are evidence-bearing observations, never automatic labels, sanctions or fitness judgements.
- Executive reports explicitly exclude personal Tutor conversations, private documents, private study activity and individual answers.
- Teacher analytics require an assigned offering. Student accounts cannot access institutional analytics.

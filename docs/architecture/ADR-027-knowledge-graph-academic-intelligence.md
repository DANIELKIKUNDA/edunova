# ADR-027 — Knowledge Graph & Academic Knowledge Intelligence
Status: Accepted — v0.21.0

EduNova models academic knowledge as a governed directed graph. Nodes represent courses, chapters, concepts, sub-concepts, competencies and learning objectives. Relations represent prerequisite, dependency, composition, contrast, causal/explanatory and assessment/remediation links.

## Safety and governance
AI/source extraction may only propose candidates. Non-human proposals require provenance. Candidate edges never influence learner decisions. Published high-stakes edges require provenance and independent validation. Dependency cycles are rejected. The graph selects learning context; it is never an unsourced scientific answer key.

## Pedagogical use
Published dependency paths support prerequisite diagnosis (LOT16/19), prerequisite-first scheduling (LOT17), multi-concept and transfer assessment context (LOT18), and explainable remediation. Graph traversals are deterministic and bounded.

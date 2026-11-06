# ADR-023 — Question Intelligence Factory

## Decision
Historical assessments are evidence, not a template to copy. EduNova imports GIFT/Moodle XML into an immutable provenance layer, deduplicates normalized stems, infers Bloom only as a review hint, and keeps every imported item unapproved until human review. Variant generation is contract-driven: preserve objective/source/cognitive demand, change scenario/surface values, forbid verbatim copying, answer leakage and unsupported facts. High-stakes approval remains human.

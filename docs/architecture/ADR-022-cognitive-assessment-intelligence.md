# ADR-022 — Cognitive assessment intelligence and Bloom-governed blueprints

**Status:** Accepted — v0.19.2

Assessment quality is a domain invariant, not a prompt-writing concern. EduNova stores Bloom level, learning objective, cognitive steps, distractor rationales, quality score and authentic-context marker on the question. Blueprints may specify a 100% Bloom distribution and minimum quality score. Selection fails closed when the bank cannot satisfy the requested cognitive profile; it does not silently substitute easier recall questions.

CREATE-level assessment requires constructed response/exercise. Results include a by-Bloom view. LLMs are optional authoring adapters and cannot bypass deterministic quality gates or editorial approval.

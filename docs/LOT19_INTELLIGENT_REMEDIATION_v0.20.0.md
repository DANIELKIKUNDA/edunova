# LOT 19 — Intelligent Remediation Engine — v0.20.0

## Purpose
Turn assessment evidence into an executable learning-repair loop, not a generic recommendation.

## Capabilities
- evidence-based misconception records by course/chapter/concept;
- severity + diagnostic confidence and Bloom gap;
- six-stage remediation path: diagnosis, micro-explanation, worked example, guided practice, transfer, reassessment;
- baseline vs verification gain;
- fail-safe rule: explanation/activity never equals mastery;
- unresolved paths loop back to targeted practice; successful paths return to spaced repetition;
- optimistic concurrency and persistence for offline/sync-ready clients;
- student premium remediation workspace with explicit evidence and progress.

## Pedagogical safeguards
A single wrong answer does not establish a misconception. Diagnosis exposes its evidence and confidence. New assessment evidence is required to close a misconception. Generated explanations must remain grounded in validated course sources when AI generation is connected. Medical/high-stakes material inherits editorial governance from LOT 11/13/18.

## Integrations
LOT 15 supplies Error Bank/progress evidence. LOT 16 remains the global adaptive profile. LOT 17 can schedule remediation actions. LOT 18 supplies assessment evidence and independent reassessment questions. The bounded context deliberately avoids making an LLM the authority on mastery.

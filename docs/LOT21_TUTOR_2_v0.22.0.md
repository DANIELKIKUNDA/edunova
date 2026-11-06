# LOT 21 — Tutor 2.0 / Socratic Academic Tutor — v0.22.0

## Goal
Turn the existing grounded RAG assistant into an explainable academic tutor.

## Policy
- Socratic-first when the learner is reasoning.
- Direct explanation remains available when explicitly requested.
- Progressive hints before solution dumping.
- Weak published prerequisites route to prerequisite repair.
- Repeated evidenced errors route to LOT19 remediation.
- Bloom target is explicit in every decision.
- High-stakes sessions abstain without validated source evidence.
- Tutor decisions persist with evidence, idempotency and row versions.

## Integration contract
LOT16 supplies mastery evidence; LOT20 supplies prerequisites; LOT18 supplies errors/assessment evidence; LOT19 performs remediation; LOT17 may schedule the resulting action. The graph selects concepts but never acts as an unsourced scientific answer key.

## OPEN-machine
PostgreSQL migration/concurrency, Flutter analyze/test/build, Android/PWA/Windows visual/accessibility, offline multi-device conflicts, real provider/RAG evaluation and pedagogical validation with real students.

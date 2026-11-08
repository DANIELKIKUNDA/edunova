# EduNova v0.44.1 — Phase 9 Jury Maximum Depth

This checkpoint deepens the jury/deliberation foundation without duplicating Gradebook.

## Added governance
- Formal jury commission membership with president/secretary/member roles.
- Voting/non-voting membership and active Campus membership validation.
- Configurable quorum per jury session.
- One president per commission.
- Per-student deliberation votes: approve, reject, abstain.
- Only voting commission members can vote; one vote per member/student.
- Lock requires a voting president, quorum on every outcome, and approval majority over rejection.
- Immutable-style deliberation evidence remains bound to canonical academic course-registration states.
- Minutes generation after lock with SHA-256 content hash over outcomes, evidence and votes.
- Publication requires generated minutes.
- Audit events for member addition, votes, minutes, lock and publication.

## Data/migrations
Migration 0068 adds jury_members, jury_votes, jury_minutes and jury_sessions.quorum.

## Certification executed in this environment
- Backend full suite: 566 passed.
- Phase 9 focused suite: 14 passed.
- LOT32 global audit: 17/17 PASS.
- Python compileall: PASS.
- Migration contract isolated: 1 passed.
- Migration chain: 0001 through 0068.

## Certification boundary
This is backend/static certification in the current environment. Flutter/device runtime, production PostgreSQL concurrency, qualified electronic signatures and jurisdiction-specific university regulations remain machine/external certification concerns.

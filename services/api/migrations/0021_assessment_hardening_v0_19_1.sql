-- LOT 18 hardening: immutable question set per attempt, optimistic concurrency and provenance are enforced by application + schema constraints.
CREATE UNIQUE INDEX IF NOT EXISTS ux_assessment_active_attempt ON assessment_attempts(account_id,blueprint_id) WHERE state='active';
CREATE INDEX IF NOT EXISTS ix_assessment_questions_bank ON assessment_questions(bank_id,approved);

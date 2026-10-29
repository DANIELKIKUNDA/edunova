-- EduNova v0.20.2 LOT 19 — industrial orchestration, idempotency and longitudinal evidence
CREATE TABLE IF NOT EXISTS remediation_events (
 id VARCHAR(64) PRIMARY KEY,
 account_id VARCHAR(64) NOT NULL,
 path_id VARCHAR(64), misconception_id VARCHAR(64),
 kind VARCHAR(32) NOT NULL,
 occurred_at TIMESTAMPTZ NOT NULL,
 payload JSONB NOT NULL DEFAULT '{}'::jsonb,
 mutation_id VARCHAR(96)
);
CREATE INDEX IF NOT EXISTS ix_remediation_events_account_time ON remediation_events(account_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS ix_remediation_events_path_time ON remediation_events(path_id, occurred_at DESC) WHERE path_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_remediation_events_mutation ON remediation_events(account_id, mutation_id) WHERE mutation_id IS NOT NULL;
ALTER TABLE remediation_paths ADD COLUMN IF NOT EXISTS last_mutation_id VARCHAR(96);
ALTER TABLE remediation_paths ADD COLUMN IF NOT EXISTS total_practice_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE remediation_paths ADD COLUMN IF NOT EXISTS successful_practice_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE remediation_paths ADD COLUMN IF NOT EXISTS cumulative_gain INTEGER NOT NULL DEFAULT 0;

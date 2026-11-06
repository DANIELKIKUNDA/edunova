-- EduNova v0.20.1 LOT 19 — Remediation Intelligence & Tutor Engine hardening
ALTER TABLE remediation_misconceptions ADD COLUMN IF NOT EXISTS root_cause VARCHAR(32) NOT NULL DEFAULT 'insufficient_evidence';
ALTER TABLE remediation_misconceptions ADD COLUMN IF NOT EXISTS hypothesis TEXT NOT NULL DEFAULT '';
ALTER TABLE remediation_misconceptions ADD COLUMN IF NOT EXISTS counter_evidence TEXT NOT NULL DEFAULT '[]';
ALTER TABLE remediation_misconceptions ADD COLUMN IF NOT EXISTS relapse_count INTEGER NOT NULL DEFAULT 0 CHECK(relapse_count >= 0);
ALTER TABLE remediation_misconceptions DROP CONSTRAINT IF EXISTS remediation_misconceptions_state_check;
ALTER TABLE remediation_misconceptions ADD CONSTRAINT remediation_misconceptions_state_check CHECK(state IN ('open','improving','resolved','relapsed'));
ALTER TABLE remediation_paths ADD COLUMN IF NOT EXISTS difficulty_level INTEGER NOT NULL DEFAULT 2 CHECK(difficulty_level BETWEEN 1 AND 5);
ALTER TABLE remediation_paths ADD COLUMN IF NOT EXISTS consecutive_successes INTEGER NOT NULL DEFAULT 0;
ALTER TABLE remediation_paths ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER NOT NULL DEFAULT 0;
ALTER TABLE remediation_paths ADD COLUMN IF NOT EXISTS last_transfer_score INTEGER CHECK(last_transfer_score BETWEEN 0 AND 100);
ALTER TABLE remediation_paths ADD COLUMN IF NOT EXISTS next_review_at TIMESTAMPTZ;
ALTER TABLE remediation_paths DROP CONSTRAINT IF EXISTS remediation_paths_status_check;
ALTER TABLE remediation_paths ADD CONSTRAINT remediation_paths_status_check CHECK(status IN ('active','completed','retained','abandoned'));
CREATE INDEX IF NOT EXISTS ix_remediation_retention_due ON remediation_paths(account_id,next_review_at) WHERE status='completed';

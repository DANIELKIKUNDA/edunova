-- LOT 16 final hardening: bounded snapshot history for trend/readiness queries.
CREATE INDEX IF NOT EXISTS ix_adaptive_account_model_time ON adaptive_learning_snapshots(account_id,model_version,generated_at DESC);
CREATE INDEX IF NOT EXISTS ix_adaptive_account_risk_time ON adaptive_learning_snapshots(account_id,risk,generated_at DESC);
ALTER TABLE adaptive_learning_snapshots ADD CONSTRAINT ck_adaptive_model_version_nonempty CHECK (length(trim(model_version)) > 0);

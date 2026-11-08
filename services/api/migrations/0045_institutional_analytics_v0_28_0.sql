-- LOT 27 v0.28.0 — Institutional Analytics & Academic Intelligence
-- Read models are computed from authoritative institutional tables; no personal/private tables are replicated.
CREATE TABLE IF NOT EXISTS institutional_analytics_snapshots (
 id VARCHAR(64) PRIMARY KEY,
 institution_id VARCHAR(64) NOT NULL,
 scope_type VARCHAR(24) NOT NULL,
 scope_id VARCHAR(64),
 academic_period_id VARCHAR(64),
 metric_contract_version INTEGER NOT NULL DEFAULT 1,
 payload_json TEXT NOT NULL,
 source_watermark VARCHAR(128) NOT NULL,
 generated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_inst_analytics_scope ON institutional_analytics_snapshots(institution_id, scope_type, scope_id, generated_at);

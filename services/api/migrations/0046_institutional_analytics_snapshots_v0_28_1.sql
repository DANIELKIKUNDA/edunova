-- LOT 27 v0.28.1 — immutable analytical history / hierarchical rollups
CREATE INDEX IF NOT EXISTS ix_inst_analytics_period_scope
 ON institutional_analytics_snapshots(institution_id, academic_period_id, scope_type, scope_id, generated_at);
CREATE INDEX IF NOT EXISTS ix_inst_analytics_watermark
 ON institutional_analytics_snapshots(institution_id, source_watermark);

-- EduNova v0.8.1 — LOT 7 hardening: device acknowledgements, revocation and safe compaction.

ALTER TABLE sync_devices ADD COLUMN IF NOT EXISTS last_sync_at timestamptz;
ALTER TABLE sync_devices ADD COLUMN IF NOT EXISTS acked_cursor bigint NOT NULL DEFAULT 0;
ALTER TABLE sync_devices ADD COLUMN IF NOT EXISTS revoked_at timestamptz;
CREATE INDEX IF NOT EXISTS ix_sync_devices_revoked_at ON sync_devices(revoked_at);

CREATE TABLE IF NOT EXISTS sync_account_state (
  account_id varchar(64) PRIMARY KEY,
  retained_floor bigint NOT NULL DEFAULT 0,
  last_compacted_at timestamptz
);

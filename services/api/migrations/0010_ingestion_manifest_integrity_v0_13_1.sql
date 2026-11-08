-- LOT 12 final hardening: persist the immutable canonical launch manifest.
ALTER TABLE ingestion_batches ADD COLUMN IF NOT EXISTS manifest_json TEXT;
CREATE INDEX IF NOT EXISTS ix_ingestion_batches_frozen_at ON ingestion_batches(frozen_at);

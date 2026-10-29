CREATE TABLE IF NOT EXISTS ingestion_batches (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(240) NOT NULL,
  created_by VARCHAR(64) NOT NULL,
  state VARCHAR(40) NOT NULL,
  defaults_json TEXT NOT NULL,
  manifest_version INTEGER NOT NULL DEFAULT 1,
  manifest_sha256 VARCHAR(64),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  frozen_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_ingestion_batches_state ON ingestion_batches(state);
CREATE INDEX IF NOT EXISTS ix_ingestion_batches_created_by ON ingestion_batches(created_by);
CREATE INDEX IF NOT EXISTS ix_ingestion_batches_created_at ON ingestion_batches(created_at);
CREATE INDEX IF NOT EXISTS ix_ingestion_batches_manifest_sha256 ON ingestion_batches(manifest_sha256);

CREATE TABLE IF NOT EXISTS ingestion_documents (
  id VARCHAR(64) PRIMARY KEY,
  batch_id VARCHAR(64) NOT NULL,
  idempotency_key VARCHAR(160) NOT NULL,
  filename VARCHAR(320) NOT NULL,
  declared_mime_type VARCHAR(120),
  detected_mime_type VARCHAR(120) NOT NULL,
  size_bytes INTEGER NOT NULL,
  checksum_sha256 VARCHAR(64) NOT NULL,
  storage_key VARCHAR(640),
  page_count INTEGER,
  width_px INTEGER,
  height_px INTEGER,
  state VARCHAR(40) NOT NULL,
  preflight_status VARCHAR(40) NOT NULL,
  rejection_code VARCHAR(120),
  duplicate_of_document_id VARCHAR(64),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  editorial_item_id VARCHAR(64),
  CONSTRAINT uq_ingestion_document_idempotency UNIQUE(batch_id,idempotency_key),
  CONSTRAINT uq_ingestion_document_checksum UNIQUE(batch_id,checksum_sha256)
);
CREATE INDEX IF NOT EXISTS ix_ingestion_documents_batch ON ingestion_documents(batch_id);
CREATE INDEX IF NOT EXISTS ix_ingestion_documents_state ON ingestion_documents(state);
CREATE INDEX IF NOT EXISTS ix_ingestion_documents_checksum ON ingestion_documents(checksum_sha256);
CREATE INDEX IF NOT EXISTS ix_ingestion_documents_editorial_item ON ingestion_documents(editorial_item_id);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
  id VARCHAR(64) PRIMARY KEY,
  batch_id VARCHAR(64) NOT NULL,
  document_id VARCHAR(64) NOT NULL UNIQUE,
  state VARCHAR(40) NOT NULL,
  priority INTEGER NOT NULL DEFAULT 50,
  attempt INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  next_run_at TIMESTAMPTZ NOT NULL,
  lease_owner VARCHAR(160),
  lease_expires_at TIMESTAMPTZ,
  heartbeat_at TIMESTAMPTZ,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ingestion_jobs_batch ON ingestion_jobs(batch_id);
CREATE INDEX IF NOT EXISTS ix_ingestion_jobs_state_next_run ON ingestion_jobs(state,next_run_at);
CREATE INDEX IF NOT EXISTS ix_ingestion_jobs_lease_expires ON ingestion_jobs(lease_expires_at);
CREATE INDEX IF NOT EXISTS ix_ingestion_jobs_priority ON ingestion_jobs(priority);

CREATE TABLE IF NOT EXISTS ingestion_results (
  id VARCHAR(64) PRIMARY KEY,
  batch_id VARCHAR(64) NOT NULL,
  document_id VARCHAR(64) NOT NULL UNIQUE,
  job_id VARCHAR(64) NOT NULL UNIQUE,
  artifact_key VARCHAR(640) NOT NULL,
  artifact_sha256 VARCHAR(64) NOT NULL,
  pipeline_version VARCHAR(80) NOT NULL,
  page_count INTEGER NOT NULL,
  sections_count INTEGER NOT NULL,
  chunks_count INTEGER NOT NULL,
  questions_count INTEGER NOT NULL,
  mean_ocr_confidence DOUBLE PRECISION,
  usable_text_ratio DOUBLE PRECISION NOT NULL,
  warnings_json TEXT NOT NULL DEFAULT '[]',
  needs_human_verification INTEGER NOT NULL DEFAULT 0,
  editorial_item_id VARCHAR(64),
  created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ingestion_results_batch ON ingestion_results(batch_id);
CREATE INDEX IF NOT EXISTS ix_ingestion_results_artifact_sha256 ON ingestion_results(artifact_sha256);
CREATE INDEX IF NOT EXISTS ix_ingestion_results_pipeline_version ON ingestion_results(pipeline_version);
CREATE INDEX IF NOT EXISTS ix_ingestion_results_editorial_item ON ingestion_results(editorial_item_id);

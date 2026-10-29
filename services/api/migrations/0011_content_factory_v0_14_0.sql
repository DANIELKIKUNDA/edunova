-- EduNova v0.14.0 / LOT 13 — Content Factory
CREATE TABLE IF NOT EXISTS content_factory_runs (
 id varchar(64) PRIMARY KEY, ingestion_document_id varchar(64) NOT NULL, editorial_item_id varchar(64), requested_by varchar(64) NOT NULL,
 state varchar(40) NOT NULL, pipeline_version varchar(80) NOT NULL, prompt_version varchar(80) NOT NULL, source_sha256 varchar(64) NOT NULL,
 academic_context_json text NOT NULL, requested_assets_json text NOT NULL, created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL,
 started_at timestamptz, completed_at timestamptz, lease_owner varchar(160), lease_expires_at timestamptz, attempt integer NOT NULL DEFAULT 0,
 max_attempts integer NOT NULL DEFAULT 3, last_error text, quality_score integer,
 CONSTRAINT uq_factory_run_idempotency UNIQUE(ingestion_document_id,pipeline_version,requested_assets_json),
 CONSTRAINT ck_factory_quality_score CHECK(quality_score IS NULL OR (quality_score BETWEEN 0 AND 100)),
 CONSTRAINT ck_factory_state CHECK(state IN ('queued','processing','ready_for_review','failed','cancelled'))
);
CREATE INDEX IF NOT EXISTS ix_factory_runs_state_created ON content_factory_runs(state,created_at);
CREATE INDEX IF NOT EXISTS ix_factory_runs_source_sha ON content_factory_runs(source_sha256);
CREATE TABLE IF NOT EXISTS content_factory_assets (
 id varchar(64) PRIMARY KEY, run_id varchar(64) NOT NULL REFERENCES content_factory_runs(id) ON DELETE CASCADE, kind varchar(40) NOT NULL, ordinal integer NOT NULL,
 title varchar(320) NOT NULL, payload_json text NOT NULL, content_sha256 varchar(64) NOT NULL, confidence double precision NOT NULL, status varchar(40) NOT NULL,
 created_at timestamptz NOT NULL, CONSTRAINT uq_factory_asset_ordinal UNIQUE(run_id,kind,ordinal), CONSTRAINT ck_factory_confidence CHECK(confidence BETWEEN 0 AND 1)
);
CREATE INDEX IF NOT EXISTS ix_factory_assets_run_kind ON content_factory_assets(run_id,kind);
CREATE TABLE IF NOT EXISTS content_factory_evidence (
 id varchar(64) PRIMARY KEY, run_id varchar(64) NOT NULL REFERENCES content_factory_runs(id) ON DELETE CASCADE,
 asset_id varchar(64) NOT NULL REFERENCES content_factory_assets(id) ON DELETE CASCADE, source_document_id varchar(64) NOT NULL,
 page_start integer NOT NULL, page_end integer NOT NULL, quote text NOT NULL, quote_sha256 varchar(64) NOT NULL, created_at timestamptz NOT NULL,
 CONSTRAINT ck_factory_pages CHECK(page_start > 0 AND page_end >= page_start)
);
CREATE INDEX IF NOT EXISTS ix_factory_evidence_asset ON content_factory_evidence(asset_id);
CREATE TABLE IF NOT EXISTS content_factory_quality_gates (
 id varchar(64) PRIMARY KEY, run_id varchar(64) NOT NULL REFERENCES content_factory_runs(id) ON DELETE CASCADE, code varchar(120) NOT NULL,
 severity varchar(30) NOT NULL, passed integer NOT NULL, detail text NOT NULL, created_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_factory_gates_run ON content_factory_quality_gates(run_id,passed);

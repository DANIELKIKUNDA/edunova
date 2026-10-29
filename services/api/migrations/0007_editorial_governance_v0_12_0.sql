CREATE TABLE IF NOT EXISTS editorial_members (
  account_id VARCHAR(64) PRIMARY KEY, role VARCHAR(32) NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_editorial_members_role ON editorial_members(role);
CREATE TABLE IF NOT EXISTS editorial_items (
  id VARCHAR(64) PRIMARY KEY, kind VARCHAR(40) NOT NULL, title VARCHAR(240) NOT NULL,
  faculty_domain VARCHAR(120) NOT NULL, program VARCHAR(160) NOT NULL, level VARCHAR(80) NOT NULL,
  semester VARCHAR(80), state VARCHAR(40) NOT NULL, risk VARCHAR(40) NOT NULL,
  rights_status VARCHAR(40) NOT NULL, rights_note TEXT NOT NULL DEFAULT '', source_fingerprint VARCHAR(128) NOT NULL DEFAULT '',
  created_by VARCHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
  current_revision_id VARCHAR(64), published_revision_id VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS ix_editorial_items_state ON editorial_items(state);
CREATE INDEX IF NOT EXISTS ix_editorial_items_scope ON editorial_items(faculty_domain,program,level,semester);
CREATE TABLE IF NOT EXISTS editorial_revisions (
  id VARCHAR(64) PRIMARY KEY, item_id VARCHAR(64) NOT NULL, revision_no INTEGER NOT NULL,
  payload_json TEXT NOT NULL, source_fingerprint VARCHAR(128) NOT NULL, ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
  prompt_version VARCHAR(80), created_by VARCHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL, note TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_editorial_revision_no ON editorial_revisions(item_id,revision_no);
CREATE TABLE IF NOT EXISTS editorial_reviews (
  id VARCHAR(64) PRIMARY KEY, item_id VARCHAR(64) NOT NULL, revision_id VARCHAR(64) NOT NULL,
  reviewer_id VARCHAR(64) NOT NULL, decision VARCHAR(40) NOT NULL, comment TEXT NOT NULL DEFAULT '', created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS editorial_sources (
  id VARCHAR(64) PRIMARY KEY, item_id VARCHAR(64) NOT NULL, filename VARCHAR(260) NOT NULL,
  mime_type VARCHAR(120), checksum_sha256 VARCHAR(64) NOT NULL, size_bytes INTEGER, storage_locator VARCHAR(512),
  ocr_confidence VARCHAR(32), human_verified BOOLEAN NOT NULL DEFAULT FALSE, imported_by VARCHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_editorial_sources_item ON editorial_sources(item_id);
CREATE INDEX IF NOT EXISTS ix_editorial_sources_checksum ON editorial_sources(checksum_sha256);

CREATE TABLE IF NOT EXISTS editorial_publications (
  id VARCHAR(64) PRIMARY KEY, item_id VARCHAR(64) NOT NULL, revision_id VARCHAR(64) NOT NULL,
  publisher_id VARCHAR(64) NOT NULL, published_at TIMESTAMPTZ NOT NULL, changelog TEXT NOT NULL DEFAULT ''
);

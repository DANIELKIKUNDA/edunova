CREATE TABLE IF NOT EXISTS candidate_upload_sessions (
 id VARCHAR(64) PRIMARY KEY, application_id VARCHAR(64) NOT NULL, requirement_code VARCHAR(80) NOT NULL,
 original_name VARCHAR(255) NOT NULL, content_type VARCHAR(120) NOT NULL, total_bytes INTEGER NOT NULL,
 total_chunks INTEGER NOT NULL, expected_sha256 VARCHAR(64), created_at TIMESTAMPTZ NOT NULL,
 expires_at TIMESTAMPTZ NOT NULL, completed_at TIMESTAMPTZ,
 CONSTRAINT ck_candidate_upload_total_bytes CHECK(total_bytes > 0 AND total_bytes <= 12582912),
 CONSTRAINT ck_candidate_upload_chunks CHECK(total_chunks > 0 AND total_chunks <= 64)
);
CREATE INDEX IF NOT EXISTS ix_candidate_upload_application ON candidate_upload_sessions(application_id,expires_at);
CREATE TABLE IF NOT EXISTS candidate_upload_chunks (
 upload_id VARCHAR(64) NOT NULL, chunk_index INTEGER NOT NULL, size_bytes INTEGER NOT NULL, sha256 VARCHAR(64) NOT NULL,
 PRIMARY KEY(upload_id,chunk_index), CONSTRAINT ck_candidate_chunk_size CHECK(size_bytes > 0 AND size_bytes <= 1048576)
);

CREATE TABLE IF NOT EXISTS candidate_applications (
 id VARCHAR(64) PRIMARY KEY, account_id VARCHAR(64) NOT NULL, institution_id VARCHAR(64) NOT NULL,
 campaign_id VARCHAR(64) NOT NULL, state VARCHAR(20) NOT NULL,
 given_names VARCHAR(160) NOT NULL, family_name VARCHAR(120) NOT NULL, birth_date VARCHAR(10),
 nationality_code VARCHAR(3), gender VARCHAR(32), address VARCHAR(500), city VARCHAR(160), country_code VARCHAR(3),
 phone_number VARCHAR(40), email VARCHAR(254), row_version INTEGER NOT NULL DEFAULT 1,
 created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, submitted_at TIMESTAMPTZ, withdrawn_at TIMESTAMPTZ,
 CONSTRAINT uq_candidate_campaign_application UNIQUE(account_id,campaign_id),
 CONSTRAINT ck_candidate_application_state CHECK(state IN ('draft','ready','submitted','withdrawn'))
);
CREATE INDEX IF NOT EXISTS ix_candidate_applications_account ON candidate_applications(account_id);
CREATE INDEX IF NOT EXISTS ix_candidate_applications_institution_state ON candidate_applications(institution_id,state);
CREATE INDEX IF NOT EXISTS ix_candidate_applications_campaign_state ON candidate_applications(campaign_id,state);
CREATE TABLE IF NOT EXISTS candidate_application_documents (
 id VARCHAR(64) PRIMARY KEY, application_id VARCHAR(64) NOT NULL, requirement_code VARCHAR(80) NOT NULL,
 original_name VARCHAR(255) NOT NULL, content_type VARCHAR(120) NOT NULL, size_bytes INTEGER NOT NULL,
 sha256 VARCHAR(64) NOT NULL, storage_key VARCHAR(500) NOT NULL UNIQUE, state VARCHAR(20) NOT NULL,
 created_at TIMESTAMPTZ NOT NULL, replaced_by VARCHAR(64),
 CONSTRAINT uq_application_document_digest UNIQUE(application_id,requirement_code,sha256),
 CONSTRAINT ck_application_document_size CHECK(size_bytes > 0),
 CONSTRAINT ck_application_document_state CHECK(state IN ('pending','uploaded','replaced'))
);
CREATE INDEX IF NOT EXISTS ix_candidate_documents_application ON candidate_application_documents(application_id);
CREATE INDEX IF NOT EXISTS ix_candidate_documents_requirement ON candidate_application_documents(application_id,requirement_code,state);

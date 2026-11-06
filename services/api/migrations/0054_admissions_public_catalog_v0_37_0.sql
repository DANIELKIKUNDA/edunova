-- EduNova v0.37.0 Phase 2 — public program catalog and admission campaigns
CREATE TABLE IF NOT EXISTS admission_campaigns (
 id VARCHAR(64) PRIMARY KEY, institution_id VARCHAR(64) NOT NULL, program_unit_id VARCHAR(64) NOT NULL,
 academic_year_id VARCHAR(64) NOT NULL, curriculum_id VARCHAR(64) NOT NULL, slug VARCHAR(120) NOT NULL,
 title VARCHAR(240) NOT NULL, summary VARCHAR(1200) NOT NULL, state VARCHAR(20) NOT NULL,
 opens_at TIMESTAMPTZ NOT NULL, closes_at TIMESTAMPTZ NOT NULL, capacity INTEGER,
 application_fee_minor INTEGER NOT NULL, currency VARCHAR(3) NOT NULL, contact_email VARCHAR(254),
 row_version INTEGER NOT NULL, created_by VARCHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL, published_at TIMESTAMPTZ,
 CONSTRAINT uq_admission_campaign_slug UNIQUE(institution_id,slug), CONSTRAINT ck_admission_capacity CHECK(capacity IS NULL OR capacity > 0), CONSTRAINT ck_admission_fee CHECK(application_fee_minor >= 0));
CREATE INDEX IF NOT EXISTS ix_admission_campaign_public ON admission_campaigns(institution_id,state,opens_at,closes_at);
CREATE INDEX IF NOT EXISTS ix_admission_campaign_program ON admission_campaigns(program_unit_id);
CREATE TABLE IF NOT EXISTS admission_requirements (
 id VARCHAR(64) PRIMARY KEY, campaign_id VARCHAR(64) NOT NULL, code VARCHAR(80) NOT NULL, label VARCHAR(240) NOT NULL,
 description VARCHAR(1000), required BOOLEAN NOT NULL, document_required BOOLEAN NOT NULL, ordinal INTEGER NOT NULL,
 CONSTRAINT uq_admission_requirement_code UNIQUE(campaign_id,code));
CREATE INDEX IF NOT EXISTS ix_admission_requirement_campaign ON admission_requirements(campaign_id,ordinal);

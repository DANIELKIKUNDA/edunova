CREATE TABLE official_document_templates (
 id VARCHAR(64) PRIMARY KEY,
 institution_id VARCHAR(64) NOT NULL,
 kind VARCHAR(40) NOT NULL,
 version VARCHAR(40) NOT NULL,
 name VARCHAR(200) NOT NULL,
 state VARCHAR(20) NOT NULL,
 created_by VARCHAR(64) NOT NULL,
 created_at TIMESTAMPTZ NOT NULL,
 published_by VARCHAR(64),
 published_at TIMESTAMPTZ,
 retired_by VARCHAR(64),
 retired_at TIMESTAMPTZ,
 CONSTRAINT uq_official_template_version UNIQUE(institution_id,kind,version)
);
CREATE INDEX ix_official_document_templates_institution_id ON official_document_templates(institution_id);
CREATE INDEX ix_official_document_templates_kind ON official_document_templates(kind);
CREATE INDEX ix_official_document_templates_state ON official_document_templates(state);
CREATE UNIQUE INDEX uq_official_document_active_template ON official_document_templates(institution_id,kind) WHERE state='published';

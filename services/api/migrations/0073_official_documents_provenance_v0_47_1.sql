ALTER TABLE official_documents ADD COLUMN IF NOT EXISTS source_evidence_hash VARCHAR(64);
ALTER TABLE official_documents ADD COLUMN IF NOT EXISTS source_jury_outcome_id VARCHAR(64);
ALTER TABLE official_documents ADD COLUMN IF NOT EXISTS replaces_document_id VARCHAR(64);
CREATE INDEX IF NOT EXISTS ix_official_documents_source_jury_outcome_id ON official_documents(source_jury_outcome_id);
CREATE INDEX IF NOT EXISTS ix_official_documents_replaces_document_id ON official_documents(replaces_document_id);

CREATE TABLE official_document_events (
 id VARCHAR(64) PRIMARY KEY,
 institution_id VARCHAR(64) NOT NULL,
 document_id VARCHAR(64) NOT NULL REFERENCES official_documents(id),
 actor_id VARCHAR(64) NOT NULL,
 event_type VARCHAR(40) NOT NULL,
 reason VARCHAR(1000),
 created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_official_document_events_institution_id ON official_document_events(institution_id);
CREATE INDEX ix_official_document_events_document_id ON official_document_events(document_id);

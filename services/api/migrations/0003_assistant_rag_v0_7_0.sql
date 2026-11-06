-- EduNova v0.7.0 — Assistant/RAG + AI credit reservations
-- LOT 6: atomic reservation of AI credits before calling an external model.
CREATE TABLE IF NOT EXISTS ai_credit_reservations (
  id varchar(64) PRIMARY KEY,
  account_id varchar(64) NOT NULL,
  credits integer NOT NULL CHECK(credits > 0),
  included_credits integer NOT NULL CHECK(included_credits >= 0),
  purchased_credits integer NOT NULL CHECK(purchased_credits >= 0),
  state varchar(32) NOT NULL,
  created_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  CHECK(included_credits + purchased_credits = credits)
);
CREATE INDEX IF NOT EXISTS ix_ai_credit_reservations_account ON ai_credit_reservations(account_id);
CREATE INDEX IF NOT EXISTS ix_ai_credit_reservations_expiry ON ai_credit_reservations(state, expires_at);

-- LOT 6 shared-course knowledge index. Personal documents are never inserted here by default.
CREATE TABLE IF NOT EXISTS knowledge_chunks (
  chunk_id varchar(128) PRIMARY KEY,
  document_id varchar(128) NOT NULL,
  course_id varchar(128) NOT NULL,
  section_title varchar(255),
  start_page integer NOT NULL CHECK(start_page > 0),
  end_page integer NOT NULL CHECK(end_page >= start_page),
  text_content text NOT NULL,
  source_fingerprint varchar(128)
);
CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_course ON knowledge_chunks(course_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_document ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_fingerprint ON knowledge_chunks(source_fingerprint);

-- PostgreSQL full-text search index for shared-course retrieval.
-- French config keeps retrieval server-side and avoids loading an entire course in API memory.
CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_fts_fr
ON knowledge_chunks USING GIN (to_tsvector('french', coalesce(section_title, '') || ' ' || text_content));

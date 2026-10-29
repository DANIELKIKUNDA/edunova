-- EduNova v0.19.3 LOT 18.3 — Question Intelligence Factory
CREATE TABLE IF NOT EXISTS assessment_question_origins (
 id VARCHAR(64) PRIMARY KEY, question_id VARCHAR(64) NOT NULL UNIQUE REFERENCES assessment_questions(id) ON DELETE CASCADE,
 source_document_id VARCHAR(128) NOT NULL, source_format VARCHAR(24) NOT NULL CHECK (source_format IN ('gift','moodle_xml','plain')), external_id VARCHAR(255),
 original_text TEXT NOT NULL, import_sha256 VARCHAR(64) NOT NULL, duplicate_fingerprint VARCHAR(64) NOT NULL UNIQUE,
 inferred_bloom VARCHAR(24) NOT NULL CHECK (inferred_bloom IN ('remember','understand','apply','analyze','evaluate','create')),
 bloom_confidence INTEGER NOT NULL CHECK (bloom_confidence BETWEEN 0 AND 100), review_status VARCHAR(24) NOT NULL DEFAULT 'imported' CHECK (review_status IN ('imported','analyzed','needs_review','approved','rejected')), recurrent_theme VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS ix_assessment_question_origins_source ON assessment_question_origins(source_document_id);
CREATE INDEX IF NOT EXISTS ix_assessment_question_origins_review ON assessment_question_origins(review_status,inferred_bloom);

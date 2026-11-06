ALTER TABLE student_success_cases ADD COLUMN source_kind VARCHAR(40);
ALTER TABLE student_success_cases ADD COLUMN source_key VARCHAR(160);
ALTER TABLE student_success_cases ADD COLUMN evidence_hash VARCHAR(64);
CREATE INDEX ix_student_success_cases_source_kind ON student_success_cases(source_kind);
CREATE INDEX ix_student_success_cases_source_key ON student_success_cases(source_key);
CREATE UNIQUE INDEX uq_student_success_cases_institution_source ON student_success_cases(institution_id,source_key) WHERE source_key IS NOT NULL;

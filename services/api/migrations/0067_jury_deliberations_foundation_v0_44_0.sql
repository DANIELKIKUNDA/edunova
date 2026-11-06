CREATE TABLE IF NOT EXISTS jury_sessions (
 id VARCHAR(64) PRIMARY KEY, institution_id VARCHAR(64) NOT NULL, cohort_id VARCHAR(64) NOT NULL,
 curriculum_id VARCHAR(64) NOT NULL, academic_year_id VARCHAR(64) NOT NULL, name VARCHAR(160) NOT NULL,
 min_credits DOUBLE PRECISION NOT NULL CHECK (min_credits >= 0 AND min_credits <= 600),
 state VARCHAR(24) NOT NULL CHECK (state IN ('draft','locked','published')),
 row_version INTEGER NOT NULL, created_by VARCHAR(64) NOT NULL,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL, updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
 CONSTRAINT uq_jury_scope_name UNIQUE(institution_id,cohort_id,academic_year_id,name)
);
CREATE INDEX IF NOT EXISTS ix_jury_sessions_institution_id ON jury_sessions(institution_id);
CREATE INDEX IF NOT EXISTS ix_jury_sessions_cohort_id ON jury_sessions(cohort_id);
CREATE TABLE IF NOT EXISTS jury_outcomes (
 id VARCHAR(64) PRIMARY KEY, session_id VARCHAR(64) NOT NULL REFERENCES jury_sessions(id),
 student_id VARCHAR(64) NOT NULL, decision VARCHAR(24) NOT NULL CHECK (decision IN ('pass','retake','deferred')),
 credits_earned DOUBLE PRECISION NOT NULL, credits_required DOUBLE PRECISION NOT NULL,
 evidence_hash VARCHAR(64) NOT NULL, decided_by VARCHAR(64) NOT NULL, reason VARCHAR(1000) NOT NULL,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL,
 CONSTRAINT uq_jury_outcome_student UNIQUE(session_id,student_id)
);
CREATE INDEX IF NOT EXISTS ix_jury_outcomes_session_id ON jury_outcomes(session_id);
CREATE INDEX IF NOT EXISTS ix_jury_outcomes_student_id ON jury_outcomes(student_id);

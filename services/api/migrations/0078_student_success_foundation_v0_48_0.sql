CREATE TABLE student_success_cases (
 id VARCHAR(64) PRIMARY KEY, institution_id VARCHAR(64) NOT NULL, student_id VARCHAR(64) NOT NULL,
 category VARCHAR(40) NOT NULL, severity VARCHAR(20) NOT NULL, description VARCHAR(2000) NOT NULL,
 state VARCHAR(20) NOT NULL, assigned_to VARCHAR(64), created_by VARCHAR(64) NOT NULL,
 created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, version INTEGER NOT NULL
);
CREATE INDEX ix_student_success_cases_institution_id ON student_success_cases(institution_id);
CREATE INDEX ix_student_success_cases_student_id ON student_success_cases(student_id);
CREATE INDEX ix_student_success_cases_state ON student_success_cases(state);
CREATE TABLE student_success_events (
 id VARCHAR(64) PRIMARY KEY, case_id VARCHAR(64) NOT NULL, actor_id VARCHAR(64) NOT NULL,
 action VARCHAR(30) NOT NULL, note VARCHAR(2000) NOT NULL, created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_student_success_events_case_id ON student_success_events(case_id);

CREATE TABLE student_success_assessments (
 id VARCHAR(64) PRIMARY KEY,
 plan_id VARCHAR(64) NOT NULL,
 case_id VARCHAR(64) NOT NULL,
 institution_id VARCHAR(64) NOT NULL,
 student_id VARCHAR(64) NOT NULL,
 failed_results INTEGER NOT NULL,
 published_results INTEGER NOT NULL,
 attendance_records INTEGER NOT NULL,
 attendance_rate FLOAT,
 outcome VARCHAR(20) NOT NULL,
 evidence_hash VARCHAR(64) NOT NULL,
 assessed_by VARCHAR(64) NOT NULL,
 created_at TIMESTAMP NOT NULL
);
CREATE INDEX ix_student_success_assessments_plan_id ON student_success_assessments(plan_id);
CREATE INDEX ix_student_success_assessments_case_id ON student_success_assessments(case_id);
CREATE INDEX ix_student_success_assessments_institution_id ON student_success_assessments(institution_id);
CREATE INDEX ix_student_success_assessments_student_id ON student_success_assessments(student_id);
CREATE INDEX ix_student_success_assessments_outcome ON student_success_assessments(outcome);

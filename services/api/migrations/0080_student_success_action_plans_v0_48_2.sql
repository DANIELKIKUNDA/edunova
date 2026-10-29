CREATE TABLE student_success_plans (
 id VARCHAR(64) PRIMARY KEY,
 case_id VARCHAR(64) NOT NULL,
 institution_id VARCHAR(64) NOT NULL,
 student_id VARCHAR(64) NOT NULL,
 objective VARCHAR(2000) NOT NULL,
 state VARCHAR(20) NOT NULL,
 target_date VARCHAR(10),
 created_by VARCHAR(64) NOT NULL,
 created_at TIMESTAMP NOT NULL,
 updated_at TIMESTAMP NOT NULL,
 version INTEGER NOT NULL
);
CREATE INDEX ix_student_success_plans_case_id ON student_success_plans(case_id);
CREATE INDEX ix_student_success_plans_institution_id ON student_success_plans(institution_id);
CREATE INDEX ix_student_success_plans_student_id ON student_success_plans(student_id);
CREATE UNIQUE INDEX uq_student_success_active_plan_per_case ON student_success_plans(case_id) WHERE state = 'active';
CREATE TABLE student_success_actions (
 id VARCHAR(64) PRIMARY KEY,
 plan_id VARCHAR(64) NOT NULL,
 title VARCHAR(500) NOT NULL,
 assigned_to VARCHAR(64) NOT NULL,
 due_date VARCHAR(10),
 state VARCHAR(20) NOT NULL,
 completion_note VARCHAR(2000),
 created_at TIMESTAMP NOT NULL,
 completed_at TIMESTAMP,
 version INTEGER NOT NULL
);
CREATE INDEX ix_student_success_actions_plan_id ON student_success_actions(plan_id);
CREATE INDEX ix_student_success_actions_assigned_to ON student_success_actions(assigned_to);
CREATE INDEX ix_student_success_actions_state ON student_success_actions(state);

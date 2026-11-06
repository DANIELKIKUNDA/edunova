-- LOT 15 hardening: exam preparation and integrity constraints
ALTER TABLE learning_study_sessions ADD CONSTRAINT ck_learning_session_state CHECK (state IN ('active','paused','completed','abandoned'));
ALTER TABLE learning_study_sessions ADD CONSTRAINT ck_learning_session_mode CHECK (mode IN ('read','quick_review','flashcards','quiz','exercises','focus','exam'));
ALTER TABLE learning_progress ADD CONSTRAINT ck_learning_mastery_stage CHECK (stage IN ('not_started','viewed','studied','practiced','assessed','mastered'));
CREATE TABLE IF NOT EXISTS learning_exam_plans (id varchar(64) PRIMARY KEY, account_id varchar(64) NOT NULL, title varchar(160) NOT NULL, exam_at timestamptz NOT NULL, daily_minutes integer NOT NULL CHECK(daily_minutes BETWEEN 10 AND 480), course_ids text NOT NULL, state varchar(24) NOT NULL CHECK(state IN ('active','completed','cancelled')), created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL, row_version integer NOT NULL DEFAULT 1 CHECK(row_version>=1));
CREATE INDEX IF NOT EXISTS ix_learning_exam_plans_account_exam ON learning_exam_plans(account_id,state,exam_at);

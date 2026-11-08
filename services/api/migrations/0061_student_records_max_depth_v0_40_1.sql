CREATE TABLE IF NOT EXISTS student_administrative_history (id VARCHAR(64) PRIMARY KEY,student_id VARCHAR(64) NOT NULL,institution_id VARCHAR(64) NOT NULL,actor_id VARCHAR(64) NOT NULL,action_type VARCHAR(64) NOT NULL,reason VARCHAR(1000) NOT NULL,before_json TEXT,after_json TEXT,created_at TIMESTAMPTZ NOT NULL);
CREATE INDEX IF NOT EXISTS ix_student_administrative_history_student_created ON student_administrative_history(student_id,created_at);
CREATE INDEX IF NOT EXISTS ix_student_administrative_history_institution_action ON student_administrative_history(institution_id,action_type);

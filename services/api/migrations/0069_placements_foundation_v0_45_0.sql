CREATE TABLE IF NOT EXISTS student_placements (
 id VARCHAR(64) PRIMARY KEY, institution_id VARCHAR(64) NOT NULL, student_id VARCHAR(64) NOT NULL,
 academic_registration_id VARCHAR(64) NOT NULL, host_name VARCHAR(200) NOT NULL,
 supervisor_account_id VARCHAR(64) NOT NULL, start_date VARCHAR(10) NOT NULL, end_date VARCHAR(10) NOT NULL,
 state VARCHAR(24) NOT NULL CHECK (state IN ('proposed','approved','active','completed','cancelled')),
 version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1), created_at TIMESTAMP WITH TIME ZONE NOT NULL,
 updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_student_placements_institution_id ON student_placements(institution_id);
CREATE INDEX IF NOT EXISTS ix_student_placements_student_id ON student_placements(student_id);
CREATE INDEX IF NOT EXISTS ix_student_placements_academic_registration_id ON student_placements(academic_registration_id);
CREATE TABLE IF NOT EXISTS student_placement_logs (
 id VARCHAR(64) PRIMARY KEY, placement_id VARCHAR(64) NOT NULL REFERENCES student_placements(id),
 student_id VARCHAR(64) NOT NULL, activity_date VARCHAR(10) NOT NULL,
 description VARCHAR(3000) NOT NULL, created_at TIMESTAMP WITH TIME ZONE NOT NULL,
 CONSTRAINT uq_placement_daily_log UNIQUE(placement_id,student_id,activity_date)
);
CREATE INDEX IF NOT EXISTS ix_student_placement_logs_placement_id ON student_placement_logs(placement_id);

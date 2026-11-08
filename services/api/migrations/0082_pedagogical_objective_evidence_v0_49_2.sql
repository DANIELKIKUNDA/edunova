CREATE TABLE IF NOT EXISTS pedagogical_learning_objectives (
 id VARCHAR(64) PRIMARY KEY, institution_id VARCHAR(64) NOT NULL, curriculum_course_id VARCHAR(64) NOT NULL,
 objective_id VARCHAR(120) NOT NULL, title VARCHAR(500) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT uq_pedintel_objective_course UNIQUE(institution_id,curriculum_course_id,objective_id));
CREATE INDEX IF NOT EXISTS ix_pedintel_objective_institution ON pedagogical_learning_objectives(institution_id);
CREATE INDEX IF NOT EXISTS ix_pedintel_objective_course ON pedagogical_learning_objectives(curriculum_course_id);
CREATE TABLE IF NOT EXISTS pedagogical_question_objectives (
 question_id VARCHAR(64) PRIMARY KEY, institution_id VARCHAR(64) NOT NULL, curriculum_course_id VARCHAR(64) NOT NULL,
 objective_id VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE INDEX IF NOT EXISTS ix_pedintel_qobj_scope ON pedagogical_question_objectives(institution_id,curriculum_course_id,objective_id);
CREATE TABLE IF NOT EXISTS pedagogical_blueprint_offerings (
 blueprint_id VARCHAR(64) PRIMARY KEY, institution_id VARCHAR(64) NOT NULL, offering_id VARCHAR(64) NOT NULL,
 curriculum_course_id VARCHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE INDEX IF NOT EXISTS ix_pedintel_blueprint_offering ON pedagogical_blueprint_offerings(institution_id,offering_id);

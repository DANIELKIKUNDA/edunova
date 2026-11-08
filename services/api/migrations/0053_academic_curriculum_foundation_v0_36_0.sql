-- EduNova v0.36.0 Phase 1 — versioned institutional academic curriculum foundation
CREATE TABLE IF NOT EXISTS academic_curriculum_versions (
 id VARCHAR(64) PRIMARY KEY, institution_id VARCHAR(64) NOT NULL, program_unit_id VARCHAR(64) NOT NULL,
 code VARCHAR(80) NOT NULL, title VARCHAR(240) NOT NULL, version INTEGER NOT NULL, state VARCHAR(20) NOT NULL,
 effective_academic_year_id VARCHAR(64) NOT NULL, source_catalog_id VARCHAR(160), row_version INTEGER NOT NULL,
 created_by VARCHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL, published_at TIMESTAMPTZ,
 CONSTRAINT uq_academic_curriculum_version UNIQUE(institution_id, program_unit_id, version));
CREATE INDEX IF NOT EXISTS ix_academic_curriculum_institution ON academic_curriculum_versions(institution_id);
CREATE INDEX IF NOT EXISTS ix_academic_curriculum_program ON academic_curriculum_versions(program_unit_id);
CREATE TABLE IF NOT EXISTS academic_curriculum_courses (
 id VARCHAR(64) PRIMARY KEY, curriculum_id VARCHAR(64) NOT NULL, semester INTEGER NOT NULL, ue_code VARCHAR(80) NOT NULL,
 code VARCHAR(80), title VARCHAR(320) NOT NULL, credits DOUBLE PRECISION, total_hours INTEGER, ordinal INTEGER NOT NULL,
 CONSTRAINT uq_academic_course_ordinal UNIQUE(curriculum_id,semester,ordinal));
CREATE INDEX IF NOT EXISTS ix_academic_course_curriculum ON academic_curriculum_courses(curriculum_id);
CREATE INDEX IF NOT EXISTS ix_academic_course_code ON academic_curriculum_courses(code);
CREATE TABLE IF NOT EXISTS academic_curriculum_prerequisites (
 id VARCHAR(64) PRIMARY KEY, curriculum_id VARCHAR(64) NOT NULL, course_id VARCHAR(64) NOT NULL,
 required_course_id VARCHAR(64) NOT NULL, minimum_status VARCHAR(24) NOT NULL,
 CONSTRAINT uq_academic_prerequisite UNIQUE(curriculum_id,course_id,required_course_id));
CREATE INDEX IF NOT EXISTS ix_academic_prerequisite_curriculum ON academic_curriculum_prerequisites(curriculum_id);

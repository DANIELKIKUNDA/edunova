CREATE TABLE IF NOT EXISTS academic_delivery_offering_links (
  id VARCHAR(64) PRIMARY KEY,
  institution_id VARCHAR(64) NOT NULL,
  offering_id VARCHAR(64) NOT NULL UNIQUE,
  curriculum_id VARCHAR(64) NOT NULL,
  curriculum_course_id VARCHAR(64) NOT NULL,
  cohort_id VARCHAR(64) NOT NULL,
  bound_by VARCHAR(64) NOT NULL,
  bound_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_academic_delivery_institution ON academic_delivery_offering_links(institution_id);
CREATE INDEX IF NOT EXISTS ix_academic_delivery_curriculum_course ON academic_delivery_offering_links(curriculum_course_id);
CREATE INDEX IF NOT EXISTS ix_academic_delivery_cohort ON academic_delivery_offering_links(cohort_id);

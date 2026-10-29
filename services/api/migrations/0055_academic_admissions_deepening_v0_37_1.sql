-- EduNova v0.37.1 — Phase 1/2 maximum-depth hardening
ALTER TABLE academic_curriculum_versions ADD COLUMN retired_at TIMESTAMPTZ;
ALTER TABLE academic_curriculum_courses ADD COLUMN cycle VARCHAR(80);
ALTER TABLE academic_curriculum_courses ADD COLUMN level VARCHAR(80);
ALTER TABLE academic_curriculum_courses ADD COLUMN ue_declared_credits DOUBLE PRECISION;
ALTER TABLE academic_curriculum_courses ADD COLUMN cmi INTEGER;
ALTER TABLE academic_curriculum_courses ADD COLUMN tp_td INTEGER;
ALTER TABLE academic_curriculum_courses ADD COLUMN tpe INTEGER;
ALTER TABLE academic_curriculum_courses ADD COLUMN percent DOUBLE PRECISION;
CREATE TABLE IF NOT EXISTS academic_curriculum_cohort_bindings (
 id VARCHAR(64) PRIMARY KEY, curriculum_id VARCHAR(64) NOT NULL, cohort_id VARCHAR(64) NOT NULL,
 bound_by VARCHAR(64) NOT NULL, bound_at TIMESTAMPTZ NOT NULL,
 CONSTRAINT uq_academic_curriculum_cohort UNIQUE(cohort_id));
CREATE INDEX IF NOT EXISTS ix_academic_curriculum_cohort_curriculum ON academic_curriculum_cohort_bindings(curriculum_id);
ALTER TABLE admission_campaigns ADD COLUMN instructions VARCHAR(4000) NOT NULL DEFAULT '';
ALTER TABLE admission_campaigns ADD COLUMN study_mode VARCHAR(20) NOT NULL DEFAULT 'on_campus';
ALTER TABLE admission_campaigns ADD COLUMN campus_label VARCHAR(240);
ALTER TABLE admission_campaigns ADD COLUMN intake_label VARCHAR(160);
ALTER TABLE admission_campaigns ADD COLUMN eligibility_summary VARCHAR(2000);
ALTER TABLE admission_campaigns ADD COLUMN archived_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_admission_campaign_year_program ON admission_campaigns(institution_id,academic_year_id,program_unit_id,state);

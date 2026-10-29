-- EduNova v0.24.2 LOT 23 Industrial Closure — operational query hardening.
CREATE INDEX IF NOT EXISTS ix_teaching_offering_course_period ON teaching_offerings(institution_id,course_id,academic_period_id,state);
CREATE INDEX IF NOT EXISTS ix_teaching_assignment_offering_role ON teaching_teacher_assignments(institution_id,offering_id,role,active);
CREATE UNIQUE INDEX IF NOT EXISTS uq_teaching_one_approved_syllabus ON teaching_syllabi(offering_id) WHERE state='approved';

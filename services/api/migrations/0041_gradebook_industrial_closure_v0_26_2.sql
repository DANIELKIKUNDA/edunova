-- EduNova v0.26.2 LOT25 FINAL Industrial Closure — deliberation/session operational hardening.
ALTER TABLE academic_gradebooks ADD CONSTRAINT ck_academic_gradebook_pass_percent CHECK (pass_percent >= 0 AND pass_percent <= 100);
ALTER TABLE academic_grade_components ADD CONSTRAINT ck_academic_grade_component_weight CHECK (weight_percent > 0 AND weight_percent <= 100);
ALTER TABLE academic_grade_components ADD CONSTRAINT ck_academic_grade_component_max_score CHECK (max_score > 0);
ALTER TABLE academic_student_marks ADD CONSTRAINT ck_academic_mark_row_version CHECK (row_version > 0);
CREATE INDEX ix_academic_gradebook_publication_scope ON academic_gradebooks(institution_id,state,offering_id);
CREATE INDEX ix_academic_marks_student_results ON academic_student_marks(institution_id,student_account_id,gradebook_id,state);

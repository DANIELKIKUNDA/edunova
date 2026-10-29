CREATE TABLE academic_published_course_results (
    id VARCHAR(64) PRIMARY KEY,
    institution_id VARCHAR(64) NOT NULL,
    student_id VARCHAR(64) NOT NULL,
    student_account_id VARCHAR(64) NOT NULL,
    course_registration_id VARCHAR(64) NOT NULL,
    curriculum_course_id VARCHAR(64) NOT NULL,
    offering_id VARCHAR(64) NOT NULL,
    gradebook_id VARCHAR(64) NOT NULL,
    percent DOUBLE PRECISION NOT NULL,
    passed BOOLEAN NOT NULL,
    evidence_hash VARCHAR(64) NOT NULL,
    published_by VARCHAR(64) NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_academic_published_course_result_registration UNIQUE (course_registration_id)
);
CREATE INDEX ix_academic_published_course_results_institution_id ON academic_published_course_results(institution_id);
CREATE INDEX ix_academic_published_course_results_student_id ON academic_published_course_results(student_id);
CREATE INDEX ix_academic_published_course_results_student_account_id ON academic_published_course_results(student_account_id);
CREATE INDEX ix_academic_published_course_results_course_registration_id ON academic_published_course_results(course_registration_id);
CREATE INDEX ix_academic_published_course_results_curriculum_course_id ON academic_published_course_results(curriculum_course_id);
CREATE INDEX ix_academic_published_course_results_offering_id ON academic_published_course_results(offering_id);
CREATE INDEX ix_academic_published_course_results_gradebook_id ON academic_published_course_results(gradebook_id);
CREATE INDEX ix_academic_published_course_results_published_at ON academic_published_course_results(published_at);

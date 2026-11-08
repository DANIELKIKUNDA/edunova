-- EduNova v0.26.1 LOT25 FINAL MAXIMAL — examination sessions, absences and deliberation locking.
ALTER TABLE academic_student_marks ADD COLUMN attendance varchar(32) NOT NULL DEFAULT 'present';
ALTER TABLE academic_student_marks ADD COLUMN note text;
ALTER TABLE academic_student_marks ADD CONSTRAINT ck_academic_mark_attendance CHECK (attendance IN ('present','absent','justified_absence','exempt'));
ALTER TABLE academic_student_marks ADD CONSTRAINT ck_academic_mark_attendance_score CHECK ((attendance='present' AND score IS NOT NULL) OR (attendance<>'present' AND score IS NULL));
CREATE TABLE academic_exam_sessions (
 id varchar(64) PRIMARY KEY, institution_id varchar(64) NOT NULL, gradebook_id varchar(64) NOT NULL REFERENCES academic_gradebooks(id),
 component_id varchar(64) NOT NULL REFERENCES academic_grade_components(id), kind varchar(24) NOT NULL CHECK(kind IN ('regular','makeup','special')),
 state varchar(24) NOT NULL CHECK(state IN ('draft','scheduled','closed','cancelled')), starts_at timestamptz NOT NULL, ends_at timestamptz NOT NULL,
 room varchar(160), instructions text, row_version integer NOT NULL CHECK(row_version>0), created_by varchar(64) NOT NULL, created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL,
 CHECK(ends_at>starts_at)
);
CREATE INDEX ix_academic_exam_sessions_scope ON academic_exam_sessions(institution_id,gradebook_id,component_id);
CREATE INDEX ix_academic_exam_sessions_schedule ON academic_exam_sessions(state,starts_at);
CREATE INDEX ix_academic_marks_deliberation ON academic_student_marks(gradebook_id,state,attendance);

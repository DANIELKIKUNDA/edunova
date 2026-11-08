-- EduNova v0.26.0 LOT25 — institutional assessments, gradebook and academic results.
CREATE TABLE academic_gradebooks (
 id varchar(64) PRIMARY KEY, institution_id varchar(64) NOT NULL, offering_id varchar(64) NOT NULL UNIQUE,
 title varchar(240) NOT NULL, state varchar(24) NOT NULL CHECK (state IN ('draft','open','locked','published','archived')),
 pass_percent double precision NOT NULL CHECK (pass_percent BETWEEN 0 AND 100), row_version integer NOT NULL CHECK (row_version > 0),
 created_by varchar(64) NOT NULL, created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL
);
CREATE INDEX ix_academic_gradebooks_institution_id ON academic_gradebooks(institution_id);
CREATE INDEX ix_academic_gradebooks_offering_id ON academic_gradebooks(offering_id);
CREATE INDEX ix_academic_gradebooks_state ON academic_gradebooks(state);
CREATE TABLE academic_grade_components (
 id varchar(64) PRIMARY KEY, institution_id varchar(64) NOT NULL, gradebook_id varchar(64) NOT NULL REFERENCES academic_gradebooks(id),
 title varchar(240) NOT NULL, kind varchar(24) NOT NULL CHECK (kind IN ('assignment','test','exam','practical','oral','other')),
 weight_percent double precision NOT NULL CHECK (weight_percent > 0 AND weight_percent <= 100), max_score double precision NOT NULL CHECK (max_score > 0),
 source_assignment_id varchar(64), position integer NOT NULL CHECK (position > 0), created_at timestamptz NOT NULL,
 CONSTRAINT uq_grade_component_position UNIQUE(gradebook_id,position)
);
CREATE INDEX ix_academic_grade_components_institution_id ON academic_grade_components(institution_id);
CREATE INDEX ix_academic_grade_components_gradebook_id ON academic_grade_components(gradebook_id);
CREATE INDEX ix_academic_grade_components_source_assignment_id ON academic_grade_components(source_assignment_id);
CREATE TABLE academic_student_marks (
 id varchar(64) PRIMARY KEY, institution_id varchar(64) NOT NULL, gradebook_id varchar(64) NOT NULL REFERENCES academic_gradebooks(id),
 component_id varchar(64) NOT NULL REFERENCES academic_grade_components(id), student_account_id varchar(64) NOT NULL,
 score double precision, state varchar(24) NOT NULL CHECK (state IN ('draft','validated','void')), source_ref varchar(128), validated_by varchar(64),
 row_version integer NOT NULL CHECK (row_version > 0), created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL,
 CONSTRAINT uq_academic_component_student UNIQUE(component_id,student_account_id), CHECK (score IS NULL OR score >= 0)
);
CREATE INDEX ix_academic_student_marks_institution_id ON academic_student_marks(institution_id);
CREATE INDEX ix_academic_student_marks_gradebook_id ON academic_student_marks(gradebook_id);
CREATE INDEX ix_academic_student_marks_component_id ON academic_student_marks(component_id);
CREATE INDEX ix_academic_student_marks_student_account_id ON academic_student_marks(student_account_id);
CREATE INDEX ix_academic_student_marks_state ON academic_student_marks(state);

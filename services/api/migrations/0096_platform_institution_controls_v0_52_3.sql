-- Platform governance state, isolated from academic/financial data.
CREATE TABLE platform_institution_controls (
 institution_id varchar(64) PRIMARY KEY,
 state varchar(24) NOT NULL CHECK (state IN ('active','suspended')),
 reason varchar(500) NOT NULL,
 row_version integer NOT NULL DEFAULT 1 CHECK (row_version >= 1),
 changed_by varchar(64) NOT NULL,
 updated_at timestamptz NOT NULL
);
CREATE INDEX idx_platform_institution_controls_state ON platform_institution_controls(state);

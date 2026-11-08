-- Canonical teaching sessions also take physical rooms. No schedule duplication.
CREATE TABLE campus_teaching_room_allocations (
    id varchar(64) PRIMARY KEY,
    institution_id varchar(64) NOT NULL,
    teaching_session_id varchar(64) NOT NULL REFERENCES teaching_sessions(id),
    resource_id varchar(64) NOT NULL REFERENCES campus_physical_resources(id),
    assigned_by varchar(64) NOT NULL,
    row_version integer NOT NULL DEFAULT 1 CHECK (row_version >= 1),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    CONSTRAINT uq_campus_room_teaching_session UNIQUE(teaching_session_id)
);
CREATE INDEX idx_campus_teaching_room_scope ON campus_teaching_room_allocations(institution_id,resource_id);

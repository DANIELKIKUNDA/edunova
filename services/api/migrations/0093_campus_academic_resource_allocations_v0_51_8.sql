-- Phase 16: Link physical resources to the EXISTING campus academic calendar.
-- No second teaching schedule. Each linked event has one physical resource.
CREATE TABLE campus_academic_resource_allocations (
    id varchar(64) PRIMARY KEY,
    institution_id varchar(64) NOT NULL,
    calendar_event_id varchar(64) NOT NULL REFERENCES campus_calendar_events(id),
    resource_id varchar(64) NOT NULL REFERENCES campus_physical_resources(id),
    assigned_by varchar(64) NOT NULL,
    row_version integer NOT NULL DEFAULT 1 CHECK (row_version >= 1),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    CONSTRAINT uq_academic_resource_calendar_event UNIQUE(calendar_event_id)
);
CREATE INDEX idx_academic_resource_allocations_scope
    ON campus_academic_resource_allocations(institution_id,resource_id);
-- Overlap is enforced inside the lock on campus_physical_resources, used by
-- both the booking and calendar allocation write paths.

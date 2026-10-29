-- Phase 16: Physical campus services; separate from digital library and teaching calendar.
CREATE TABLE IF NOT EXISTS campus_physical_resources (
    id varchar(64) PRIMARY KEY,
    institution_id varchar(64) NOT NULL,
    kind varchar(32) NOT NULL CHECK (kind IN ('room','laboratory','equipment','library_space')),
    code varchar(40) NOT NULL,
    name varchar(180) NOT NULL,
    location varchar(240) NOT NULL DEFAULT '',
    capacity integer NOT NULL CHECK (capacity BETWEEN 1 AND 5000),
    active boolean NOT NULL DEFAULT TRUE,
    row_version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    CONSTRAINT uq_physical_resource_institution_code UNIQUE (institution_id,code)
);
CREATE INDEX IF NOT EXISTS idx_physical_resource_tenant ON campus_physical_resources(institution_id,active,kind);
CREATE TABLE IF NOT EXISTS campus_resource_bookings (
    id varchar(64) PRIMARY KEY,
    institution_id varchar(64) NOT NULL,
    resource_id varchar(64) NOT NULL REFERENCES campus_physical_resources(id),
    requested_by varchar(64) NOT NULL,
    purpose varchar(240) NOT NULL,
    starts_at timestamptz NOT NULL,
    ends_at timestamptz NOT NULL,
    state varchar(24) NOT NULL CHECK (state IN ('confirmed','cancelled')),
    row_version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    CONSTRAINT ck_campus_booking_time CHECK (ends_at > starts_at)
);
CREATE INDEX IF NOT EXISTS idx_campus_booking_resource_time ON campus_resource_bookings(institution_id,resource_id,starts_at,ends_at,state);
CREATE INDEX IF NOT EXISTS idx_campus_booking_owner ON campus_resource_bookings(institution_id,requested_by,starts_at DESC);
-- PostgreSQL overlap safety uses SELECT FOR UPDATE on the parent resource row
-- within every book() transaction (not a process-local mutex).

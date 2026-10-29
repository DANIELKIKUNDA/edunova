-- Phase 16: controlled equipment/room maintenance, coupled atomically with bookings.
ALTER TABLE campus_physical_resources
  ADD COLUMN service_state varchar(24) NOT NULL DEFAULT 'available'
  CHECK (service_state IN ('available','maintenance'));
ALTER TABLE campus_resource_bookings
  ADD COLUMN cancellation_reason varchar(32) NOT NULL DEFAULT '';
CREATE TABLE campus_resource_maintenance (
  id varchar(64) PRIMARY KEY,
  institution_id varchar(64) NOT NULL,
  resource_id varchar(64) NOT NULL REFERENCES campus_physical_resources(id),
  reported_by varchar(64) NOT NULL,
  description varchar(500) NOT NULL,
  status varchar(24) NOT NULL CHECK (status IN ('reported','in_progress','resolved','dismissed')),
  resolution varchar(500) NOT NULL DEFAULT '',
  row_version integer NOT NULL CHECK (row_version >= 1),
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL
);
CREATE INDEX idx_campus_maintenance_institution ON campus_resource_maintenance(institution_id,created_at DESC);
CREATE INDEX idx_campus_maintenance_resource ON campus_resource_maintenance(resource_id);
CREATE UNIQUE INDEX uq_campus_maintenance_open_resource ON campus_resource_maintenance(resource_id)
  WHERE status IN ('reported','in_progress');

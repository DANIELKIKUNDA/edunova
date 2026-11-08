-- Phase 16: optional enrollment in EXISTING calendar events (kind = 'event').
-- The default zero disables enrollment for every historical event.
ALTER TABLE campus_calendar_events ADD COLUMN registration_capacity integer NOT NULL DEFAULT 0
  CHECK (registration_capacity BETWEEN 0 AND 5000);
CREATE TABLE campus_event_registrations (
  id varchar(64) PRIMARY KEY,
  institution_id varchar(64) NOT NULL,
  event_id varchar(64) NOT NULL REFERENCES campus_calendar_events(id),
  account_id varchar(64) NOT NULL,
  state varchar(24) NOT NULL CHECK (state IN ('registered','cancelled')),
  row_version integer NOT NULL CHECK (row_version >= 1),
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  CONSTRAINT uq_campus_event_account UNIQUE (event_id, account_id)
);
CREATE INDEX ix_campus_event_registrations_institution_id ON campus_event_registrations(institution_id);
CREATE INDEX ix_campus_event_registrations_event_id ON campus_event_registrations(event_id);
CREATE INDEX ix_campus_event_registrations_account_id ON campus_event_registrations(account_id);
-- Count active registrations without transferring cross-tenant data.
CREATE INDEX ix_campus_event_active_count ON campus_event_registrations(event_id)
  WHERE state = 'registered';

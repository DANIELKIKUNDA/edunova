-- LOT 26 maximal hardening: independent signed proximity proof.
ALTER TABLE campus_attendance_policies ADD COLUMN IF NOT EXISTS proximity_mode varchar(24) NOT NULL DEFAULT 'none';
ALTER TABLE campus_attendance_policies ADD COLUMN IF NOT EXISTS proximity_ttl_seconds integer NOT NULL DEFAULT 10;
ALTER TABLE campus_attendance_policies DROP CONSTRAINT IF EXISTS ck_attendance_proximity_mode;
ALTER TABLE campus_attendance_policies ADD CONSTRAINT ck_attendance_proximity_mode CHECK (proximity_mode IN ('none','signed_beacon'));
ALTER TABLE campus_attendance_policies DROP CONSTRAINT IF EXISTS ck_attendance_proximity_ttl;
ALTER TABLE campus_attendance_policies ADD CONSTRAINT ck_attendance_proximity_ttl CHECK (proximity_ttl_seconds BETWEEN 5 AND 30);
CREATE INDEX IF NOT EXISTS ix_attendance_session_open_window ON campus_attendance_sessions(institution_id,state,opens_at,closes_at);

-- LOT26 complete campus operations
ALTER TABLE campus_announcements ALTER COLUMN published_at DROP NOT NULL;
ALTER TABLE campus_announcements ADD COLUMN IF NOT EXISTS state varchar(24) NOT NULL DEFAULT 'published';
ALTER TABLE campus_announcements ADD COLUMN IF NOT EXISTS publish_at timestamptz;
ALTER TABLE campus_announcements ADD COLUMN IF NOT EXISTS row_version integer NOT NULL DEFAULT 1;
ALTER TABLE campus_announcements ADD COLUMN IF NOT EXISTS created_at timestamptz;
ALTER TABLE campus_announcements ADD COLUMN IF NOT EXISTS updated_at timestamptz;
UPDATE campus_announcements SET publish_at=COALESCE(publish_at,published_at),created_at=COALESCE(created_at,published_at),updated_at=COALESCE(updated_at,published_at);
ALTER TABLE campus_announcements ALTER COLUMN publish_at SET NOT NULL; ALTER TABLE campus_announcements ALTER COLUMN created_at SET NOT NULL; ALTER TABLE campus_announcements ALTER COLUMN updated_at SET NOT NULL;
CREATE TABLE IF NOT EXISTS campus_absence_requests(id varchar(64) PRIMARY KEY,institution_id varchar(64) NOT NULL,attendance_session_id varchar(64) NOT NULL,student_account_id varchar(64) NOT NULL,reason varchar(2000) NOT NULL,evidence_uri varchar(1000),state varchar(24) NOT NULL,decision_reason varchar(2000),decided_by varchar(64),row_version integer NOT NULL,created_at timestamptz NOT NULL,updated_at timestamptz NOT NULL,CONSTRAINT uq_absence_request_student_session UNIQUE(attendance_session_id,student_account_id),CONSTRAINT ck_absence_state CHECK(state IN ('pending','approved','rejected','withdrawn')));
CREATE INDEX IF NOT EXISTS ix_absence_institution_state ON campus_absence_requests(institution_id,state,created_at DESC);
CREATE TABLE IF NOT EXISTS campus_calendar_events(id varchar(64) PRIMARY KEY,institution_id varchar(64) NOT NULL,offering_id varchar(64),cohort_id varchar(64),kind varchar(24) NOT NULL,title varchar(240) NOT NULL,details varchar(4000) NOT NULL,starts_at timestamptz NOT NULL,ends_at timestamptz NOT NULL,location varchar(240),state varchar(24) NOT NULL,source_ref varchar(128),row_version integer NOT NULL,created_by varchar(64) NOT NULL,created_at timestamptz NOT NULL,updated_at timestamptz NOT NULL,CONSTRAINT ck_calendar_window CHECK(ends_at>starts_at),CONSTRAINT ck_calendar_state CHECK(state IN ('scheduled','cancelled','completed')));
CREATE INDEX IF NOT EXISTS ix_calendar_institution_time ON campus_calendar_events(institution_id,starts_at,state);
CREATE INDEX IF NOT EXISTS ix_calendar_cohort_time ON campus_calendar_events(cohort_id,starts_at) WHERE cohort_id IS NOT NULL;

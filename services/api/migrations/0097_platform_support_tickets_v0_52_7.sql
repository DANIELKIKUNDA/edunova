CREATE TABLE platform_support_tickets (
 id varchar(64) PRIMARY KEY,
 institution_id varchar(64) NOT NULL REFERENCES campus_institutions(id),
 title varchar(160) NOT NULL,
 description varchar(1500) NOT NULL,
 state varchar(24) NOT NULL CHECK (state IN ('open','in_progress','resolved','closed')),
 priority varchar(16) NOT NULL CHECK (priority IN ('low','normal','high','critical')),
 assigned_to varchar(64),
 created_by varchar(64) NOT NULL,
 updated_by varchar(64) NOT NULL,
 row_version integer NOT NULL CHECK (row_version>=1),
 created_at timestamptz NOT NULL,
 updated_at timestamptz NOT NULL
);
CREATE INDEX idx_platform_support_tickets_institution ON platform_support_tickets(institution_id);
CREATE INDEX idx_platform_support_tickets_state_created ON platform_support_tickets(state,created_at);

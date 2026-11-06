ALTER TABLE jury_sessions ADD COLUMN quorum INTEGER NOT NULL DEFAULT 1 CHECK (quorum >= 1);
CREATE TABLE IF NOT EXISTS jury_members (
 id VARCHAR(64) PRIMARY KEY, session_id VARCHAR(64) NOT NULL REFERENCES jury_sessions(id), account_id VARCHAR(64) NOT NULL,
 role VARCHAR(24) NOT NULL CHECK (role IN ('president','secretary','member')), voting BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL, CONSTRAINT uq_jury_member UNIQUE(session_id,account_id)
);
CREATE INDEX IF NOT EXISTS ix_jury_members_session_id ON jury_members(session_id);
CREATE TABLE IF NOT EXISTS jury_votes (
 id VARCHAR(64) PRIMARY KEY, session_id VARCHAR(64) NOT NULL REFERENCES jury_sessions(id), student_id VARCHAR(64) NOT NULL,
 account_id VARCHAR(64) NOT NULL, choice VARCHAR(24) NOT NULL CHECK (choice IN ('approve','reject','abstain')),
 rationale VARCHAR(1000) NOT NULL, created_at TIMESTAMP WITH TIME ZONE NOT NULL,
 CONSTRAINT uq_jury_vote UNIQUE(session_id,student_id,account_id)
);
CREATE INDEX IF NOT EXISTS ix_jury_votes_session_student ON jury_votes(session_id,student_id);
CREATE TABLE IF NOT EXISTS jury_minutes (
 id VARCHAR(64) PRIMARY KEY, session_id VARCHAR(64) NOT NULL UNIQUE REFERENCES jury_sessions(id), content_hash VARCHAR(64) NOT NULL,
 outcome_count INTEGER NOT NULL, generated_by VARCHAR(64) NOT NULL, generated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

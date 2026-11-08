-- LOT 28 v0.29.0 — Trust, Privacy, Security & Governance
-- Persistent trusted-device sessions: NULL means no arbitrary time expiry; explicit/security revocation remains authoritative.
ALTER TABLE refresh_sessions ALTER COLUMN expires_at DROP NOT NULL;
CREATE TABLE IF NOT EXISTS privacy_consents (
 id varchar(64) PRIMARY KEY, account_id varchar(64) NOT NULL, purpose varchar(128) NOT NULL,
 policy_version varchar(64) NOT NULL, state varchar(32) NOT NULL, recorded_at timestamptz NOT NULL, source varchar(32) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_privacy_consents_account_purpose ON privacy_consents(account_id,purpose,recorded_at DESC);
CREATE TABLE IF NOT EXISTS privacy_requests (
 id varchar(64) PRIMARY KEY, account_id varchar(64) NOT NULL, kind varchar(32) NOT NULL,
 state varchar(32) NOT NULL, requested_at timestamptz NOT NULL, completed_at timestamptz NULL
);
CREATE INDEX IF NOT EXISTS ix_privacy_requests_account_state ON privacy_requests(account_id,state,requested_at DESC);


CREATE TABLE IF NOT EXISTS account_mfa_credentials (
 account_id varchar(64) PRIMARY KEY, encrypted_secret text NOT NULL, enabled boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL, verified_at timestamptz NULL
);
CREATE TABLE IF NOT EXISTS institution_retention_policies (
 id varchar(64) PRIMARY KEY, institution_id varchar(64) NOT NULL, data_class varchar(64) NOT NULL, retention_days integer NOT NULL,
 policy_version varchar(64) NOT NULL, updated_at timestamptz NOT NULL, updated_by varchar(64) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_retention_institution_class ON institution_retention_policies(institution_id,data_class,updated_at DESC);
CREATE TABLE IF NOT EXISTS security_ledger (
 id varchar(64) PRIMARY KEY, actor_id varchar(64) NULL, action varchar(128) NOT NULL,
 resource_type varchar(64) NOT NULL, resource_id varchar(128) NOT NULL, occurred_at timestamptz NOT NULL,
 previous_hash varchar(64) NOT NULL, event_hash varchar(64) NOT NULL UNIQUE, metadata_json text NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS ix_security_ledger_time ON security_ledger(occurred_at,id);
CREATE INDEX IF NOT EXISTS ix_security_ledger_actor ON security_ledger(actor_id,occurred_at DESC);

-- EduNova v0.6.1 — Commerce/Identity hardening
-- v0.6.1 hardening: reversible ledger for each subscription payment.
CREATE TABLE IF NOT EXISTS subscription_grants (
  id varchar(96) PRIMARY KEY,
  payment_id varchar(64) NOT NULL UNIQUE,
  account_id varchar(64) NOT NULL,
  duration_days integer NOT NULL CHECK(duration_days > 0),
  granted_at timestamptz NOT NULL,
  starts_at timestamptz NOT NULL,
  ends_at timestamptz NOT NULL,
  reversed_at timestamptz
);
CREATE INDEX IF NOT EXISTS ix_subscription_grants_account ON subscription_grants(account_id);
CREATE INDEX IF NOT EXISTS ix_subscription_grants_end ON subscription_grants(account_id, ends_at);

CREATE TABLE IF NOT EXISTS recovery_challenges (
  id varchar(64) PRIMARY KEY,
  account_id varchar(64) NOT NULL,
  destination varchar(320) NOT NULL,
  channel varchar(16) NOT NULL,
  code_hash varchar(64) NOT NULL,
  created_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  attempts_left integer NOT NULL DEFAULT 5 CHECK(attempts_left >= 0),
  consumed_at timestamptz
);
CREATE INDEX IF NOT EXISTS ix_recovery_challenges_account ON recovery_challenges(account_id);
CREATE INDEX IF NOT EXISTS ix_recovery_challenges_expiry ON recovery_challenges(expires_at);

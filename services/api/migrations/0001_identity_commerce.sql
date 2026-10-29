-- EduNova v0.6.0 — Identity + Commerce
-- Production migration reference. Apply through the deployment migration runner before API rollout.
CREATE TABLE IF NOT EXISTS accounts (
  id varchar(64) PRIMARY KEY,
  display_name varchar(160) NOT NULL,
  password_hash varchar(512) NOT NULL,
  email varchar(320) UNIQUE,
  phone_number varchar(32) UNIQUE,
  state varchar(32) NOT NULL DEFAULT 'active',
  token_version integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_accounts_email ON accounts(email);
CREATE INDEX IF NOT EXISTS ix_accounts_phone ON accounts(phone_number);

CREATE TABLE IF NOT EXISTS refresh_sessions (
  id varchar(64) PRIMARY KEY,
  account_id varchar(64) NOT NULL,
  token_hash varchar(64) NOT NULL UNIQUE,
  created_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  device_name varchar(160),
  revoked_at timestamptz,
  replaced_by varchar(64)
);
CREATE INDEX IF NOT EXISTS ix_refresh_sessions_account ON refresh_sessions(account_id);

CREATE TABLE IF NOT EXISTS payment_intents (
  id varchar(64) PRIMARY KEY,
  account_id varchar(64) NOT NULL,
  plan_code varchar(64) NOT NULL,
  amount_cdf integer NOT NULL CHECK(amount_cdf > 0),
  phone_number varchar(32) NOT NULL,
  idempotency_key varchar(128) NOT NULL,
  state varchar(32) NOT NULL,
  provider varchar(64) NOT NULL,
  provider_reference varchar(160) UNIQUE,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  failure_reason varchar(255),
  metadata_json text NOT NULL DEFAULT '{}',
  UNIQUE(account_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS ix_payment_provider_ref ON payment_intents(provider, provider_reference);
CREATE INDEX IF NOT EXISTS ix_payment_account ON payment_intents(account_id);

CREATE TABLE IF NOT EXISTS entitlements (
  account_id varchar(64) PRIMARY KEY,
  premium_until timestamptz,
  state varchar(32) NOT NULL DEFAULT 'free',
  source_payment_id varchar(64),
  updated_at timestamptz
);

CREATE TABLE IF NOT EXISTS ai_wallets (
  account_id varchar(64) PRIMARY KEY,
  included_balance integer NOT NULL DEFAULT 0 CHECK(included_balance >= 0),
  purchased_balance integer NOT NULL DEFAULT 0 CHECK(purchased_balance >= 0),
  lifetime_granted integer NOT NULL DEFAULT 0,
  lifetime_spent integer NOT NULL DEFAULT 0,
  updated_at timestamptz
);

CREATE TABLE IF NOT EXISTS receipts (
  id varchar(64) PRIMARY KEY,
  payment_id varchar(64) NOT NULL UNIQUE,
  account_id varchar(64) NOT NULL,
  amount_cdf integer NOT NULL,
  issued_at timestamptz NOT NULL,
  description varchar(255) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_receipts_account ON receipts(account_id);

CREATE TABLE IF NOT EXISTS webhook_inbox (
  dedupe_key varchar(64) PRIMARY KEY,
  provider varchar(64) NOT NULL,
  event_id varchar(160) NOT NULL,
  received_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
  id varchar(64) PRIMARY KEY,
  actor_id varchar(64),
  action varchar(96) NOT NULL,
  entity_type varchar(64) NOT NULL,
  entity_id varchar(128),
  metadata_json text NOT NULL DEFAULT '{}',
  occurred_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_audit_actor ON audit_events(actor_id);
CREATE INDEX IF NOT EXISTS ix_audit_action_time ON audit_events(action, occurred_at);

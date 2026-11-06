-- LOT31 pilot readiness persistence. Tokens are stored hashed only.
CREATE TABLE IF NOT EXISTS pilot_invitations (
  token_hash VARCHAR(64) PRIMARY KEY,
  institution_id VARCHAR(64) NOT NULL,
  role VARCHAR(32) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_pilot_invitations_institution ON pilot_invitations(institution_id, expires_at);
CREATE TABLE IF NOT EXISTS product_funnel_events (
  id BIGSERIAL PRIMARY KEY,
  event_name VARCHAR(80) NOT NULL,
  actor_id VARCHAR(64) NULL,
  safe_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_product_funnel_events_name_time ON product_funnel_events(event_name, created_at DESC);

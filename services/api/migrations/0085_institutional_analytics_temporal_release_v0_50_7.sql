-- EduNova Phase 15: persistent first-publication guard for live aggregates.
-- Never store student IDs, learner lists, raw scores or published rates here.
CREATE TABLE IF NOT EXISTS institutional_analytics_live_releases (
  institution_id VARCHAR(64) NOT NULL,
  scope_key VARCHAR(64) NOT NULL,
  scope_json TEXT NOT NULL,
  nonce VARCHAR(48) NOT NULL,
  disclosure_hmac VARCHAR(64) NOT NULL,
  contract_version INTEGER NOT NULL DEFAULT 1,
  first_released_at TIMESTAMPTZ NOT NULL,
  CONSTRAINT pk_institutional_analytics_live_release PRIMARY KEY (institution_id,scope_key)
);
-- Intentionally no DELETE/UPDATE flow: a changed population or source stays suppressed.

CREATE TABLE IF NOT EXISTS campus_paid_orders (
  id VARCHAR(64) PRIMARY KEY,
  institution_id VARCHAR(64) NOT NULL,
  account_id VARCHAR(64) NOT NULL,
  offer_code VARCHAR(64) NOT NULL,
  offer_revision INTEGER NOT NULL,
  amount_cdf INTEGER NOT NULL CHECK (amount_cdf > 0),
  seats INTEGER NOT NULL CHECK (seats > 0),
  duration_days INTEGER NOT NULL CHECK (duration_days > 0),
  grace_days INTEGER NOT NULL CHECK (grace_days >= 0),
  idempotency_key VARCHAR(128) NOT NULL,
  payment_id VARCHAR(64) NOT NULL UNIQUE,
  license_id VARCHAR(64) UNIQUE,
  status VARCHAR(24) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  CONSTRAINT uq_campus_paid_order_idempotency UNIQUE (institution_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS ix_campus_paid_orders_institution_id ON campus_paid_orders (institution_id);

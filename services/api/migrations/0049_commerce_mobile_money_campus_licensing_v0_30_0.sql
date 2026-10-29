-- LOT 29 v0.30.0 — Commerce, Mobile Money, Campus Licensing & Revenue Sharing
CREATE TABLE IF NOT EXISTS campus_licenses(id varchar(64) PRIMARY KEY,institution_id varchar(64) NOT NULL,plan_code varchar(64) NOT NULL,state varchar(24) NOT NULL,seats integer NOT NULL CHECK(seats>0),price_cdf integer NOT NULL CHECK(price_cdf>=0),starts_at timestamptz NOT NULL,ends_at timestamptz NOT NULL,grace_until timestamptz NULL,created_by varchar(64) NOT NULL,created_at timestamptz NOT NULL);
CREATE INDEX IF NOT EXISTS ix_campus_licenses_institution_end ON campus_licenses(institution_id,ends_at DESC);
CREATE TABLE IF NOT EXISTS revenue_partners(id varchar(64) PRIMARY KEY,name varchar(160) NOT NULL,share_bps integer NOT NULL CHECK(share_bps BETWEEN 0 AND 10000),state varchar(24) NOT NULL,created_at timestamptz NOT NULL);
CREATE TABLE IF NOT EXISTS revenue_share_rules(id varchar(64) PRIMARY KEY,partner_id varchar(64) NOT NULL,institution_id varchar(64) NULL,product_code varchar(64) NULL,share_bps integer NOT NULL CHECK(share_bps BETWEEN 0 AND 10000),starts_at timestamptz NOT NULL,ends_at timestamptz NULL);
CREATE INDEX IF NOT EXISTS ix_revenue_rules_scope ON revenue_share_rules(institution_id,product_code,starts_at DESC);
CREATE TABLE IF NOT EXISTS commercial_ledger(id varchar(64) PRIMARY KEY,institution_id varchar(64) NULL,account_id varchar(64) NULL,partner_id varchar(64) NULL,kind varchar(32) NOT NULL,reference_type varchar(32) NOT NULL,reference_id varchar(96) NOT NULL,amount_cdf integer NOT NULL CHECK(amount_cdf<>0),created_at timestamptz NOT NULL,metadata_json text NOT NULL DEFAULT '{}');
CREATE INDEX IF NOT EXISTS ix_commercial_ledger_partner_time ON commercial_ledger(partner_id,created_at);
CREATE INDEX IF NOT EXISTS ix_commercial_ledger_reference ON commercial_ledger(reference_type,reference_id);
CREATE TABLE IF NOT EXISTS partner_settlements(id varchar(64) PRIMARY KEY,partner_id varchar(64) NOT NULL,period_start timestamptz NOT NULL,period_end timestamptz NOT NULL,gross_cdf integer NOT NULL,partner_cdf integer NOT NULL,platform_cdf integer NOT NULL,status varchar(24) NOT NULL,created_at timestamptz NOT NULL);
CREATE INDEX IF NOT EXISTS ix_partner_settlements_partner_period ON partner_settlements(partner_id,period_start,period_end);
-- v0.30.2 hardening: business-event and settlement-period idempotence.
CREATE UNIQUE INDEX IF NOT EXISTS uq_commercial_ledger_business_event ON commercial_ledger(kind,reference_type,reference_id,partner_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_partner_settlement_period ON partner_settlements(partner_id,period_start,period_end);

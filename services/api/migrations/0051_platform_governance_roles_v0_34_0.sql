CREATE TABLE IF NOT EXISTS platform_memberships (
 account_id VARCHAR(64) PRIMARY KEY,
 role VARCHAR(40) NOT NULL,
 active BOOLEAN NOT NULL DEFAULT TRUE,
 row_version INTEGER NOT NULL DEFAULT 1,
 granted_by VARCHAR(64) NOT NULL,
 created_at TIMESTAMPTZ NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL,
 CONSTRAINT ck_platform_role CHECK (role IN ('owner','platform_admin','finance_commercial','content_editorial','support_operator','security_audit','read_only_analyst'))
);
CREATE INDEX IF NOT EXISTS ix_platform_memberships_role ON platform_memberships(role);
CREATE INDEX IF NOT EXISTS ix_platform_memberships_active ON platform_memberships(active);

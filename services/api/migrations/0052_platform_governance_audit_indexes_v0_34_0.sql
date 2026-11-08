CREATE INDEX IF NOT EXISTS ix_platform_memberships_granted_by ON platform_memberships(granted_by);
CREATE INDEX IF NOT EXISTS ix_platform_memberships_role_active ON platform_memberships(role,active);

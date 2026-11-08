from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class PlatformRole(StrEnum):
    OWNER='owner'
    PLATFORM_ADMIN='platform_admin'
    FINANCE_COMMERCIAL='finance_commercial'
    CONTENT_EDITORIAL='content_editorial'
    SUPPORT_OPERATOR='support_operator'
    SECURITY_AUDIT='security_audit'
    READ_ONLY_ANALYST='read_only_analyst'

PERMISSIONS={
 PlatformRole.OWNER:frozenset({'platform.roles.manage','platform.dashboard.owner','platform.institutions.read','platform.institutions.manage','platform.assignments.manage','platform.commerce.read','platform.security.read','platform.content.read','platform.support.read','platform.analytics.read','platform.audit.read','platform.support.manage'}),
 PlatformRole.PLATFORM_ADMIN:frozenset({'platform.dashboard.admin','platform.institutions.read','platform.institutions.manage','platform.assignments.manage','platform.support.read','platform.support.manage','platform.analytics.read'}),
 PlatformRole.FINANCE_COMMERCIAL:frozenset({'platform.dashboard.finance','platform.commerce.read','platform.commerce.manage','platform.analytics.read'}),
 PlatformRole.CONTENT_EDITORIAL:frozenset({'platform.dashboard.editorial','platform.content.read','platform.content.manage'}),
 PlatformRole.SUPPORT_OPERATOR:frozenset({'platform.dashboard.support','platform.support.read','platform.support.manage','platform.institutions.read'}),
 PlatformRole.SECURITY_AUDIT:frozenset({'platform.dashboard.security','platform.security.read','platform.security.manage','platform.audit.read'}),
 PlatformRole.READ_ONLY_ANALYST:frozenset({'platform.dashboard.analytics','platform.analytics.read'}),
}

@dataclass(frozen=True)
class PlatformMembership:
    account_id:str
    role:PlatformRole
    active:bool
    row_version:int
    granted_by:str
    created_at:datetime
    updated_at:datetime

    @property
    def permissions(self)->frozenset[str]: return PERMISSIONS[self.role]

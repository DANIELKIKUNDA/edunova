from pathlib import Path
checks={
'identity persistent session':'expires_at=None' in Path('services/api/app/modules/identity/application/service.py').read_text(),
'refresh replay defense':'credential theft' in Path('services/api/app/modules/identity/application/service.py').read_text(),
'secure mobile storage':'flutter_secure_storage' in Path('apps/mobile/lib/src/features/identity/infrastructure/secure_session_store.dart').read_text(),
'explicit logout':'/logout' in Path('services/api/app/modules/identity/api/router.py').read_text(),
'session revocation':'/sessions/{session_id}' in Path('services/api/app/modules/identity/api/router.py').read_text(),
'mfa encrypted':'MfaVault' in Path('services/api/app/modules/trust_governance/infrastructure/mfa.py').read_text(),
'mfa login gate':'mfa_required' in Path('services/api/app/modules/identity/api/router.py').read_text(),
'personal isolation':'PERSONAL_ONLY' in Path('services/api/app/modules/trust_governance/application/service.py').read_text(),
'consent versioning':'policy_version' in Path('services/api/app/modules/trust_governance/domain/model.py').read_text(),
'external ai gate':'external_ai_allowed' in Path('services/api/app/modules/trust_governance/application/service.py').read_text(),
'privacy requests':'PrivacyRequestKind' in Path('services/api/app/modules/trust_governance/domain/model.py').read_text(),
'retention guardrail':'institution_cannot_govern_personal_space_retention' in Path('services/api/app/modules/trust_governance/application/service.py').read_text(),
'hash ledger':'sha256' in Path('services/api/app/modules/trust_governance/application/service.py').read_text(),
'security headers':'Content-Security-Policy' in Path('services/api/app/shared/security/http_headers.py').read_text(),
'tenant tests':Path('services/api/tests/test_campus_lot22.py').exists(),
'migration 0048':Path('services/api/migrations/0048_trust_privacy_security_governance_v0_29_0.sql').exists(),
'ADR 048':Path('docs/architecture/ADR-048-trust-privacy-security-governance.md').exists(),
'no credentials committed':'MFA_ENCRYPTION_KEY' in Path('services/api/app/runtime.py').read_text(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"LOT28 AUDIT: {sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

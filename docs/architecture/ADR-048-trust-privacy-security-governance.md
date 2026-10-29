# ADR-048 — LOT 28 Trust, Privacy, Security & Governance

Status: accepted for v0.29.0.

## Decisions
- Personal EduNova identity is independent from institutional tenancy. Campus never owns the student's personal account.
- `tutor_conversation`, `private_document`, `personal_study_activity`, and `personal_note` are personal-only classes and are denied to institutional access by policy.
- Trusted-device sessions are persistent: no arbitrary 30-day logout. Access JWTs remain short-lived and refresh tokens rotate. Explicit logout/revocation and critical security events remain authoritative.
- Refresh-token replay is credential-theft evidence and revokes all sessions plus access-token version.
- TOTP MFA is available; its seed is encrypted at rest. Production requires a dedicated MFA encryption key.
- Consent is append-only/versioned; withdrawal does not erase history. External AI requires current explicit consent.
- Institutional retention policy cannot govern personal-space classes.
- Security-sensitive governance actions are written to a SHA-256 chained tamper-evident ledger.
- HTTP responses receive anti-framing, nosniff, referrer, permissions and CSP headers; HSTS is emitted on HTTPS.
- Existing Campus RBAC/scoping remains the authority for tenant and academic-unit access. LOT 28 adds privacy boundaries rather than bypassing Campus authorization.

## Persistent-login UX
A trusted device stays signed in across app restarts and long periods of use. Secure storage retains rotating credentials. Users can revoke a device or logout explicitly. Password recovery/change, account disablement, refresh-token replay, or other critical security actions may invalidate sessions by design.

## OPEN-machine / deployment
Real TLS termination/HSTS verification, OS secure-keystore behavior, production PostgreSQL transaction/concurrency, Redis distributed rate limits, secrets manager/KMS rotation, SAST/DAST/dependency scan, penetration test, Android/iOS attestation, backup/restore and incident drills remain deployment certification items.

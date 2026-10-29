# ADR-050 — Production Platform & Operations

Status: accepted for LOT 30 / v0.31.0.

EduNova separates liveness from readiness, fails readiness closed when a critical dependency is unavailable, emits correlation IDs, uses structured logs, and configures bounded PostgreSQL pools/timeouts. Production containers run non-root with dropped capabilities and no-new-privileges. Redis persists AOF and has health checks. Production schema changes are explicit migrations; runtime auto-create remains forbidden in production.

CI is a release gate: compilation, full backend tests, LOT30 audit and container build must pass. Production deployment requires environment approval and external secrets. Backup artifacts are PostgreSQL custom dumps with SHA-256 sidecars; restore is destructive and requires an explicit confirmation token.

OPEN-machine/cloud: real TLS/DNS/reverse proxy, cloud/VPS network policy, KMS/secret rotation, PostgreSQL/Redis load and failover, object-storage backup, real restore drill, SAST/DAST/SCA platform integrations and incident exercises.

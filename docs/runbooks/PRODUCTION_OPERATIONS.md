# EduNova production operations runbook

## Deploy
Run CI. Take a verified backup. Apply migrations with `scripts/migrate_production.sh`. Roll out API/workers. Admit traffic only when `/v1/operations/ready` returns 200. Keep the previous image digest available for rollback.

## Rollback
Stop traffic to the unhealthy revision. Roll back application image first. Database rollback is never improvised: prefer forward-fix migrations; restore only after an incident decision and verified backup.

## Backup / restore
Use `backup_postgres.sh`; retain the `.dump` and `.sha256` together outside the application host. Restore only in a controlled maintenance window using `CONFIRM_RESTORE=RESTORE_EDUNOVA restore_postgres.sh <dump>`. Verify application readiness and business invariants after restore.

## Dependency incident
A database or Redis failure must make readiness fail. Remove unhealthy instances from traffic. Do not repeatedly restart workers without inspecting failed/retried jobs and idempotency keys.

## Security incident / secrets
Revoke compromised credentials at the provider, rotate environment/KMS values, restart affected workloads, revoke relevant EduNova sessions if identity material is affected, preserve audit evidence, and document timeline/actions.

## Mobile Money incident
Pause provider initiation if callbacks cannot be trusted. Preserve webhook inbox/ledger. Reconcile provider records before manual financial correction; corrections are compensating ledger events, never destructive edits.

## LOT30 v0.31.2 hardening
- `/v1/operations/metrics` exposes low-cardinality Prometheus HTTP counters/latency totals.
- Production Compose runs both ingestion and Content Factory workers.
- `backup_object_storage.sh` / `restore_object_storage.sh` support S3-compatible storage (AWS S3/R2/MinIO) with SHA-256 verification and explicit restore confirmation.
- `security.yml` gates dependencies with pip-audit and container images with Trivy.
- Tagged releases pass tests/audit, require the GitHub `production` environment approval, deploy over SSH, and automatically roll back the application revision if readiness does not recover.
- Database schema rollback remains forward-fix by policy: destructive automatic migration rollback is forbidden.

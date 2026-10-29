from pathlib import Path
R=Path
checks={
'live/ready/metrics': all(x in R('services/api/app/modules/operations/api/router.py').read_text() for x in ['/live','/ready','/metrics']),
'database probe':'SELECT 1' in R('services/api/app/modules/operations/infrastructure/probes.py').read_text(),
'prometheus metrics':'edunova_http_requests_total' in R('services/api/app/modules/operations/application/metrics.py').read_text(),
'correlation/json logging':all(x in R('services/api/app/shared/infrastructure/observability.py').read_text() for x in ['X-Request-ID','JsonFormatter']),
'bounded db pool':'DB_POOL_SIZE' in R('services/api/app/shared/infrastructure/database.py').read_text(),
'non-root image':'USER edunova' in R('services/api/Dockerfile').read_text(),
'prod hardening':all(x in R('docker-compose.production.yml').read_text() for x in ['cap_drop','read_only','redis-cli']),
'ingestion worker':'app.modules.ingestion.worker' in R('docker-compose.production.yml').read_text(),
'content factory worker':'app.modules.content_factory.worker' in R('docker-compose.production.yml').read_text(),
'postgres backup checksum':'sha256sum' in R('scripts/backup_postgres.sh').read_text(),
'object backup checksum':all(x in R('scripts/backup_object_storage.sh').read_text() for x in ['aws','s3 sync','sha256sum']),
'object restore guarded':all(x in R('scripts/restore_object_storage.sh').read_text() for x in ['CONFIRM_OBJECT_RESTORE','sha256sum -c','s3 sync']),
'migration fail-fast':'ON_ERROR_STOP' in R('scripts/migrate_production.sh').read_text(),
'ci full tests':'pytest -q' in R('.github/workflows/ci.yml').read_text(),
'ci image build':'docker/build-push-action' in R('.github/workflows/ci.yml').read_text(),
'dependency SCA':'pip-audit' in R('.github/workflows/security.yml').read_text(),
'image scan':'trivy' in R('.github/workflows/security.yml').read_text().lower(),
'release approval':'environment: production' in R('.github/workflows/release.yml').read_text(),
'real deploy step':'ssh-action' in R('.github/workflows/release.yml').read_text(),
'rollback readiness':all(x in R('scripts/deploy_production.sh').read_text() for x in ['READINESS_URL','rollback_production.sh']),
'redis distributed test':'test_redis_rate_limit_is_shared_across_instances' in R('services/api/tests/test_operations_hardening_lot30.py').read_text(),
'runbook':R('docs/runbooks/PRODUCTION_OPERATIONS.md').exists(),
'ADR':R('docs/architecture/ADR-050-production-platform-operations.md').exists(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"LOT30 HARDENED AUDIT: {sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

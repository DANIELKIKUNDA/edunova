from historical_audit_contracts import release_at_least
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def text(path): return (ROOT/path).read_text(encoding='utf-8')
def has(path,*needles):
    try: t=text(path)
    except FileNotFoundError: return False
    return all(n in t for n in needles)
def exists(path): return (ROOT/path).exists()
def ck(name, ok): checks.append((name,bool(ok)))

ck('api_version_0_13_1',release_at_least(ROOT, 'api', '0.13.1'))
ck('mobile_version_0_13_1',release_at_least(ROOT, 'mobile', '0.13.1+19'))
ck('admin_version_0_13_1',release_at_least(ROOT, 'admin', '0.13.1+19'))
ck('migration_0009',exists('services/api/migrations/0009_ingestion_industrielle_v0_13_0.sql'))
ck('migration_tables',has('services/api/migrations/0009_ingestion_industrielle_v0_13_0.sql','ingestion_batches','ingestion_documents','ingestion_jobs','ingestion_results','artifact_sha256','pipeline_version'))
ck('domain_batch_document_job_result',has('services/api/app/modules/ingestion/domain/model.py','class IngestionBatch','class IngestionDocument','class IngestionJob','class IngestionResult'))
ck('manifest_immutable',has('services/api/app/modules/ingestion/application/service.py','batch_manifest_frozen','manifest_sha256'))
ck('idempotency_upload',has('services/api/app/modules/ingestion/application/service.py','find_document_by_idempotency','idempotency_key'))
ck('contextual_dedup',has('services/api/app/modules/ingestion/application/service.py','duplicate_source_different_context','previous_batch.defaults==batch.defaults'))
ck('multi_page_bundle',has('services/api/app/modules/ingestion/application/service.py','def add_image_bundle','save_all=True','append_images=rest'))
ck('signature_preflight',has('services/api/app/modules/ingestion/application/preflight.py','application/pdf','image/jpeg','image/png','image/webp'))
ck('encrypted_pdf_rejected',has('services/api/app/modules/ingestion/application/preflight.py','encrypted_pdf_not_supported'))
ck('size_page_pixel_limits',has('services/api/app/modules/ingestion/application/preflight.py','max_file_bytes','max_pdf_pages','max_image_pixels'))
ck('clamav_adapter',has('services/api/app/modules/ingestion/infrastructure/security.py','ClamAV','INSTREAM'))
ck('prod_antivirus_fail_closed',has('services/api/app/runtime.py','ClamAvTcpScanner','DisabledMalwareScanner'))
ck('local_staging_safe',has('services/api/app/modules/ingestion/infrastructure/storage.py','LocalStagingStorage','invalid_storage_key'))
ck('s3_staging',has('services/api/app/modules/ingestion/infrastructure/storage.py','S3StagingStorage','boto3'))
ck('worker_separate',exists('services/api/app/modules/ingestion/worker.py') and has('docker-compose.yml','ingestion-worker','app.modules.ingestion.worker'))
ck('lease_heartbeat',has('services/api/app/modules/ingestion/worker.py','heartbeat','recover_expired_leases_internal'))
ck('retry_dead_letter',has('services/api/app/modules/ingestion/application/service.py','DEAD_LETTER','retry_dead_letter','retry_scheduled'))
ck('artifact_content_addressed',has('services/api/app/modules/ingestion/application/service.py','artifact_sha','pipeline_version','document-engine-v1'))
ck('studio_projection',has('services/api/app/modules/ingestion/infrastructure/editorial_bridge.py','create_from_processed_document','create_item','add_revision','add_source'))
ck('ocr_human_verification',has('services/api/app/modules/ingestion/application/service.py','needs_verification'))
ck('dashboard_metrics',has('services/api/app/modules/ingestion/application/service.py','def dashboard','def metrics'))
ck('preview_ocr',has('services/api/app/modules/ingestion/application/service.py','def preview'))
ck('audit_actions',has('services/api/app/modules/ingestion/application/service.py','ingestion.batch.created','ingestion.document.accepted','ingestion.job.dead_letter'))
ck('router_dashboard',has('services/api/app/modules/ingestion/api/router.py','/dashboard'))
ck('router_bundle',has('services/api/app/modules/ingestion/api/router.py','image-bundles'))
ck('router_preview',has('services/api/app/modules/ingestion/api/router.py','/preview'))
ck('router_retry',has('services/api/app/modules/ingestion/api/router.py','/retry'))
ck('upload_size_stream_guard',has('services/api/app/modules/ingestion/api/router.py','INGESTION_MAX_FILE_BYTES') or has('services/api/app/modules/ingestion/api/router.py','max_file_bytes'))
ck('rate_limit_ingestion',has('services/api/app/modules/ingestion/api/router.py','rate'))
ck('docker_tesseract_fr_en',has('services/api/Dockerfile','tesseract-ocr-fra','tesseract-ocr-eng'))
ck('compose_clamav_profile',has('docker-compose.yml','clamav','production-security'))
ck('env_controls',has('.env.example','INGESTION_MAX_BATCH_FILES','INGESTION_MAX_FILE_BYTES','INGESTION_LEASE_SECONDS','INGESTION_PENDING_SLA_MINUTES','INGESTION_SYSTEM_ACCOUNT_ID'))
ck('studio_file_picker',has('apps/admin/pubspec.yaml','file_picker:'))
ck('studio_ingestion_section',has('apps/admin/lib/src/features/editorial/editorial_shell.dart','IngestionPage','Ingestion'))
ck('studio_responsive_nav',has('apps/admin/lib/src/features/editorial/editorial_shell.dart','NavigationRail','NavigationDestination'))
ck('studio_dashboard',has('apps/admin/lib/src/features/editorial/ingestion_page.dart','Ingestion industrielle','Jobs en attente','Dead-letter'))
ck('studio_multi_upload',has('apps/admin/lib/src/features/editorial/ingestion_page.dart','Ajouter des fichiers','Regrouper des photos'))
ck('studio_manifest_progress',has('apps/admin/lib/src/features/editorial/ingestion_page.dart','Manifest figé','LinearProgressIndicator'))
ck('studio_ocr_quality',has('apps/admin/lib/src/features/editorial/ingestion_page.dart','OCR','Vérification humaine requise'))
ck('studio_preview',has('apps/admin/lib/src/features/editorial/ingestion_page.dart','Aperçu OCR / extraction','Questions détectées'))
ck('studio_role_aware',has('apps/admin/lib/src/features/editorial/ingestion_page.dart','canEdit'))
ck('api_client_idempotency',has('apps/admin/lib/src/features/editorial/editorial_api.dart','Idempotency-Key','uploadIngestionFile','uploadImageBundle'))
ck('tests_ingestion_present',len(list((ROOT/'services/api/tests/ingestion').glob('test_*.py')))>=4)
ck('docs_architecture',exists('docs/architecture/ADR-013-industrial-ingestion-pipeline.md'))
ck('docs_runbook',exists('docs/LOT12_RUNBOOK_v0.13.1.md'))
ck('docs_acceptance',exists('docs/certification/LOT12_ACCEPTANCE_v0.13.1.md'))
ck('docs_machine_cert',exists('docs/LOT12_MACHINE_CERTIFICATION_v0.13.1.md'))
# Structural delimiter balance for changed/admin Dart files; not a replacement for flutter analyze.
for path in [ROOT/'apps/admin/lib/src/features/editorial/ingestion_page.dart',ROOT/'apps/admin/lib/src/features/editorial/editorial_api.dart',ROOT/'apps/admin/lib/src/features/editorial/editorial_shell.dart']:
    t=path.read_text(encoding='utf-8')
    stripped=re.sub(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"",'',t)
    for op,cl in [('(',')'),('[',']'),('{','}')]: ck(f'dart_balance:{path.name}:{op}',stripped.count(op)==stripped.count(cl))
# No unresolved stubs in new LOT12 core.
bad=[]
for base in [ROOT/'services/api/app/modules/ingestion',ROOT/'apps/admin/lib/src/features/editorial/ingestion_page.dart']:
    paths=[base] if base.is_file() else list(base.rglob('*'))
    for p in paths:
        if p.is_file() and p.suffix in {'.py','.dart'}:
            t=p.read_text(encoding='utf-8',errors='ignore')
            if re.search(r'\b(TODO|FIXME|NotImplementedError)\b',t): bad.append(str(p.relative_to(ROOT)))
ck('no_lot12_core_stubs',not bad)
ck('migration_0010_manifest_integrity',exists('services/api/migrations/0010_ingestion_manifest_integrity_v0_13_1.sql'))
ck('manifest_snapshot_persisted',has('services/api/app/modules/ingestion/application/service.py','manifest_json = json.dumps','verify_manifest'))
ck('manifest_verify_api',has('services/api/app/modules/ingestion/api/router.py','/manifest/verify'))
ck('bulk_dead_letter_retry',has('services/api/app/modules/ingestion/application/service.py','retry_dead_letters_bulk'))
failed=[n for n,v in checks if not v]
for n,v in checks: print(('PASS' if v else 'FAIL'),n)
print(f'RESULT {sum(v for _,v in checks)}/{len(checks)} PASS')
if failed:
    print('FAILED:',', '.join(failed)); sys.exit(1)

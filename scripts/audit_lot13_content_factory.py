from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'content_factory_domain':r/'services/api/app/modules/content_factory/domain/model.py',
'factory_service':r/'services/api/app/modules/content_factory/application/service.py',
'sql_repository':r/'services/api/app/modules/content_factory/infrastructure/sqlalchemy_repo.py',
'api_router':r/'services/api/app/modules/content_factory/api/router.py',
'worker':r/'services/api/app/modules/content_factory/worker.py',
'migration_0011':r/'services/api/migrations/0011_content_factory_v0_14_0.sql',
'adr_014':r/'docs/architecture/ADR-014-content-factory-industrial-pipeline.md',
'lot13_doc':r/'docs/LOT13_CONTENT_FACTORY_v0.14.0.md',
'acceptance':r/'docs/certification/LOT13_ACCEPTANCE_v0.14.0.md',
'admin_page':r/'apps/admin/lib/src/features/editorial/content_factory_page.dart',
'tests':r/'services/api/tests/content_factory/test_content_factory.py',
}
texts='\n'.join(p.read_text(errors='ignore') for p in checks.values() if p.exists())
semantic=['READY_FOR_REVIEW','provenance_complete','source_sha256','content_sha256','quote_sha256','summary_express','summary_detailed','flashcard','quiz','rag_chunk','quality_score','requested_assets_json','content_factory_runs','human_review_required','CONTENT_FACTORY_SYSTEM_ACCOUNT_ID']
results=[(k,p.exists()) for k,p in checks.items()]+[(f'invariant:{x}',x.lower() in texts.lower()) for x in semantic]
for k,v in results: print(('PASS' if v else 'FAIL'),k)
passed=sum(v for _,v in results); print(f'{passed}/{len(results)} PASS')
raise SystemExit(0 if passed==len(results) else 1)

from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'publication module':(r/'services/api/app/modules/publication/application/service.py').exists(),
'migration 0012':(r/'services/api/migrations/0012_academic_publication_v0_15_0.sql').exists(),
'router mounted':'publication_router' in (r/'services/api/app/main.py').read_text(),
'preflight':'publication_preflight_failed' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'published exact revision':'published_revision_matches' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'rights gate':'rights_clear' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'scheduled':'SCHEDULED' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'rollout':'rollout_percentage' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'premium':'premium_required' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'offline':'offline_allowed' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'snapshot sha':'sha256' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'withdraw':'withdraw' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'audit':'publication.release.published' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'UI center':(r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').exists(),
'UI filters':'ChoiceChip' in (r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').read_text(),
'branding':'From Volcano Tech' in (r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').read_text(),
'ADR':(r/'docs/architecture/ADR-015-academic-publishing-distribution.md').exists(),
'acceptance':(r/'docs/certification/LOT14_ACCEPTANCE_v0.15.0.md').exists(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

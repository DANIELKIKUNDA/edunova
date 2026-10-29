from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'api 0.15.1':'version="0.15.1"' in (r/'services/api/app/main.py').read_text(),
'admin 0.15.1+24':'0.15.1+24' in (r/'apps/admin/pubspec.yaml').read_text(),
'mobile 0.15.1+24':'0.15.1+24' in (r/'apps/mobile/pubspec.yaml').read_text(),
'migration 0013':(r/'services/api/migrations/0013_publication_hardening_v0_15_1.sql').exists(),
'rollout DB check':'ck_publication_rollout_percentage' in (r/'services/api/migrations/0013_publication_hardening_v0_15_1.sql').read_text(),
'due scheduler index':'ix_publication_due_scheduler' in (r/'services/api/migrations/0013_publication_hardening_v0_15_1.sql').read_text(),
'publish re-preflight':'publication_preflight_failed_at_publish' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'placement contract':'invalid_academic_placement' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'audience contract':'audience_rollout_requires_audience' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'schedule contract':'scheduled_at_must_be_future' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'snapshot verify service':'verify_snapshot' in (r/'services/api/app/modules/publication/application/service.py').read_text(),
'snapshot verify route':"/{release_id}/verify" in (r/'services/api/app/modules/publication/api/router.py').read_text(),
'ui search':"Rechercher une release" in (r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').read_text(),
'ui master detail':'_Inspector' in (r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').read_text(),
'ui mobile sheet':'showModalBottomSheet' in (r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').read_text(),
'ui integrity':'Snapshot vérifié' in (r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').read_text(),
'ui empty state':'_EmptyState' in (r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').read_text(),
'ui error state':'_ErrorCard' in (r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').read_text(),
'branding':'From Volcano Tech' in (r/'apps/admin/lib/src/features/editorial/publication_center_page.dart').read_text(),
'ADR 016':(r/'docs/architecture/ADR-016-publication-boundary-integrity.md').exists(),
'final doc':(r/'docs/LOT14_FINAL_HARDENING_v0.15.1.md').exists(),
'publication tests':'test_release_contract_rejects_unsafe_distribution' in (r/'services/api/tests/publication/test_publication_service.py').read_text(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

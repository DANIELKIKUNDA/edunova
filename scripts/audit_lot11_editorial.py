from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
'workflow states':'IN_REVIEW' in (root/'services/api/app/modules/editorial/domain/model.py').read_text(),
'four eyes':'four_eyes_required' in (root/'services/api/app/modules/editorial/application/service.py').read_text(),
'rights gate':'distribution_rights_not_cleared' in (root/'services/api/app/modules/editorial/application/service.py').read_text(),
'ocr human verify':'ocr_source_requires_human_verification' in (root/'services/api/app/modules/editorial/application/service.py').read_text(),
'prompt provenance':'ai_prompt_version_required' in (root/'services/api/app/modules/editorial/application/service.py').read_text(),
'library projector':(root/'services/api/app/modules/editorial/infrastructure/library_projector.py').exists(),
'migration 0007':(root/'services/api/migrations/0007_editorial_governance_v0_12_0.sql').exists(),
'admin app':(root/'apps/admin/lib/src/features/editorial/editorial_shell.dart').exists(),
'responsive rail':'NavigationRail' in (root/'apps/admin/lib/src/features/editorial/editorial_shell.dart').read_text(),
'editorial api route':'/v1/editorial' in (root/'services/api/app/main.py').read_text(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
raise SystemExit(0 if all(checks.values()) else 1)

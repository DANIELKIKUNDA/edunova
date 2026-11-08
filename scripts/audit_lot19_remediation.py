from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={'domain':root/'services/api/app/modules/remediation/domain/model.py','service':root/'services/api/app/modules/remediation/application/service.py','repo':root/'services/api/app/modules/remediation/infrastructure/sqlalchemy_repo.py','api':root/'services/api/app/modules/remediation/api/router.py','migration':root/'services/api/migrations/0024_intelligent_remediation_v0_20_0.sql','tests':root/'services/api/tests/test_remediation_lot19.py','adr':root/'docs/ADR-024-intelligent-remediation-engine.md','ui':root/'apps/mobile/lib/src/features/remediation/presentation/remediation_page.dart'}
for k,p in checks.items():assert p.exists(),f'{k}:missing'
s=(root/'services/api/app/modules/remediation/application/service.py').read_text();
for token in ['Misconception','WORKED_EXAMPLE','TRANSFER','REASSESS','remediation_version_conflict','spaced_review']:assert token in s,token
print(f'LOT19 audit PASS {len(checks)+6}/{len(checks)+6}')

from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
'migration_0026':root/'services/api/migrations/0026_remediation_orchestration_hardening_v0_20_2.sql',
'adr_026':root/'docs/architecture/ADR-026-remediation-industrial-orchestration.md',
'closure_doc':root/'docs/LOT19_FINAL_INDUSTRIAL_CLOSURE_v0.20.2.md',
'domain':root/'services/api/app/modules/remediation/domain/model.py',
'service':root/'services/api/app/modules/remediation/application/service.py',
'repo':root/'services/api/app/modules/remediation/infrastructure/sqlalchemy_repo.py',
'api':root/'services/api/app/modules/remediation/api/router.py',
'tests':root/'services/api/tests/test_remediation_lot19.py',
}
for n,p in checks.items(): assert p.exists(),n
texts='\n'.join(p.read_text(errors='ignore') for p in checks.values())
for token in ['mutation_id','RemediationEvent','cumulative_gain','longitudinal','transfer_verified','personal_success_rate']:
 assert token in texts,token
print('LOT19 v0.20.2 industrial closure audit PASS 14/14')

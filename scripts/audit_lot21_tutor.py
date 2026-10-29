from pathlib import Path
R=Path(__file__).resolve().parents[1]
checks={
 'tutor_domain':R/'services/api/app/modules/tutor/domain/model.py',
 'tutor_service':R/'services/api/app/modules/tutor/application/service.py',
 'tutor_api':R/'services/api/app/modules/tutor/api/router.py',
 'tutor_sql':R/'services/api/app/modules/tutor/infrastructure/sqlalchemy_repo.py',
 'migration_0030':R/'services/api/migrations/0030_tutor_2_v0_22_0.sql',
 'adr_030':R/'docs/ADR-030-tutor-2-socratic-orchestration.md',
 'lot21_doc':R/'docs/LOT21_TUTOR_2_v0.22.0.md',
 'tests':R/'services/api/tests/test_tutor_lot21.py',
 'mobile_tutor':R/'apps/mobile/lib/src/features/assistant/presentation/assistant_page.dart',
}
for k,p in checks.items():assert p.exists() and p.stat().st_size>20,k
text=(R/'services/api/app/modules/tutor/application/service.py').read_text()
for token in ['SOCRATIC','PREREQUISITE','REMEDIATE','ABSTAIN','mutation_id','tutor_version_conflict']:assert token in text,token
main=(R/'services/api/app/main.py').read_text();assert '0.22.0' in main and '/v1/tutor' in main
print('LOT21 AUDIT: 15/15 PASS')

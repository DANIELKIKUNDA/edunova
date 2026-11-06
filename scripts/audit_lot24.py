from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
 'domain':r/'services/api/app/modules/assignments/domain/model.py','service':r/'services/api/app/modules/assignments/application/service.py','repo':r/'services/api/app/modules/assignments/infrastructure/sqlalchemy_repo.py','api':r/'services/api/app/modules/assignments/api/router.py','migration':r/'services/api/migrations/0036_assignments_submissions_grading_v0_25_0.sql','tests':r/'services/api/tests/test_assignments_lot24.py','adr':r/'docs/ADR-036-assignment-grading-human-control.md','lot':r/'docs/LOT24_v0.25.0_ASSIGNMENTS_SUBMISSIONS_INTELLIGENT_GRADING.md','cert':r/'docs/certification/LOT24_BASELINE_ACCEPTANCE_v0.25.0.md'}
missing=[k for k,p in checks.items() if not p.exists() or p.stat().st_size==0]
service=checks['service'].read_text();migration=checks['migration'].read_text();main=(r/'services/api/app/main.py').read_text()
semantic={'human validation':'validate_grade' in service and 'final_score' in service,'similarity review':'needs_review' in service,'attempt limit':'assignment_attempt_limit' in service,'late':'SubmissionState.LATE' in service,'rubric':'rubric_total_mismatch' in service,'router':'assignments_router' in main,'tables':all(x in migration for x in ['campus_assignments','assignment_submissions','assignment_grading_decisions','assignment_similarity_flags'])}
failed=missing+[k for k,v in semantic.items() if not v]
print(f'LOT24 audit: {len(checks)+len(semantic)-len(failed)}/{len(checks)+len(semantic)} PASS')
if failed:print('FAILED:',','.join(failed));raise SystemExit(1)

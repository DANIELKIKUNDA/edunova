from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'0034 migration':r/'services/api/migrations/0034_teaching_delivery_maximal_v0_24_1.sql',
'ADR-034':r/'docs/ADR-034-teaching-syllabus-progress-resource-history.md',
'LOT23 maximal':r/'docs/LOT23_FINAL_MAXIMAL_v0.24.1.md',
'domain':r/'services/api/app/modules/teaching/domain/model.py',
'service':r/'services/api/app/modules/teaching/application/service.py',
'api':r/'services/api/app/modules/teaching/api/router.py',
'tests':r/'services/api/tests/test_teaching_lot23.py'}
for k,p in checks.items():
 assert p.exists(),k
texts='\n'.join(p.read_text(errors='ignore') for p in checks.values() if p.suffix in {'.py','.md','.sql'})
for token in ['Syllabus','SyllabusTopic','ResourceRevision','concept_refs','teaching_progress','approval_forbidden']:
 assert token in texts,token
print(f'LOT23 MAXIMAL AUDIT PASS — {len(checks)+6}/13 checks')

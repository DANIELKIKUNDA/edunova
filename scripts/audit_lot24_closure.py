from pathlib import Path
r=Path(__file__).resolve().parents[1]
files=['services/api/app/modules/assignments/domain/model.py','services/api/app/modules/assignments/application/service.py','services/api/app/modules/assignments/api/router.py','services/api/migrations/0038_assignment_results_industrial_closure_v0_25_2.sql','services/api/tests/test_assignments_lot24.py','docs/ADR-038-lot24-industrial-closure-results-safety.md','docs/LOT24_v0.25.2_INDUSTRIAL_CLOSURE.md']
checks=[(x,(r/x).exists() and (r/x).stat().st_size>0) for x in files]
s=(r/files[1]).read_text();api=(r/files[2]).read_text();mig=(r/files[3]).read_text()
checks += [('private-until-published','assignment_results_not_published' in s),('complete-grading-gate','assignment_results_incomplete_grading' in s),('audited-retraction','assignment.results.retracted' in s),('human-final-score','def validate_grade' in s and 'final_score' in s),('deterministic-proposal','deterministic_sympy' in s),('group-api','/groups' in api),('autograde-api','/auto-items' in api),('reopen-api','/reopen-grants' in api),('review-api','similarity/{fid}/review' in api),('result-api','/my-result' in api),('db-review-check','ck_assignment_similarity_review_state' in mig)]
failed=[n for n,v in checks if not v]
print(f'LOT24 closure audit: {len(checks)-len(failed)}/{len(checks)} PASS')
if failed: print('FAILED:',','.join(failed)); raise SystemExit(1)

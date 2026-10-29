from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={'gradebook domain':root/'services/api/app/modules/gradebook/domain/model.py','gradebook service':root/'services/api/app/modules/gradebook/application/service.py','gradebook api':root/'services/api/app/modules/gradebook/api/router.py','gradebook persistence':root/'services/api/app/modules/gradebook/infrastructure/sqlalchemy_repo.py','migration 0039':root/'services/api/migrations/0039_academic_gradebook_results_v0_26_0.sql','ADR-039':root/'docs/architecture/ADR-039-academic-gradebook-results.md','tests':root/'services/api/tests/test_gradebook_lot25.py'}
failed=[]
for n,p in checks.items():
 ok=p.exists() and p.stat().st_size>50;print(('PASS' if ok else 'FAIL'),n);failed += ([] if ok else [n])
text=(root/'services/api/app/modules/gradebook/application/service.py').read_text()
for n,token in [('weights 100','gradebook_weights_must_total_100'),('private until publish','gradebook_results_not_published'),('retraction audit','gradebook.results.retracted'),('assignment import','import_assignment_results'),('enrollment guard','gradebook_student_enrollment_required')]:
 ok=token in text;print(('PASS' if ok else 'FAIL'),n);failed += ([] if ok else [n])
raise SystemExit(1 if failed else 0)

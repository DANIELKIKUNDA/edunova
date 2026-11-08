from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks=['services/api/app/modules/teaching/domain/model.py','services/api/app/modules/teaching/application/service.py','services/api/app/modules/teaching/infrastructure/sqlalchemy_repo.py','services/api/app/modules/teaching/api/router.py','services/api/migrations/0033_teaching_course_delivery_v0_24_0.sql','services/api/tests/test_teaching_lot23.py','docs/ADR-033-teaching-course-delivery.md']
for x in checks:assert (r/x).exists(),x
s=(r/'services/api/app/modules/teaching/application/service.py').read_text();
for token in ['teaching_membership_required','teaching_offering_write_forbidden','teaching_concurrent_modification','PUBLISHED','source_revision']:assert token in s,token
print('LOT23 AUDIT PASS',len(checks)+5,'checks')

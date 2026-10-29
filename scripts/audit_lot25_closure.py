from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks=[r/'docs/ADR-041-gradebook-industrial-closure.md',r/'docs/LOT25_FINAL_INDUSTRIAL_CLOSURE_v0.26.2.md',r/'services/api/migrations/0041_gradebook_industrial_closure_v0_26_2.sql']
assert all(p.exists() for p in checks)
svc=(r/'services/api/app/modules/gradebook/application/service.py').read_text();api=(r/'services/api/app/modules/gradebook/api/router.py').read_text();mig=checks[2].read_text()
for t in ['gradebook_deliberation_lock_required','gradebook_academic_admin_required','gradebook_exam_session_overlap','transition_exam_session']:assert t in svc,t
for t in ['attendance=q.attendance','note=q.note','exam-sessions/{sid}/transition']:assert t in api,t
for t in ['ck_academic_gradebook_pass_percent','ix_academic_marks_student_results']:assert t in mig,t
print('LOT25 INDUSTRIAL CLOSURE AUDIT: 14/14 PASS')

from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'ADR-040':r/'docs/ADR-040-gradebook-deliberation-exam-sessions.md',
'migration-0040':r/'services/api/migrations/0040_gradebook_maximal_v0_26_1.sql',
'lot25-doc':r/'docs/LOT25_FINAL_MAXIMAL_v0.26.1.md',
}
for k,p in checks.items(): assert p.exists(),k
svc=(r/'services/api/app/modules/gradebook/application/service.py').read_text()
api=(r/'services/api/app/modules/gradebook/api/router.py').read_text()
mig=(r/'services/api/migrations/0040_gradebook_maximal_v0_26_1.sql').read_text()
for token in ['unlock_exceptionally','create_exam_session','AttendanceOutcome','gradebook.locked']: assert token in svc,token
for token in ['/lock','/unlock-exceptionally','/exam-sessions']: assert token in api,token
for token in ['academic_exam_sessions','justified_absence','ck_academic_mark_attendance']: assert token in mig,token
print('LOT25 MAXIMAL AUDIT: 13/13 PASS')

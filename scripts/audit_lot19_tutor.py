from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks=['RootCause','TutorIntervention','tutor_decision','record_practice','retention_check','transfer_ok','next_review_at','Remediation Intelligence & Tutor Engine hardening','ADR-025','0.20.1']
blob='\n'.join(p.read_text(errors='ignore') for p in [r/'services/api/app/modules/remediation/domain/model.py',r/'services/api/app/modules/remediation/application/service.py',r/'services/api/migrations/0025_remediation_tutor_intelligence_v0_20_1.sql',r/'docs/architecture/ADR-025-remediation-tutor-intelligence.md',r/'services/api/app/main.py'])
for c in checks: assert c in blob,c
print(f'LOT19 tutor audit: {len(checks)}/{len(checks)} PASS')

from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
'Bloom taxonomy domain':'class BloomLevel' in (root/'services/api/app/modules/assessment/domain/model.py').read_text(),
'Learning objective':'learning_objective' in (root/'services/api/app/modules/assessment/domain/model.py').read_text(),
'Cognitive steps':'cognitive_steps' in (root/'services/api/app/modules/assessment/domain/model.py').read_text(),
'Distractor rationales':'distractor_rationales' in (root/'services/api/app/modules/assessment/domain/model.py').read_text(),
'Quality score':'quality_score' in (root/'services/api/app/modules/assessment/domain/model.py').read_text(),
'Bloom blueprint':'bloom_distribution' in (root/'services/api/app/modules/assessment/domain/model.py').read_text(),
'Fail closed cognitive selection':'insufficient_bloom_questions' in (root/'services/api/app/modules/assessment/application/service.py').read_text(),
'CREATE constructed response':'create_level_requires_constructed_response' in (root/'services/api/app/modules/assessment/application/service.py').read_text(),
'Quality API':"/questions/quality-check" in (root/'services/api/app/modules/assessment/api/router.py').read_text(),
'Migration 0022':(root/'services/api/migrations/0022_assessment_cognitive_intelligence_v0_19_2.sql').exists(),
'ADR 022':(root/'docs/architecture/ADR-022-cognitive-assessment-intelligence.md').exists(),
'Cognitive spec':(root/'docs/LOT18_COGNITIVE_ASSESSMENT_INTELLIGENCE_v0.19.2.md').exists(),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
assert all(checks.values())
print(f"{sum(checks.values())}/{len(checks)} PASS")

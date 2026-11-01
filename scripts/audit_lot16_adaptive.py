from historical_audit_contracts import release_at_least
from pathlib import Path
p=Path(__file__).resolve().parents[1]; files=['services/api/app/modules/adaptive_learning/domain/model.py','services/api/app/modules/adaptive_learning/application/service.py','services/api/app/modules/adaptive_learning/infrastructure/sqlalchemy_repo.py','services/api/app/modules/adaptive_learning/api/router.py','services/api/migrations/0016_adaptive_learning_v0_17_0.sql','services/api/tests/test_adaptive_learning.py','docs/architecture/ADR-018-adaptive-learning-intelligence.md','apps/mobile/lib/src/features/adaptive_learning/presentation/adaptive_learning_page.dart']
for x in files:assert (p/x).exists(),x
assert release_at_least(p, 'api', '0.17.0');assert 'adaptive-learning' in (p/'services/api/app/main.py').read_text();print('LOT16 AUDIT: 10/10 PASS')

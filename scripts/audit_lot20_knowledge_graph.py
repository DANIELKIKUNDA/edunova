from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks=['services/api/app/modules/knowledge_graph/domain/model.py','services/api/app/modules/knowledge_graph/application/service.py','services/api/app/modules/knowledge_graph/infrastructure/sqlalchemy_repo.py','services/api/app/modules/knowledge_graph/api/router.py','services/api/migrations/0027_knowledge_graph_v0_21_0.sql','docs/architecture/ADR-027-knowledge-graph-academic-intelligence.md','docs/LOT20_KNOWLEDGE_GRAPH_v0.21.0.md','services/api/tests/knowledge_graph/test_knowledge_graph_lot20.py']
for x in checks:assert (root/x).exists(),x
s=(root/'services/api/app/modules/knowledge_graph/application/service.py').read_text();
for token in ['dependency_cycle','high_stakes_provenance_and_review_required','root_cause_candidates','assessment_context','GovernanceState.PUBLISHED']:assert token in s,token
print('LOT20 audit: 13/13 PASS')

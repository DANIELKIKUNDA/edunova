from pathlib import Path
r=Path(__file__).resolve().parents[1]
files=['services/api/migrations/0028_knowledge_graph_extraction_governance_v0_21_1.sql','docs/architecture/ADR-028-knowledge-graph-extraction-governance.md','docs/LOT20_KNOWLEDGE_GRAPH_EXTRACTION_v0.21.1.md','apps/admin/lib/src/features/knowledge_graph/presentation/knowledge_graph_studio_page.dart']
for f in files:assert (r/f).exists(),f
s=(r/'services/api/app/modules/knowledge_graph/application/service.py').read_text()
for x in ['start_extraction','source_locator_required','independent_review_required','high_stakes_confidence_too_low','learning_sequence','graph_health','SOURCE_EXTRACTION']:assert x in s,x
m=(r/'services/api/migrations/0028_knowledge_graph_extraction_governance_v0_21_1.sql').read_text()
for x in ['source_sha256','fingerprint','confidence BETWEEN 0 AND 100','uq_kg_extract_fingerprint_batch']:assert x in m,x
print('LOT20 v0.21.1 audit: 15/15 PASS')

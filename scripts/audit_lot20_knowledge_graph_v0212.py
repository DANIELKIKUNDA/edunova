from pathlib import Path
r=Path(__file__).resolve().parents[1]
files=['services/api/migrations/0029_knowledge_graph_snapshot_impact_v0_21_2.sql','docs/architecture/ADR-029-knowledge-graph-snapshots-impact-closure.md','docs/LOT20_INDUSTRIAL_CLOSURE_v0.21.2.md','docs/certification/LOT20_ACCEPTANCE_v0.21.2.md']
for f in files: assert (r/f).exists(),f
s=(r/'services/api/app/modules/knowledge_graph/application/service.py').read_text()
for x in ['create_snapshot','content_sha256','impact_analysis','retire_relation','graph_version_conflict','prerequisite_plan','GovernanceState.PUBLISHED']: assert x in s,x
m=(r/'services/api/migrations/0029_knowledge_graph_snapshot_impact_v0_21_2.sql').read_text()
for x in ['knowledge_graph_snapshots','knowledge_graph_impacts','content_sha256','affected_concept_id','CHECK(distance>=0)']: assert x in m,x
print('LOT20 v0.21.2 audit: 16/16 PASS')

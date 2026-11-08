-- LOT 27 v0.28.2 FINAL — institutional pedagogical intelligence query paths
CREATE INDEX IF NOT EXISTS ix_assessment_blueprints_course ON assessment_blueprints(course_id);
CREATE INDEX IF NOT EXISTS ix_assessment_attempts_blueprint_state ON assessment_attempts(blueprint_id, state);
CREATE INDEX IF NOT EXISTS ix_knowledge_graph_nodes_tenant_course_state ON knowledge_graph_nodes(tenant_id, course_id, state);
CREATE INDEX IF NOT EXISTS ix_knowledge_graph_relations_tenant_state ON knowledge_graph_relations(tenant_id, state);

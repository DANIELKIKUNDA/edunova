CREATE TABLE knowledge_graph_snapshots (id varchar(64) PRIMARY KEY, tenant_id varchar(64) NOT NULL, sequence integer NOT NULL CHECK(sequence>0), content_sha256 varchar(64) NOT NULL CHECK(length(content_sha256)=64), node_count integer NOT NULL CHECK(node_count>=0), relation_count integer NOT NULL CHECK(relation_count>=0), reason varchar(255) NOT NULL, created_by varchar(64) NOT NULL, state varchar(24) NOT NULL CHECK(state IN ('active','superseded')), created_at timestamptz NOT NULL);
CREATE UNIQUE INDEX uq_kg_snapshot_tenant_sequence ON knowledge_graph_snapshots(tenant_id,sequence);
CREATE INDEX ix_kg_snapshot_tenant_hash ON knowledge_graph_snapshots(tenant_id,content_sha256);
CREATE INDEX ix_kg_snapshot_active ON knowledge_graph_snapshots(tenant_id,state,sequence DESC);
CREATE TABLE knowledge_graph_impacts (id varchar(64) PRIMARY KEY, tenant_id varchar(64) NOT NULL, relation_id varchar(64) NOT NULL REFERENCES knowledge_graph_relations(id), change_kind varchar(32) NOT NULL, affected_concept_id varchar(64) NOT NULL, distance integer NOT NULL CHECK(distance>=0), path text NOT NULL, snapshot_id varchar(64) REFERENCES knowledge_graph_snapshots(id), created_at timestamptz NOT NULL);
CREATE INDEX ix_kg_impact_relation ON knowledge_graph_impacts(tenant_id,relation_id);
CREATE INDEX ix_kg_impact_concept ON knowledge_graph_impacts(tenant_id,affected_concept_id,distance);

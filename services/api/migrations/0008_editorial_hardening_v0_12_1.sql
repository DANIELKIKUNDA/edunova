ALTER TABLE editorial_items ADD COLUMN IF NOT EXISTS row_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE editorial_reviews ADD COLUMN IF NOT EXISTS checklist_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE editorial_reviews ADD COLUMN IF NOT EXISTS quality_score INTEGER;

CREATE TABLE IF NOT EXISTS editorial_assignments (
  id VARCHAR(64) PRIMARY KEY,
  item_id VARCHAR(64) NOT NULL,
  stage VARCHAR(32) NOT NULL,
  assignee_id VARCHAR(64) NOT NULL,
  assigned_by VARCHAR(64) NOT NULL,
  due_at TIMESTAMPTZ,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_editorial_assignments_item ON editorial_assignments(item_id);
CREATE INDEX IF NOT EXISTS ix_editorial_assignments_assignee ON editorial_assignments(assignee_id, active);
CREATE INDEX IF NOT EXISTS ix_editorial_assignments_due ON editorial_assignments(due_at, active);
CREATE INDEX IF NOT EXISTS ix_editorial_items_row_version ON editorial_items(row_version);

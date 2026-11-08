-- LOT 17 final hardening: defensive indexes and state invariants.
CREATE INDEX IF NOT EXISTS ix_study_plan_due_execution ON study_plan_items(account_id,state,starts_at) WHERE state='planned';
CREATE INDEX IF NOT EXISTS ix_study_plan_replanning ON study_plan_items(account_id,plan_date,priority DESC) WHERE state='planned';
-- A plan item is an execution instruction; impossible temporal spans are rejected at DB level by 0018.
-- row_version remains the concurrency token for offline/multi-device reconciliation.

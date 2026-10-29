-- EduNova v0.15.1 — LOT 14 publication hardening
-- Defensive database constraints complement application validation.
ALTER TABLE publication_releases
  ADD CONSTRAINT ck_publication_rollout_percentage CHECK (rollout_percentage BETWEEN 1 AND 100),
  ADD CONSTRAINT ck_publication_all_rollout CHECK (rollout_mode <> 'all' OR rollout_percentage = 100),
  ADD CONSTRAINT ck_publication_state CHECK (state IN ('draft','scheduled','published','withdrawn'));
CREATE INDEX IF NOT EXISTS ix_publication_due_scheduler ON publication_releases (scheduled_at, id) WHERE state='scheduled';
CREATE INDEX IF NOT EXISTS ix_publication_catalog_scope ON publication_releases (state, published_at DESC);

-- EduNova 0.49.12: freeze the canonical automatic-sum grading INPUTS at grading time.
-- Existing versions 0 and 1 remain unchanged; NEVER reconstruct snapshots for past grades.
ALTER TABLE assessment_results ADD COLUMN grading_snapshot JSONB;
ALTER TABLE assessment_results ADD COLUMN grading_snapshot_sha256 VARCHAR(64);
-- 0083 created an anonymous version CHECK. PostgreSQL generates a constraint
-- name which is not a stable API; discover that one check by its definition.
DO $$
DECLARE check_name text;
BEGIN
  FOR check_name IN
    SELECT c.conname FROM pg_constraint c
    WHERE c.conrelid='assessment_results'::regclass AND c.contype='c'
      AND pg_get_constraintdef(c.oid) LIKE '%grading_contract_version%'
  LOOP
    EXECUTE format('ALTER TABLE assessment_results DROP CONSTRAINT %I', check_name);
  END LOOP;
END $$;
ALTER TABLE assessment_results
  ADD CONSTRAINT assessment_results_snapshot_contract_check
  CHECK (
     (grading_contract_version IN (0,1) AND grading_snapshot IS NULL AND grading_snapshot_sha256 IS NULL)
     OR
     (grading_contract_version = 2 AND grading_snapshot IS NOT NULL
      AND grading_snapshot_sha256 ~ '^[a-f0-9]{64}$')
  );
COMMENT ON COLUMN assessment_results.grading_snapshot IS
  'Version-2 immutable grading-time inputs (course, blueprint, question IDs and points, pass threshold); no retrospective reconstruction.';
COMMENT ON COLUMN assessment_results.grading_snapshot_sha256 IS
  'Unkeyed canonical snapshot SHA-256 for consistency checks; not a tamper-proof signature.';

-- EduNova 0.49.11: preserve legacy incompleteness; certify only new auto-sum grades.
-- Historical rows get version 0 and MUST NOT be bulk-promoted to version 1.
ALTER TABLE assessment_results
    ADD COLUMN grading_contract_version INTEGER NOT NULL DEFAULT 0
    CHECK (grading_contract_version IN (0, 1));
COMMENT ON COLUMN assessment_results.grading_contract_version IS
    '0 = historical/unverified breakdown; 1 = complete deterministic auto-sum verified at write. No inference of manual adjustments.';

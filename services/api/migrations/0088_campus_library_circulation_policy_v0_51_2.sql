-- Phase 16 v0.51.2: Renewal state for physical lending; historical loans retain zero renewals.
ALTER TABLE campus_library_loans ADD COLUMN renewal_count integer NOT NULL DEFAULT 0;
ALTER TABLE campus_library_loans ADD COLUMN last_renewed_at timestamptz;
ALTER TABLE campus_library_loans ADD CONSTRAINT ck_campus_library_loan_renewals
    CHECK (renewal_count >= 0 AND renewal_count <= 2);
CREATE INDEX IF NOT EXISTS ix_campus_library_active_borrower_due
    ON campus_library_loans(institution_id, borrower_account_id, due_at)
    WHERE returned_at IS NULL;

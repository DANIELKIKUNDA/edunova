-- Phase 16 v0.51.3: Opt-in institution-specific library policy.
-- With no row, the application returns the v0.51.2 defaults (21,3,2,14).
CREATE TABLE IF NOT EXISTS campus_library_policies (
    institution_id varchar(64) PRIMARY KEY,
    loan_days integer NOT NULL CHECK (loan_days BETWEEN 1 AND 60),
    max_open_loans integer NOT NULL CHECK (max_open_loans BETWEEN 1 AND 10),
    max_renewals integer NOT NULL CHECK (max_renewals BETWEEN 0 AND 2),
    renewal_days integer NOT NULL CHECK (renewal_days BETWEEN 1 AND 30),
    row_version integer NOT NULL CHECK (row_version >= 1),
    updated_at timestamptz NOT NULL
);
-- No student data in this table. Transactions use per-institution PostgreSQL
-- advisory locks to serialise updates with checkouts and renewals.

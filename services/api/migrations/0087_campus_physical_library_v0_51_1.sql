-- Phase 16: Physical library; separate from library_courses (digital library).
CREATE TABLE IF NOT EXISTS campus_library_books (
    id varchar(64) PRIMARY KEY,
    institution_id varchar(64) NOT NULL,
    title varchar(240) NOT NULL,
    author varchar(180) NOT NULL,
    isbn varchar(32) NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL,
    CONSTRAINT uq_campus_library_books_tenant_id UNIQUE (institution_id, id)
);
CREATE INDEX IF NOT EXISTS ix_campus_library_books_institution_id ON campus_library_books(institution_id);
CREATE TABLE IF NOT EXISTS campus_library_copies (
    id varchar(64) PRIMARY KEY,
    institution_id varchar(64) NOT NULL,
    book_id varchar(64) NOT NULL,
    barcode varchar(64) NOT NULL,
    active boolean NOT NULL DEFAULT TRUE,
    created_at timestamptz NOT NULL,
    CONSTRAINT uq_campus_library_copies_tenant_id UNIQUE (institution_id, id),
    CONSTRAINT uq_campus_library_copy_barcode UNIQUE (institution_id, barcode),
    CONSTRAINT fk_campus_library_copy_book_tenant FOREIGN KEY (institution_id,book_id)
        REFERENCES campus_library_books(institution_id,id)
);
CREATE INDEX IF NOT EXISTS ix_campus_library_copies_institution_id ON campus_library_copies(institution_id);
CREATE TABLE IF NOT EXISTS campus_library_loans (
    id varchar(64) PRIMARY KEY,
    institution_id varchar(64) NOT NULL,
    copy_id varchar(64) NOT NULL,
    borrower_account_id varchar(64) NOT NULL,
    borrowed_at timestamptz NOT NULL,
    due_at timestamptz NOT NULL,
    returned_at timestamptz,
    row_version integer NOT NULL DEFAULT 1 CHECK (row_version >= 1),
    CONSTRAINT ck_campus_library_due_after_borrow CHECK (due_at > borrowed_at),
    CONSTRAINT ck_campus_library_return_after_borrow CHECK (returned_at IS NULL OR returned_at >= borrowed_at),
    CONSTRAINT fk_campus_library_loan_copy_tenant FOREIGN KEY (institution_id,copy_id)
        REFERENCES campus_library_copies(institution_id,id)
);
CREATE INDEX IF NOT EXISTS ix_campus_library_loans_institution_id ON campus_library_loans(institution_id);
CREATE INDEX IF NOT EXISTS ix_campus_library_borrower ON campus_library_loans(institution_id,borrower_account_id,borrowed_at);
-- Database-level guarantee: no two open loans for a single physical copy.
CREATE UNIQUE INDEX IF NOT EXISTS uq_campus_library_one_open_loan
    ON campus_library_loans(institution_id,copy_id) WHERE returned_at IS NULL;

-- v0.51.4: physical copy loss/damage resolution, preserving historic records.
ALTER TABLE campus_library_copies ADD COLUMN condition varchar(16) NOT NULL DEFAULT 'serviceable';
ALTER TABLE campus_library_copies ADD COLUMN row_version integer NOT NULL DEFAULT 1;
-- Preserve unknown previously-inactive items as withdrawn (do not invent damage).
UPDATE campus_library_copies SET condition = 'withdrawn' WHERE active = FALSE;
ALTER TABLE campus_library_copies ADD CONSTRAINT ck_campus_library_copy_condition
  CHECK (condition IN ('serviceable','damaged','lost','withdrawn'));
ALTER TABLE campus_library_copies ADD CONSTRAINT ck_campus_library_copy_condition_active
  CHECK ((condition = 'serviceable' AND active = TRUE) OR
         (condition <> 'serviceable' AND active = FALSE));
ALTER TABLE campus_library_copies ADD CONSTRAINT ck_campus_library_copy_version
  CHECK (row_version >= 1);
ALTER TABLE campus_library_loans ADD COLUMN closure_reason varchar(16);
-- Existing returns are valid historical returns; open loans remain NULL.
UPDATE campus_library_loans SET closure_reason = 'returned' WHERE returned_at IS NOT NULL;
ALTER TABLE campus_library_loans ADD CONSTRAINT ck_campus_library_loan_resolution
  CHECK ((returned_at IS NULL AND closure_reason IS NULL) OR
         (returned_at IS NOT NULL AND closure_reason IN ('returned','damaged','lost')));

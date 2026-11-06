-- Phase 16: voluntary Alumni identity and institution-curated opportunities.
CREATE TABLE campus_alumni_profiles (
    id varchar(64) PRIMARY KEY,
    institution_id varchar(64) NOT NULL,
    account_id varchar(64) NOT NULL,
    display_name varchar(160) NOT NULL,
    program_name varchar(160) NOT NULL,
    graduation_year integer NOT NULL CHECK(graduation_year BETWEEN 1950 AND 2100),
    headline varchar(240) NOT NULL DEFAULT '',
    visible boolean NOT NULL DEFAULT FALSE,
    status varchar(24) NOT NULL CHECK(status IN ('pending','verified','rejected')),
    verification_reference varchar(160) NOT NULL DEFAULT '',
    reviewed_by varchar(64),
    row_version integer NOT NULL DEFAULT 1 CHECK(row_version >= 1),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    CONSTRAINT uq_alumni_tenant_account UNIQUE(institution_id,account_id)
);
CREATE INDEX idx_alumni_directory ON campus_alumni_profiles(institution_id,status,visible);
CREATE TABLE campus_alumni_opportunities (
    id varchar(64) PRIMARY KEY,
    institution_id varchar(64) NOT NULL,
    posted_by varchar(64) NOT NULL,
    title varchar(180) NOT NULL,
    description varchar(2000) NOT NULL,
    application_url varchar(500) NOT NULL DEFAULT '',
    state varchar(24) NOT NULL CHECK(state IN ('published','withdrawn')),
    row_version integer NOT NULL DEFAULT 1 CHECK(row_version >= 1),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);
CREATE INDEX idx_alumni_opportunity_scope ON campus_alumni_opportunities(institution_id,state,created_at);

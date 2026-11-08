-- EduNova v0.8.0 — LOT 7 Synchronisation multi-appareils + bibliothèque partagée

CREATE TABLE IF NOT EXISTS sync_devices (
  id varchar(128) PRIMARY KEY,
  account_id varchar(64) NOT NULL,
  name varchar(160) NOT NULL,
  platform varchar(32) NOT NULL,
  app_version varchar(40) NOT NULL,
  created_at timestamptz NOT NULL,
  last_seen_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sync_devices_account_id ON sync_devices(account_id);
CREATE INDEX IF NOT EXISTS ix_sync_devices_last_seen_at ON sync_devices(last_seen_at);

CREATE TABLE IF NOT EXISTS sync_records (
  id bigserial PRIMARY KEY,
  account_id varchar(64) NOT NULL,
  entity_type varchar(64) NOT NULL,
  entity_id varchar(128) NOT NULL,
  version integer NOT NULL DEFAULT 1,
  payload_json text NOT NULL DEFAULT '{}',
  deleted boolean NOT NULL DEFAULT false,
  client_modified_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  last_device_id varchar(128) NOT NULL,
  server_seq bigint NOT NULL DEFAULT 0,
  CONSTRAINT uq_sync_record_owner_entity UNIQUE(account_id, entity_type, entity_id)
);
CREATE INDEX IF NOT EXISTS ix_sync_records_account_type ON sync_records(account_id, entity_type);
CREATE INDEX IF NOT EXISTS ix_sync_records_server_seq ON sync_records(server_seq);

CREATE TABLE IF NOT EXISTS sync_changes (
  seq bigserial PRIMARY KEY,
  account_id varchar(64) NOT NULL,
  entity_type varchar(64) NOT NULL,
  entity_id varchar(128) NOT NULL,
  version integer NOT NULL,
  payload_json text NOT NULL,
  deleted boolean NOT NULL,
  changed_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sync_changes_owner_seq ON sync_changes(account_id, seq);

CREATE TABLE IF NOT EXISTS sync_mutation_inbox (
  id bigserial PRIMARY KEY,
  account_id varchar(64) NOT NULL,
  mutation_id varchar(128) NOT NULL,
  disposition varchar(32) NOT NULL,
  result_json text NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL,
  CONSTRAINT uq_sync_mutation_owner_id UNIQUE(account_id, mutation_id)
);
CREATE INDEX IF NOT EXISTS ix_sync_mutation_owner ON sync_mutation_inbox(account_id, mutation_id);

CREATE TABLE IF NOT EXISTS library_courses (
  id varchar(64) PRIMARY KEY,
  faculty_domain varchar(120) NOT NULL,
  program varchar(160) NOT NULL,
  level varchar(80) NOT NULL,
  semester varchar(80) NOT NULL,
  title varchar(240) NOT NULL,
  slug varchar(240) NOT NULL UNIQUE,
  description text NOT NULL DEFAULT '',
  publication_state varchar(32) NOT NULL DEFAULT 'draft',
  premium_required boolean NOT NULL DEFAULT false,
  active_version_id varchar(64),
  updated_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_library_course_path ON library_courses(faculty_domain, program, level, semester);
CREATE INDEX IF NOT EXISTS ix_library_course_state ON library_courses(publication_state);

CREATE TABLE IF NOT EXISTS library_course_versions (
  id varchar(64) PRIMARY KEY,
  course_id varchar(64) NOT NULL,
  label varchar(120) NOT NULL,
  academic_year varchar(40),
  source_fingerprint varchar(128) NOT NULL,
  changelog text NOT NULL DEFAULT '',
  published_at timestamptz
);
CREATE INDEX IF NOT EXISTS ix_library_versions_course ON library_course_versions(course_id);
CREATE INDEX IF NOT EXISTS ix_library_versions_fingerprint ON library_course_versions(source_fingerprint);

CREATE TABLE IF NOT EXISTS library_resources (
  id varchar(64) PRIMARY KEY,
  version_id varchar(64) NOT NULL,
  kind varchar(48) NOT NULL,
  title varchar(240) NOT NULL,
  mime_type varchar(120),
  size_bytes integer,
  checksum_sha256 varchar(64),
  premium_required boolean NOT NULL DEFAULT false,
  offline_allowed boolean NOT NULL DEFAULT false,
  sort_order integer NOT NULL DEFAULT 0,
  storage_locator varchar(512)
);
CREATE INDEX IF NOT EXISTS ix_library_resources_version ON library_resources(version_id);
CREATE INDEX IF NOT EXISTS ix_library_resources_kind ON library_resources(kind);

CREATE TABLE IF NOT EXISTS engagement_preferences (
  account_id VARCHAR(64) PRIMARY KEY,
  quiet_start_minute INTEGER NOT NULL DEFAULT 1320,
  quiet_end_minute INTEGER NOT NULL DEFAULT 420,
  max_daily_notifications INTEGER NOT NULL DEFAULT 2,
  assessment_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  study_plan_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  flashcards_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  streak_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  content_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  preferred_study_minute INTEGER NOT NULL DEFAULT 1140,
  timezone_offset_minutes INTEGER NOT NULL DEFAULT 0,
  daily_goal_minutes INTEGER NOT NULL DEFAULT 30
);
CREATE TABLE IF NOT EXISTS engagement_notification_intents (
  id VARCHAR(64) PRIMARY KEY, account_id VARCHAR(64) NOT NULL, dedupe_key VARCHAR(180) NOT NULL,
  category VARCHAR(40) NOT NULL, channel VARCHAR(20) NOT NULL, title VARCHAR(240) NOT NULL,
  body TEXT NOT NULL, deep_link VARCHAR(512) NOT NULL DEFAULT '', fire_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL, priority INTEGER NOT NULL DEFAULT 50, status VARCHAR(24) NOT NULL DEFAULT 'planned', delivered_at TIMESTAMPTZ NULL, created_at TIMESTAMPTZ NOT NULL,
  CONSTRAINT uq_engagement_dedupe UNIQUE(account_id,dedupe_key)
);
CREATE INDEX IF NOT EXISTS ix_engagement_notification_due ON engagement_notification_intents(account_id,fire_at);
CREATE TABLE IF NOT EXISTS engagement_days (
  id BIGSERIAL PRIMARY KEY, account_id VARCHAR(64) NOT NULL, day_key VARCHAR(10) NOT NULL,
  active_minutes INTEGER NOT NULL DEFAULT 0, completed_tasks INTEGER NOT NULL DEFAULT 0,
  quiz_questions INTEGER NOT NULL DEFAULT 0, flashcards_reviewed INTEGER NOT NULL DEFAULT 0,
  CONSTRAINT uq_engagement_day UNIQUE(account_id,day_key)
);
CREATE TABLE IF NOT EXISTS engagement_push_devices (
  id BIGSERIAL PRIMARY KEY, account_id VARCHAR(64) NOT NULL, device_id VARCHAR(80) NOT NULL,
  platform VARCHAR(20) NOT NULL, token TEXT NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_engagement_push_device UNIQUE(account_id,device_id)
);

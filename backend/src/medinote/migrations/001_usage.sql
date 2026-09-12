CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);
INSERT INTO schema_version SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM schema_version);
CREATE TABLE IF NOT EXISTS jobs(
 job_id TEXT PRIMARY KEY, channel TEXT NOT NULL CHECK(channel IN ('public','experiment')),
 case_id TEXT NOT NULL, method TEXT NOT NULL, created_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts(
 attempt_id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(job_id), month_utc TEXT NOT NULL,
 day_utc TEXT NOT NULL, client_key TEXT, reserved_micro_usd INTEGER NOT NULL,
 charged_micro_usd INTEGER, status TEXT NOT NULL CHECK(status IN ('reserved','settled','unknown')),
 started_at TEXT NOT NULL, finished_at TEXT, input_tokens INTEGER, output_tokens INTEGER, error_code TEXT
);
CREATE TABLE IF NOT EXISTS visitor_cooldowns(
 day_utc TEXT NOT NULL,client_key TEXT NOT NULL,last_request_at TEXT NOT NULL,PRIMARY KEY(day_utc,client_key)
);
CREATE TABLE IF NOT EXISTS generation_lease(
 singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),job_id TEXT NOT NULL REFERENCES jobs(job_id),expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS attempts_month ON attempts(month_utc);
CREATE INDEX IF NOT EXISTS attempts_day ON attempts(day_utc,job_id);
CREATE INDEX IF NOT EXISTS attempts_visitor ON attempts(day_utc,client_key);

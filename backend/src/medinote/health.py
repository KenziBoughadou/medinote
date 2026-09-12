from medinote.publication import load_public


def check_readiness(settings, usage):
    try:
        load_public(settings.root)
        if not usage or not settings.db_path.is_file():
            return False
        with usage.connection() as db:
            if [r[0] for r in db.execute("SELECT version FROM schema_version")] != [1]:
                return False
            required = {
                "jobs": {"job_id", "channel", "status"},
                "attempts": {"attempt_id", "job_id", "charged_micro_usd", "status"},
                "visitor_cooldowns": {"client_key", "day_utc", "last_request_at"},
                "generation_lease": {"singleton_id", "job_id", "expires_at"},
            }
            return all(
                columns <= {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
                for table, columns in required.items()
            )
    except Exception:
        return False

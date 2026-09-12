import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from medinote.config import (
    COOLDOWN_SECONDS,
    LEASE_SECONDS,
    MONTHLY_BUDGET,
    PUBLIC_DAILY,
    RESERVATION,
    VISITOR_DAILY,
)
from medinote.errors import ServiceError
from medinote.llm import estimated_micro_usd


def iso(now):
    return now.astimezone(UTC).isoformat().replace("+00:00", "Z")


class UsageStore:
    def __init__(self, path: Path, clock=None):
        self.path = path
        self.clock = clock or (lambda: datetime.now(UTC))

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=5000")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript((Path(__file__).parent / "migrations/001_usage.sql").read_text())
            if [r[0] for r in db.execute("SELECT version FROM schema_version")] != [1]:
                raise ValueError("Version SQLite incompatible")
        self.recover_expired_leases()
        self.purge_visitor_keys()

    def _recover(self, db, now):
        expired = [
            r[0]
            for r in db.execute(
                "SELECT job_id FROM generation_lease WHERE expires_at<=?", (iso(now),)
            )
        ]
        for job_id in expired:
            db.execute(
                "UPDATE attempts SET status='unknown',charged_micro_usd=reserved_micro_usd,finished_at=?,error_code='CRASH_RECOVERY' WHERE job_id=? AND status='reserved'",
                (iso(now), job_id),
            )
            db.execute(
                "UPDATE jobs SET status='interrupted',finished_at=? WHERE job_id=?",
                (iso(now), job_id),
            )
        db.execute("DELETE FROM generation_lease WHERE expires_at<=?", (iso(now),))

    def recover_expired_leases(self):
        with self.transaction() as db:
            self._recover(db, self.clock())

    def acquire_lease(self, channel, case_id, method):
        now = self.clock()
        job_id = uuid4().hex
        with self.transaction() as db:
            self._recover(db, now)
            if db.execute("SELECT 1 FROM generation_lease").fetchone():
                raise ServiceError("SERVER_BUSY", "Une génération est déjà en cours.", 429, 5)
            db.execute(
                "INSERT INTO jobs VALUES(?,?,?,?,?,NULL,?)",
                (job_id, channel, case_id, str(method), iso(now), "running"),
            )
            db.execute(
                "INSERT INTO generation_lease VALUES(1,?,?)",
                (job_id, iso(now + timedelta(seconds=LEASE_SECONDS))),
            )
        return job_id

    def release_lease(self, job_id, status="finished"):
        with self.transaction() as db:
            db.execute("DELETE FROM generation_lease WHERE job_id=?", (job_id,))
            db.execute(
                "UPDATE jobs SET status=?,finished_at=? WHERE job_id=?",
                (status, iso(self.clock()), job_id),
            )

    def _budget_available(self, db, month):
        if db.execute(
            "SELECT 1 FROM attempts WHERE charged_micro_usd>reserved_micro_usd LIMIT 1"
        ).fetchone():
            return False
        spent = db.execute(
            "SELECT COALESCE(SUM(COALESCE(charged_micro_usd,reserved_micro_usd)),0) FROM attempts WHERE month_utc=?",
            (month,),
        ).fetchone()[0]
        return spent + RESERVATION <= MONTHLY_BUDGET

    def reserve_attempt(self, job_id, client_key=None, retry=False):
        now = self.clock()
        stamp = iso(now)
        day = stamp[:10]
        month = stamp[:7]
        aid = uuid4().hex
        with self.transaction() as db:
            job = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if (
                not job
                or not db.execute(
                    "SELECT 1 FROM generation_lease WHERE job_id=? AND expires_at>?",
                    (job_id, stamp),
                ).fetchone()
            ):
                raise ServiceError("LEASE_EXPIRED", "Le délai de génération est dépassé.", 504)
            if not self._budget_available(db, month):
                raise ServiceError(
                    "BUDGET_EXHAUSTED", "Les relances sont temporairement indisponibles.", 429
                )
            if job["channel"] == "public":
                if not client_key:
                    raise ServiceError(
                        "CLIENT_ADDRESS_UNAVAILABLE", "Adresse visiteur indisponible.", 503
                    )
                counts = db.execute(
                    "SELECT COUNT(*) FROM attempts a JOIN jobs j USING(job_id) WHERE a.day_utc=? AND j.channel='public'",
                    (day,),
                ).fetchone()[0]
                visitor = db.execute(
                    "SELECT COUNT(*) FROM attempts WHERE day_utc=? AND client_key=?",
                    (day, client_key),
                ).fetchone()[0]
                if counts >= PUBLIC_DAILY or visitor >= VISITOR_DAILY:
                    raise ServiceError(
                        "QUOTA_EXHAUSTED", "Quota quotidien de relances atteint.", 429
                    )
                attempts = db.execute(
                    "SELECT COUNT(*) FROM attempts WHERE job_id=?", (job_id,)
                ).fetchone()[0]
                if retry:
                    if attempts != 1:
                        raise ValueError("Une seule reprise après une première tentative")
                else:
                    if attempts:
                        raise ValueError("Demande utilisateur déjà réservée")
                    cooldown = db.execute(
                        "SELECT last_request_at FROM visitor_cooldowns WHERE day_utc=? AND client_key=?",
                        (day, client_key),
                    ).fetchone()
                    if cooldown:
                        wait = (
                            COOLDOWN_SECONDS
                            - (now - datetime.fromisoformat(cooldown[0])).total_seconds()
                        )
                        if wait > 0:
                            raise ServiceError(
                                "COOLDOWN",
                                "Veuillez patienter avant une nouvelle relance.",
                                429,
                                int(wait) + 1,
                            )
                    db.execute(
                        "INSERT OR REPLACE INTO visitor_cooldowns VALUES(?,?,?)",
                        (day, client_key, stamp),
                    )
            db.execute(
                "INSERT INTO attempts VALUES(?,?,?,?,?,?,NULL,'reserved',?,NULL,NULL,NULL,NULL)",
                (aid, job_id, month, day, client_key, RESERVATION, stamp),
            )
        return aid

    def settle_attempt(self, attempt_id, input_tokens, output_tokens, error_code=None):
        charge = estimated_micro_usd(input_tokens, output_tokens)
        if charge is None:
            self.mark_unknown(attempt_id, error_code)
            return None
        with self.transaction() as db:
            count = db.execute(
                "UPDATE attempts SET charged_micro_usd=?,status='settled',finished_at=?,input_tokens=?,output_tokens=?,error_code=? WHERE attempt_id=? AND status='reserved'",
                (charge, iso(self.clock()), input_tokens, output_tokens, error_code, attempt_id),
            ).rowcount
            if count != 1:
                raise ValueError("Réservation absente ou déjà régularisée")
        return charge

    def mark_unknown(self, attempt_id, error_code=None):
        with self.transaction() as db:
            db.execute(
                "UPDATE attempts SET charged_micro_usd=reserved_micro_usd,status='unknown',finished_at=?,error_code=? WHERE attempt_id=? AND status='reserved'",
                (iso(self.clock()), error_code, attempt_id),
            )

    def get_capabilities(self, client_key=None):
        now = self.clock()
        day = iso(now)[:10]
        with self.connection() as db:
            available = self._budget_available(db, day[:7])
            busy = bool(
                db.execute(
                    "SELECT 1 FROM generation_lease WHERE expires_at>?", (iso(now),)
                ).fetchone()
            )
            global_count = db.execute(
                "SELECT COUNT(*) FROM attempts a JOIN jobs j USING(job_id) WHERE a.day_utc=? AND j.channel='public'",
                (day,),
            ).fetchone()[0]
            visitor = db.execute(
                "SELECT COUNT(*) FROM attempts WHERE day_utc=? AND client_key=?", (day, client_key)
            ).fetchone()[0]
            cooldown = db.execute(
                "SELECT last_request_at FROM visitor_cooldowns WHERE day_utc=? AND client_key=?",
                (day, client_key),
            ).fetchone()
            next_at = None
            if cooldown:
                until = datetime.fromisoformat(cooldown[0]) + timedelta(seconds=COOLDOWN_SECONDS)
                if until > now:
                    next_at = iso(until)
            reason = (
                "Relances temporairement indisponibles."
                if not available
                else "Une génération est en cours."
                if busy
                else "Quota quotidien atteint."
                if global_count >= PUBLIC_DAILY or visitor >= VISITOR_DAILY
                else "Veuillez patienter avant une nouvelle relance."
                if next_at
                else None
            )
            return dict(
                live_available=reason is None,
                reason=reason,
                methods=["direct", "structured"],
                visitor_remaining=max(0, VISITOR_DAILY - visitor),
                global_remaining=max(0, PUBLIC_DAILY - global_count),
                next_attempt_at=next_at,
            )

    def purge_visitor_keys(self):
        now = self.clock()
        cutoff = (now - timedelta(days=2)).date().isoformat()
        # Douze mois calendaires, avec ajustement du 29 février.
        previous_year = now.year - 1
        try:
            financial_cutoff = now.replace(year=previous_year)
        except ValueError:
            financial_cutoff = now.replace(year=previous_year, day=28)
        with self.transaction() as db:
            db.execute("UPDATE attempts SET client_key=NULL WHERE day_utc<?", (cutoff,))
            db.execute("DELETE FROM visitor_cooldowns WHERE day_utc<?", (cutoff,))
            db.execute(
                "DELETE FROM attempts WHERE started_at<? AND job_id NOT IN (SELECT job_id FROM generation_lease)",
                (iso(financial_cutoff),),
            )
            db.execute(
                "DELETE FROM jobs WHERE job_id NOT IN (SELECT job_id FROM attempts) AND job_id NOT IN (SELECT job_id FROM generation_lease) AND created_at<?",
                (iso(financial_cutoff),),
            )

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from medinote.config import MONTHLY_BUDGET, RESERVATION
from medinote.errors import ServiceError
from medinote.usage import UsageStore


@pytest.fixture
def store(tmp_path):
    store = UsageStore(tmp_path / "usage.sqlite3")
    store.initialize()
    return store


def test_concurrent_lease_and_persistence(store):
    def acquire(_):
        other = UsageStore(store.path)
        try:
            return other.acquire_lease("public", "case", "direct")
        except ServiceError:
            return None

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(acquire, range(2)))
    assert sum(r is not None for r in results) == 1
    job = next(r for r in results if r)
    aid = store.reserve_attempt(job, "hash")
    store.mark_unknown(aid)
    store.release_lease(job)
    reopened = UsageStore(store.path)
    reopened.initialize()
    assert reopened.get_capabilities("hash")["visitor_remaining"] == 5


def test_budget_boundary_and_anomaly(store):
    job = store.acquire_lease("experiment", "case", "direct")
    aid = store.reserve_attempt(job)
    with store.transaction() as db:
        db.execute(
            "UPDATE attempts SET charged_micro_usd=?,reserved_micro_usd=?,status='settled' WHERE attempt_id=?",
            (MONTHLY_BUDGET - RESERVATION, MONTHLY_BUDGET - RESERVATION, aid),
        )
    last = store.reserve_attempt(job)
    with pytest.raises(ServiceError):
        store.reserve_attempt(job)
    store.settle_attempt(last, 100000, 100000)
    assert store.get_capabilities()["live_available"] is False


def test_crash_expiry_and_utc(store):
    now = datetime(2026, 1, 31, 23, 59, 50, tzinfo=UTC)
    store.clock = lambda: now
    job = store.acquire_lease("public", "case", "direct")
    aid = store.reserve_attempt(job, "h")
    now += timedelta(seconds=76)
    store.recover_expired_leases()
    with store.connection() as db:
        row = db.execute("SELECT * FROM attempts WHERE attempt_id=?", (aid,)).fetchone()
        assert row["status"] == "unknown" and row["charged_micro_usd"] == RESERVATION
        assert row["month_utc"] == "2026-01"
    next_job = store.acquire_lease("public", "case", "direct")
    store.reserve_attempt(next_job, "new-day-h")
    store.release_lease(next_job)


def test_retry_cooldown_and_quota(store):
    now = datetime(2026, 9, 11, tzinfo=UTC)
    store.clock = lambda: now
    job = store.acquire_lease("public", "case", "direct")
    store.mark_unknown(store.reserve_attempt(job, "h"))
    store.mark_unknown(store.reserve_attempt(job, "h", retry=True))
    store.release_lease(job)
    job = store.acquire_lease("public", "case", "direct")
    with pytest.raises(ServiceError, match="COOLDOWN"):
        store.reserve_attempt(job, "h")
    store.release_lease(job)
    for _ in range(4):
        now += timedelta(seconds=61)
        job = store.acquire_lease("public", "case", "direct")
        store.mark_unknown(store.reserve_attempt(job, "h"))
        store.release_lease(job)
    now += timedelta(seconds=61)
    job = store.acquire_lease("public", "case", "direct")
    with pytest.raises(ServiceError, match="QUOTA"):
        store.reserve_attempt(job, "h")


def test_separate_processes_share_lease(store):
    import subprocess
    import sys

    code = """import sys
from pathlib import Path
from medinote.usage import UsageStore
from medinote.errors import ServiceError
s=UsageStore(Path(sys.argv[1]))
try:
 s.acquire_lease('experiment','synthetic','direct')
 print('acquired')
except ServiceError:
 print('busy')
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", code, str(store.path)], stdout=subprocess.PIPE, text=True
        )
        for _ in range(2)
    ]
    assert sorted(p.communicate(timeout=15)[0].strip() for p in processes) == ["acquired", "busy"]

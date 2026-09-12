"""Intégration isolée sur runner CI : changement d'IP et rollback réel des conteneurs."""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

BASE = [
    "docker",
    "compose",
    "-p",
    os.environ.get("COMPOSE_PROJECT_NAME", "medinote-ci"),
    "-f",
    "deploy/compose.local.yml",
    "-f",
    "deploy/compose.ci.yml",
]


def run(*args, capture=False, check=True):
    return subprocess.run(
        [*BASE, *args], check=check, text=True, stdout=subprocess.PIPE if capture else None
    )


def main():
    run("up", "-d", "--wait", "--wait-timeout", "120")
    # Réservation inconnue persistante, sans aucun appel fournisseur.
    reserve = "from medinote.usage import UsageStore; from pathlib import Path; s=UsageStore(Path('/var/lib/medinote/usage.sqlite3')); j=s.acquire_lease('experiment','ci-synthetic','direct'); a=s.reserve_attempt(j); s.mark_unknown(a); s.release_lease(j)"
    run("exec", "-T", "api", "python", "-c", reserve)
    old_id = run("ps", "-q", "api", capture=True).stdout.strip()
    inspect = json.loads(subprocess.check_output(["docker", "inspect", old_id], text=True))[0]
    network, details = next(iter(inspect["NetworkSettings"]["Networks"].items()))
    old_ip = details["IPAddress"]
    run("stop", "api")
    run("rm", "-f", "api")
    holder = "medinote-ci-ip-holder"
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            holder,
            "--network",
            network,
            "--ip",
            old_ip,
            "--memory",
            "128m",
            "--cap-drop",
            "ALL",
            os.environ["MEDINOTE_API_IMAGE"],
            "python",
            "-c",
            "import time;time.sleep(180)",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    try:
        run("up", "-d", "--no-deps", "--wait", "--wait-timeout", "120", "api")
        time.sleep(6)
        subprocess.run(
            ["python", "scripts/smoke.py", "--origin", "http://127.0.0.1:18080"], check=True
        )
    finally:
        subprocess.run(["docker", "rm", "-f", holder], check=False, stdout=subprocess.DEVNULL)
    # Candidate réellement non healthy puis réapplication ensemble des deux services.
    with tempfile.TemporaryDirectory() as folder:
        override = Path(folder) / "unhealthy.yml"
        override.write_text('services:\n  frontend:\n    entrypoint: ["sh", "-c", "exit 1"]\n')
        failed = subprocess.run(
            [
                *BASE,
                "-f",
                str(override),
                "up",
                "-d",
                "--force-recreate",
                "--wait",
                "--wait-timeout",
                "15",
            ],
            check=False,
        )
        assert failed.returncode != 0
    run("up", "-d", "--force-recreate", "--wait", "--wait-timeout", "120")
    check = "import sqlite3; c=sqlite3.connect('/var/lib/medinote/usage.sqlite3'); assert c.execute('SELECT SUM(charged_micro_usd) FROM attempts').fetchone()[0]>=25000"
    run("exec", "-T", "api", "python", "-c", check)
    subprocess.run(["python", "scripts/smoke.py", "--origin", "http://127.0.0.1:18080"], check=True)
    print(
        "IP API remplacée sans redémarrage nginx ; rollback des deux conteneurs ; budget conservé."
    )


if __name__ == "__main__":
    main()

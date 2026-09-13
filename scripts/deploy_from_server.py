"""Déploiement opérateur par HTTPS sortant, avec suivi GitHub vérifié."""

import argparse
import fcntl
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from deployment_preflight import deployment_preflight
from package_release import ARCHIVE_FILES, SHA, file_hash, validate_release
from smoke import smoke
from unpack_release import safe_unpack_release

REPO = "KenziBoughadou/medinote"
BASE = Path("/opt/medinote")
ORIGIN = "https://medinote.kbcompany.fr"


def github(path, body=None):
    args = ["gh", "api", "--hostname", "github.com", f"repos/{REPO}/{path}"]
    if body is not None:
        args += ["--method", "POST", "--input", "-"]
    result = subprocess.run(
        args,
        input=json.dumps(body) if body is not None else None,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return json.loads(result.stdout)


def verified_ci(sha):
    if not SHA.fullmatch(sha):
        raise ValueError("SHA complet requis")
    comparison = github(f"compare/{sha}...main")
    if comparison["status"] not in {"ahead", "identical"}:
        raise ValueError("Le commit n’appartient pas à main")
    environment = github("environments/production")
    if environment["protection_rules"] or environment["deployment_branch_policy"]:
        raise ValueError("Protection GitHub à respecter via le workflow ; arrêt du mode serveur")
    workflow_id = github("actions/workflows/ci.yml")["id"]
    runs = github(
        f"actions/workflows/ci.yml/runs?head_sha={sha}"
        "&branch=main&event=push&status=success&per_page=100"
    )["workflow_runs"]
    eligible = [
        r
        for r in runs
        if (
            r["head_sha"] == sha
            and r["head_branch"] == "main"
            and r["event"] == "push"
            and r["status"] == "completed"
            and r["conclusion"] == "success"
            and r["workflow_id"] == workflow_id
            and r["path"] == ".github/workflows/ci.yml"
            and r["repository"]["full_name"] == REPO
        )
    ]
    if not eligible:
        raise ValueError("Aucune CI réussie de main pour ce SHA")
    run = max(eligible, key=lambda r: r["id"])
    artifacts = github(f"actions/runs/{run['id']}/artifacts")["artifacts"]
    releases = [a for a in artifacts if a["name"] == f"release-{sha}" and not a["expired"]]
    if len(releases) != 1 or not 0 < releases[0]["size_in_bytes"] <= 21 * 1024**2:
        raise ValueError("Artefact de release absent, expiré ou hors limites")
    return run, releases[0]


def prepare_release(sha, run, base):
    destination = base / "releases" / sha
    with tempfile.TemporaryDirectory(prefix="server-deploy-", dir=base / "incoming") as temp:
        downloaded = Path(temp) / "download"
        subprocess.run(
            [
                "gh",
                "run",
                "download",
                str(run["id"]),
                "--repo",
                f"https://github.com/{REPO}",
                "--name",
                f"release-{sha}",
                "--dir",
                str(downloaded),
            ],
            check=True,
            timeout=180,
        )
        extracted = safe_unpack_release(downloaded / f"release-{sha}.tar.gz", Path(temp) / sha)
        if destination.is_symlink():
            raise ValueError("Lien de release refusé")
        if destination.exists():
            validate_release(destination)
            for name in ARCHIVE_FILES:
                if (destination / name).is_symlink() or (
                    (destination / name).read_bytes() != (extracted / name).read_bytes()
                ):
                    raise ValueError("Release locale différente de l’artefact CI")
        else:
            os.rename(extracted, destination)
    return destination


def verify_running(release, base):
    if (base / "current").resolve(strict=True) != release:
        raise ValueError("La release demandée n’est pas active")
    manifest = deployment_preflight(release, after_pull=True, inspect=True, base=base)
    args = [
        "docker",
        "compose",
        "-p",
        "medinote",
        "--env-file",
        str(release / "release.env"),
        "-f",
        str(release / "deploy/compose.production.yml"),
        "ps",
        "--all",
        "--quiet",
    ]
    ids = subprocess.check_output(args, text=True, timeout=30).split()
    if len(ids) != 2:
        raise ValueError("Deux conteneurs MediNote attendus")
    containers = json.loads(
        subprocess.check_output(
            ["docker", "inspect", *ids],
            text=True,
            timeout=30,
        )
    )
    seen = set()
    for container in containers:
        labels = container["Config"]["Labels"]
        service = labels.get("com.docker.compose.service")
        if (
            labels.get("com.docker.compose.project") != "medinote"
            or service not in manifest["images"]
            or service in seen
            or container["Config"]["Image"] != manifest["images"][service]["ref"]
            or not container["State"]["Running"]
            or container["State"].get("Health", {}).get("Status") != "healthy"
        ):
            raise ValueError("Conteneurs actifs incompatibles avec la release ou non healthy")
        seen.add(service)
    smoke(ORIGIN, manifest["commit_sha"])
    return manifest


def status(deployment_id, state, description):
    return github(
        f"deployments/{deployment_id}/statuses",
        {
            "state": state,
            "description": description,
            "environment": "production",
            "environment_url": ORIGIN,
            "auto_inactive": False,
        },
    )


def deploy_locked(sha, record_current, base, lock_fd):
    if record_current:
        release = (base / "current").resolve(strict=True)
        sha = release.name
        if not SHA.fullmatch(sha) or release != base / "releases" / sha:
            raise ValueError("Chemin de release active refusé")
    run, artifact = verified_ci(sha)
    release = prepare_release(sha, run, base)
    if record_current:
        verify_running(release, base)
    else:
        deployment_preflight(release, base=base)
    operation = "verify_current" if record_current else "deploy"
    deployment = github(
        "deployments",
        {
            "ref": sha,
            "auto_merge": False,
            "required_contexts": [],
            "environment": "production",
            "production_environment": True,
            "description": "Release active vérifiée depuis le serveur"
            if record_current
            else "Déploiement depuis la session serveur autorisée",
            "payload": {
                "transport": "authorized_server_session",
                "operation": operation,
                "ci_run_id": run["id"],
                "artifact_id": artifact["id"],
                "release_manifest_sha256": file_hash(release / "release.json"),
            },
        },
    )
    deployment_id = deployment["id"]
    print(f"Suivi GitHub créé : déploiement {deployment_id}, commit {sha}", flush=True)
    status(deployment_id, "in_progress", "Vérification de la production depuis le serveur")
    try:
        if not record_current:
            # Le verrou du parent reste détenu, y compris pendant un rollback.
            # Réutiliser le corps existant sans reprendre le même flock dans le fils.
            subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; deploy_locked "$2"',
                    "medinote-deploy",
                    str(release / "scripts/deploy.sh"),
                    str(release),
                ],
                check=True,
                pass_fds=(lock_fd,),
            )
        manifest = verify_running(release, base)
    except (Exception, KeyboardInterrupt):
        status(
            deployment_id, "failure", "Déploiement ou vérification échoué ; contrôler le serveur"
        )
        raise
    receipt = {
        "verified_at": datetime.now(UTC).isoformat(),
        "commit_sha": sha,
        "deployment_id": deployment_id,
        "operation": operation,
        "transport": "authorized_server_session",
        "ci_url": run["html_url"],
        "artifact_id": artifact["id"],
        "images": manifest["images"],
        "https_verified": True,
        "github_status": "pending",
    }
    receipts = base / "deployments"
    receipts.mkdir(mode=0o750, exist_ok=True)
    receipt_path = receipts / f"{deployment_id}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    # Ne jamais confondre une panne d’enregistrement GitHub avec un échec de l’application.
    status(deployment_id, "success", "Deux conteneurs healthy, HTTPS et version vérifiés")
    receipt["github_status"] = "success"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Production vérifiée et enregistrée : https://github.com/{REPO}/deployments")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--sha", help="SHA complet de main avec une CI réussie")
    selection.add_argument(
        "--record-current",
        action="store_true",
        help="Vérifier et enregistrer la release active sans la redéployer",
    )
    args = parser.parse_args()
    if args.sha is not None and not SHA.fullmatch(args.sha):
        parser.error("SHA complet requis")
    os.umask(0o027)
    with (BASE / "deploy.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        deploy_locked(args.sha, args.record_current, BASE, lock.fileno())


if __name__ == "__main__":
    main()

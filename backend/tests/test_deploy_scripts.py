import json
import subprocess
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("mutation", [None, "digest", "size", "sha"])
def test_local_image_accounting_keeps_digest_and_limits(root, monkeypatch, tmp_path, mutation):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import deployment_preflight as pre

    ref = "ghcr.io/kenziboughadou/medinote-api@sha256:" + "a" * 64
    manifest = {"commit_sha": "b" * 40, "images": {"api": {"ref": ref, "size_bytes": 289497163}}}
    info = {
        "Config": {"Labels": {"org.opencontainers.image.revision": "b" * 40}},
        "RepoDigests": [ref],
        "Size": 289518701,
        "Architecture": "amd64",
        "Os": "linux",
    }
    if mutation == "digest":
        info["RepoDigests"] = []
    elif mutation == "size":
        info["Size"] = 601 * 1024**2
    elif mutation == "sha":
        info["Config"]["Labels"]["org.opencontainers.image.revision"] = "c" * 40
    monkeypatch.setattr(pre, "validate_release", lambda _: manifest)
    monkeypatch.setattr(
        pre.os,
        "statvfs",
        lambda _: SimpleNamespace(f_bavail=5 * 1024**3, f_frsize=1, f_favail=20000),
    )
    monkeypatch.setattr(pre.subprocess, "run", lambda *a, **kw: None)
    monkeypatch.setattr(pre.subprocess, "check_output", lambda *a, **kw: json.dumps([info]))
    if mutation:
        with pytest.raises(ValueError):
            pre.deployment_preflight(tmp_path, after_pull=True, inspect=True, base=tmp_path)
    else:
        assert (
            pre.deployment_preflight(tmp_path, after_pull=True, inspect=True, base=tmp_path)
            == manifest
        )


def test_preflight_before_mutation(root, monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import deployment_preflight as pre

    monkeypatch.setattr(
        pre,
        "validate_release",
        lambda _: {
            "images": {"api": {"size_bytes": 200000000}, "frontend": {"size_bytes": 60000000}}
        },
    )
    monkeypatch.setattr(
        pre.os, "statvfs", lambda _: SimpleNamespace(f_bavail=1, f_frsize=4096, f_favail=20000)
    )
    called = []
    monkeypatch.setattr(pre.subprocess, "run", lambda *a, **kw: called.append(a))
    with pytest.raises(ValueError, match="insuffisants"):
        pre.deployment_preflight(tmp_path)
    assert called == []


def test_shell_syntax_and_no_destructive_budget_restore(root):
    for name in ["deploy", "rollback", "bootstrap-admin"]:
        subprocess.run(["bash", "-n", str(root / f"scripts/{name}.sh")], check=True)
    text = (root / "scripts/deploy.sh").read_text()
    assert "flock -x" in text and "system prune" not in text and "down -v" not in text
    assert "usage.sqlite3" not in text


def test_rollback_both_images_simulated(root, tmp_path):
    script = f"""source {root}/scripts/deploy.sh
apply_release() {{ echo "apply:$1"; }}
wait_ready() {{ echo "healthy:$1"; }}
smoke_public() {{ echo "https:$1"; }}
rollback_release /previous /candidate
"""
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True)
    assert result.stdout.splitlines() == ["apply:/previous", "healthy:/previous", "https:/previous"]


def test_first_deploy_no_false_rollback(root):
    script = f"""source {root}/scripts/deploy.sh
compose_release() {{ echo "compose:$*"; }}
rollback_release "" /candidate
"""
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert result.returncode == 1 and "compose:/candidate stop" in result.stdout

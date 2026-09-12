import subprocess
from types import SimpleNamespace

import pytest


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

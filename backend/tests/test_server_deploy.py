import copy
import json
import subprocess

import pytest


@pytest.fixture
def server_deploy(root, monkeypatch):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import deploy_from_server

    return deploy_from_server


@pytest.fixture
def ci_responses():
    sha = "a" * 40
    run = {
        "id": 12,
        "head_sha": sha,
        "head_branch": "main",
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "workflow_id": 34,
        "path": ".github/workflows/ci.yml",
        "repository": {"full_name": "KenziBoughadou/medinote"},
        "html_url": "https://github.com/KenziBoughadou/medinote/actions/runs/12",
    }
    return {
        f"compare/{sha}...main": {"status": "ahead"},
        "environments/production": {"protection_rules": [], "deployment_branch_policy": None},
        "actions/workflows/ci.yml": {"id": 34},
        f"actions/workflows/ci.yml/runs?head_sha={sha}"
        "&branch=main&event=push&status=success&per_page=100": {"workflow_runs": [run]},
        "actions/runs/12/artifacts": {
            "artifacts": [
                {"id": 56, "name": f"release-{sha}", "expired": False, "size_in_bytes": 8000},
            ]
        },
    }


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "branch",
        "event",
        "sha",
        "workflow",
        "repository",
        "failed",
        "expired",
        "protection",
    ],
)
def test_only_a_successful_main_ci_can_authorize_release(
    server_deploy,
    ci_responses,
    monkeypatch,
    mutation,
):
    responses = copy.deepcopy(ci_responses)
    run = next(v["workflow_runs"][0] for v in responses.values() if "workflow_runs" in v)
    if mutation == "branch":
        responses[f"compare/{'a' * 40}...main"]["status"] = "diverged"
    elif mutation == "event":
        run["event"] = "pull_request"
    elif mutation == "sha":
        run["head_sha"] = "b" * 40
    elif mutation == "workflow":
        run["workflow_id"] = 99
    elif mutation == "repository":
        run["repository"]["full_name"] = "someone/medinote"
    elif mutation == "failed":
        run["conclusion"] = "failure"
    elif mutation == "expired":
        responses["actions/runs/12/artifacts"]["artifacts"][0]["expired"] = True
    elif mutation == "protection":
        responses["environments/production"]["protection_rules"] = [{"type": "required_reviewers"}]
    monkeypatch.setattr(server_deploy, "github", lambda path: responses[path])
    if mutation:
        with pytest.raises(ValueError):
            server_deploy.verified_ci("a" * 40)
    else:
        assert server_deploy.verified_ci("a" * 40)[1]["id"] == 56


def test_invalid_sha_does_not_contact_github(server_deploy, monkeypatch):
    monkeypatch.setattr(server_deploy, "github", lambda *a: pytest.fail("Accès GitHub interdit"))
    with pytest.raises(ValueError, match="SHA complet"):
        server_deploy.verified_ci("main; echo unsafe")


def test_local_release_must_match_the_ci_archive(server_deploy, root, tmp_path, monkeypatch):
    from package_release import package_release

    base = tmp_path / "base"
    (base / "incoming").mkdir(parents=True)
    release = base / "releases" / ("a" * 40)
    archive = package_release(
        root,
        release,
        release.name,
        "ghcr.io/kenziboughadou/medinote-api@sha256:" + "1" * 64,
        "ghcr.io/kenziboughadou/medinote-frontend@sha256:" + "2" * 64,
        200000000,
        60000000,
    )

    def download(args, **kwargs):
        target = server_deploy.Path(args[-1])
        target.mkdir()
        (target / archive.name).write_bytes(archive.read_bytes())

    monkeypatch.setattr(server_deploy.subprocess, "run", download)
    assert server_deploy.prepare_release(release.name, {"id": 12}, base) == release
    # Un manifest encore structurellement valide ne prouve pas son identité avec la CI.
    manifest_path = release / "release.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["public_bundle_sha256"] = "f" * 64
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="différente"):
        server_deploy.prepare_release(release.name, {"id": 12}, base)


@pytest.mark.parametrize("mutation", [None, "unhealthy", "wrong_image", "stopped", "duplicate"])
def test_running_containers_must_match_before_public_success(
    server_deploy,
    tmp_path,
    monkeypatch,
    mutation,
):
    release = tmp_path / "releases" / ("a" * 40)
    release.mkdir(parents=True)
    (tmp_path / "current").symlink_to(release)
    manifest = {
        "commit_sha": release.name,
        "images": {
            "api": {"ref": "api@sha256:1"},
            "frontend": {"ref": "frontend@sha256:2"},
        },
    }
    containers = [
        {
            "Config": {
                "Image": image["ref"],
                "Labels": {
                    "com.docker.compose.project": "medinote",
                    "com.docker.compose.service": service,
                },
            },
            "State": {"Running": True, "Health": {"Status": "healthy"}},
        }
        for service, image in manifest["images"].items()
    ]
    if mutation == "unhealthy":
        containers[1]["State"]["Health"]["Status"] = "unhealthy"
    elif mutation == "wrong_image":
        containers[1]["Config"]["Image"] = "old-image"
    elif mutation == "stopped":
        containers[1]["State"]["Running"] = False
    elif mutation == "duplicate":
        containers[1] = containers[0]
    monkeypatch.setattr(server_deploy, "deployment_preflight", lambda *a, **kw: manifest)
    monkeypatch.setattr(
        server_deploy.subprocess,
        "check_output",
        lambda args, **kw: json.dumps(containers) if args[1] == "inspect" else "api-id\nfront-id\n",
    )
    public_checks = []
    monkeypatch.setattr(server_deploy, "smoke", lambda *a: public_checks.append(a))
    if mutation:
        with pytest.raises(ValueError):
            server_deploy.verify_running(release, tmp_path)
        assert not public_checks
    else:
        assert server_deploy.verify_running(release, tmp_path) == manifest
        assert public_checks == [(server_deploy.ORIGIN, release.name)]


@pytest.mark.parametrize("mode", ["record", "deploy", "deploy_failure", "health_failure"])
def test_github_success_requires_completed_deployment_and_verification(
    server_deploy,
    tmp_path,
    monkeypatch,
    mode,
):
    release = tmp_path / "releases" / ("a" * 40)
    release.mkdir(parents=True)
    (release / "release.json").write_text("{}")
    (tmp_path / "current").symlink_to(release)
    run = {"id": 12, "html_url": "https://github.com/KenziBoughadou/medinote/actions/runs/12"}
    monkeypatch.setattr(server_deploy, "verified_ci", lambda sha: (run, {"id": 56}))
    monkeypatch.setattr(server_deploy, "prepare_release", lambda *a: release)
    monkeypatch.setattr(server_deploy, "deployment_preflight", lambda *a, **kw: None)
    events = []

    def verify(*args):
        events.append("verify")
        if mode == "health_failure":
            raise ValueError("HTTPS en échec")
        return {"images": {}}

    def execute(*args, **kwargs):
        events.append("execute")
        assert kwargs["pass_fds"] == (99,)
        if mode == "deploy_failure":
            raise subprocess.CalledProcessError(1, "deploy.sh")

    monkeypatch.setattr(server_deploy, "verify_running", verify)
    monkeypatch.setattr(server_deploy.subprocess, "run", execute)
    monkeypatch.setattr(server_deploy, "github", lambda *a: {"id": 78})
    monkeypatch.setattr(server_deploy, "status", lambda _, state, description: events.append(state))
    if mode.endswith("failure"):
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            server_deploy.deploy_locked(release.name, False, tmp_path, 99)
        assert events[-1] == "failure" and "success" not in events
        assert not (tmp_path / "deployments").exists()
    else:
        server_deploy.deploy_locked(release.name, mode == "record", tmp_path, 99)
        assert events[-2:] == ["verify", "success"]
        assert ("execute" in events) == (mode == "deploy")
        assert (
            json.loads((tmp_path / "deployments/78.json").read_text())["github_status"] == "success"
        )

import io
import json
import tarfile

import pytest


@pytest.fixture
def release_modules(root, monkeypatch):
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import package_release
    import unpack_release

    return package_release, unpack_release


def make_release(root, tmp_path, modules):
    package, _ = modules
    return package.package_release(
        root,
        tmp_path / "release",
        "a" * 40,
        "ghcr.io/kenziboughadou/medinote-api@sha256:" + "1" * 64,
        "ghcr.io/kenziboughadou/medinote-frontend@sha256:" + "2" * 64,
        200_000_000,
        60_000_000,
    )


def test_archive_roundtrip(root, tmp_path, release_modules):
    package, unpack = release_modules
    archive = make_release(root, tmp_path, release_modules)
    dest = tmp_path / "releases" / ("a" * 40)
    unpack.safe_unpack_release(archive, dest)
    assert package.validate_release(dest)["db_schema_version"] == 1
    with pytest.raises(ValueError):
        unpack.safe_unpack_release(archive, dest)


@pytest.mark.parametrize(
    "entry,kind",
    [
        ("../escape", "file"),
        ("/tmp/escape", "file"),
        ("scripts/deploy.sh", "symlink"),
        ("unexpected", "file"),
    ],
)
def test_malicious_tar(root, tmp_path, release_modules, entry, kind):
    _, unpack = release_modules
    path = tmp_path / "evil.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo(entry)
        if kind == "symlink":
            member.type = tarfile.SYMTYPE
            member.linkname = "/etc/passwd"
            archive.addfile(member)
        else:
            member.size = 1
            archive.addfile(member, io.BytesIO(b"x"))
    with pytest.raises(ValueError):
        unpack.safe_unpack_release(path, tmp_path / ("a" * 40))
    assert not (tmp_path / "escape").exists()


@pytest.mark.parametrize("mutation", ["sha", "owner", "digest", "config", "db"])
def test_manifest_rejects_inconsistency(root, tmp_path, release_modules, mutation):
    package, _ = release_modules
    make_release(root, tmp_path, release_modules)
    p = tmp_path / "release/release.json"
    m = json.loads(p.read_text())
    if mutation == "sha":
        m["commit_sha"] = "abc123"
    if mutation == "owner":
        m["images"]["api"]["ref"] = m["images"]["api"]["ref"].replace("kenziboughadou", "someone")
    if mutation == "digest":
        m["images"]["api"]["ref"] = m["images"]["api"]["ref"].replace("sha256:", "sha256:xx")
    if mutation == "config":
        (tmp_path / "release/scripts/deploy.sh").write_text("altered")
    if mutation == "db":
        m["db_schema_version"] = 2
    p.write_text(json.dumps(m))
    with pytest.raises(ValueError):
        package.validate_release(tmp_path / "release")

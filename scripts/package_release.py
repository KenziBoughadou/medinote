"""Archive immuable d'une release : bibliothèque stdlib, aucun secret."""

import argparse
import hashlib
import json
import re
import tarfile
from pathlib import Path

PAYLOAD_FILES = [
    "deploy/compose.production.yml",
    "deploy/base-images.lock.json",
    "scripts/deploy.sh",
    "scripts/rollback.sh",
    "scripts/deployment_preflight.py",
    "scripts/package_release.py",
    "scripts/unpack_release.py",
    "scripts/check_images.py",
    "scripts/smoke.py",
]
ARCHIVE_FILES = set(PAYLOAD_FILES + ["release.json", "release.env"])
SHA = re.compile(r"^[0-9a-f]{40}$")
IMAGE = re.compile(r"^ghcr\.io/kenziboughadou/medinote-(api|frontend)@sha256:[0-9a-f]{64}$")


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release_env(manifest):
    return "".join(
        f"MEDINOTE_{kind.upper()}_IMAGE={manifest['images'][kind]['ref']}\n"
        for kind in ["api", "frontend"]
    )


def validate_release(directory):
    manifest = json.loads((directory / "release.json").read_text())
    if set(manifest) != {
        "schema_version",
        "commit_sha",
        "images",
        "architecture",
        "configuration_hashes",
        "db_schema_version",
        "public_bundle_sha256",
    }:
        raise ValueError("Champs du manifest invalides")
    if not SHA.fullmatch(manifest["commit_sha"]):
        raise ValueError("SHA complet requis")
    if (
        manifest["schema_version"] != "1.0"
        or manifest["architecture"] != "linux/amd64"
        or manifest["db_schema_version"] != 1
    ):
        raise ValueError("Release incompatible")
    if not re.fullmatch("[0-9a-f]{64}", manifest["public_bundle_sha256"]):
        raise ValueError("Hash de bundle invalide")
    if set(manifest["images"]) != {"api", "frontend"}:
        raise ValueError("Deux images requises")
    for kind, maximum in [("api", 600 * 1024**2), ("frontend", 128 * 1024**2)]:
        image = manifest["images"][kind]
        match = IMAGE.fullmatch(image["ref"])
        if not match or match[1] != kind:
            raise ValueError("Image GHCR non autorisée")
        if type(image["size_bytes"]) is not int or not 0 < image["size_bytes"] <= maximum:
            raise ValueError("Taille image hors plafond")
    if set(manifest["configuration_hashes"]) != set(PAYLOAD_FILES):
        raise ValueError("Configuration incomplète")
    for name, expected in manifest["configuration_hashes"].items():
        if (directory / name).is_symlink() or file_hash(directory / name) != expected:
            raise ValueError(f"Configuration altérée : {name}")
    if (directory / "release.env").read_text() != release_env(manifest):
        raise ValueError("Images et release.env discordants")
    return manifest


def package_release(root, output, sha, api_ref, frontend_ref, api_size, frontend_size):
    output.mkdir(parents=True, exist_ok=False)
    import shutil

    for name in PAYLOAD_FILES:
        (output / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, output / name)
    bundle = json.loads((root / "public-data/bundle.v1.json").read_text())
    manifest = {
        "schema_version": "1.0",
        "commit_sha": sha,
        "architecture": "linux/amd64",
        "db_schema_version": 1,
        "images": {
            "api": {"ref": api_ref, "size_bytes": api_size},
            "frontend": {"ref": frontend_ref, "size_bytes": frontend_size},
        },
        "configuration_hashes": {name: file_hash(output / name) for name in PAYLOAD_FILES},
        "public_bundle_sha256": bundle["content_sha256"],
    }
    (output / "release.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    (output / "release.env").write_text(release_env(manifest))
    validate_release(output)
    archive = output.parent / f"release-{sha}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name in sorted(ARCHIVE_FILES):
            tar.add(output / name, arcname=name, recursive=False)
    if archive.stat().st_size > 20 * 1024**2:
        raise ValueError("Archive trop volumineuse")
    return archive


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--sha", required=True)
    for kind in ["api", "frontend"]:
        p.add_argument(f"--{kind}-ref", required=True)
        p.add_argument(f"--{kind}-size", type=int, required=True)
    a = p.parse_args()
    print(
        package_release(
            a.root, a.output, a.sha, a.api_ref, a.frontend_ref, a.api_size, a.frontend_size
        )
    )


if __name__ == "__main__":
    main()

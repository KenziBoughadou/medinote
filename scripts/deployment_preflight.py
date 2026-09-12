import argparse
import json
import os
import subprocess
from pathlib import Path

from package_release import validate_release

GIB = 1024**3


def deployment_preflight(directory, after_pull=False, inspect=False, base=Path("/opt/medinote")):
    manifest = validate_release(directory)
    stats = os.statvfs(base)
    available = stats.f_bavail * stats.f_frsize
    minimum = (
        2 * GIB
        if after_pull
        else max(3 * GIB, 2 * GIB + 2 * sum(i["size_bytes"] for i in manifest["images"].values()))
    )
    if available < minimum or stats.f_favail <= 10000:
        raise ValueError("Espace ou inodes insuffisants : aucune mutation autorisée")
    subprocess.run(["docker", "network", "inspect", "web"], check=True, stdout=subprocess.DEVNULL)
    if inspect:
        for kind, image in manifest["images"].items():
            info = json.loads(
                subprocess.check_output(["docker", "image", "inspect", image["ref"]], text=True)
            )[0]
            if (
                info["Config"]["Labels"].get("org.opencontainers.image.revision")
                != manifest["commit_sha"]
            ):
                raise ValueError("Images de commits différents")
            if image["ref"] not in info["RepoDigests"] or info["Size"] != image["size_bytes"]:
                raise ValueError("Digest ou taille d’image discordants")
            if info["Architecture"] != "amd64":
                raise ValueError("Architecture incorrecte")
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--release-dir", type=Path, required=True)
    p.add_argument("--after-pull", action="store_true")
    p.add_argument("--inspect", action="store_true")
    a = p.parse_args()
    deployment_preflight(a.release_dir, a.after_pull, a.inspect)
    print("Préflight conforme")

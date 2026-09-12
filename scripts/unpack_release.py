import argparse
import os
import shutil
import tarfile
import tempfile
from pathlib import Path

from package_release import ARCHIVE_FILES, validate_release


def safe_unpack_release(archive, destination):
    if archive.stat().st_size > 20 * 1024**2 or destination.exists():
        raise ValueError("Archive trop grosse ou destination existante")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".medinote-unpack-", dir=destination.parent))
    try:
        with tarfile.open(archive, "r:gz") as tar:
            members = tar.getmembers()
            if len(members) != len(ARCHIVE_FILES) or {m.name for m in members} != ARCHIVE_FILES:
                raise ValueError("Archive hors liste autorisée")
            if sum(m.size for m in members) > 20 * 1024**2:
                raise ValueError("Archive décompressée trop grosse")
            for member in members:
                path = Path(member.name)
                if (
                    not member.isfile()
                    or path.is_absolute()
                    or ".." in path.parts
                    or member.size < 0
                ):
                    raise ValueError("Membre d’archive dangereux")
                target = temporary / path
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, target.open("xb") as dest:
                    shutil.copyfileobj(source, dest)
                target.chmod(0o750 if target.suffix == ".sh" else 0o640)
        manifest = validate_release(temporary)
        if destination.name != manifest["commit_sha"]:
            raise ValueError("SHA de destination discordant")
        os.rename(temporary, destination)
        return destination
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--destination", type=Path, required=True)
    a = p.parse_args()
    print(safe_unpack_release(a.archive, a.destination))

#!/usr/bin/env python3
"""Initialiser les clés MediNote dans le seul fichier central, sans les afficher."""

import argparse
import fcntl
import getpass
import os
import re
import secrets
import stat
import sys
import tempfile
import warnings
from pathlib import Path

SECRET_FILE = Path("/opt/secrets/medinote.env")


def initial_config(existing: str, api_key: str) -> str:
    lines = [line.strip() for line in existing.splitlines()]
    settings = [line for line in lines if line and not line.startswith("#")]
    if settings != ["MEDINOTE_LIVE_ENABLED=false"]:
        raise ValueError(
            "Configuration déjà renseignée ou différente du bootstrap ; aucun écrasement."
        )
    if not re.fullmatch(r"sk-[A-Za-z0-9_-]{20,}", api_key):
        raise ValueError("Format de clé incorrect ; aucune modification.")
    return (
        "MEDINOTE_LIVE_ENABLED=true\n"
        f"MEDINOTE_OPENAI_API_KEY={api_key}\n"
        f"MEDINOTE_QUOTA_HMAC_KEY={secrets.token_hex(32)}\n"
    )


def rotation_settings(existing: str) -> dict[str, str]:
    settings = {}
    for line in existing.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if not separator or name in settings:
            raise ValueError("Configuration non reconnue ; aucune modification.")
        settings[name] = value
    if (
        set(settings)
        != {"MEDINOTE_LIVE_ENABLED", "MEDINOTE_OPENAI_API_KEY", "MEDINOTE_QUOTA_HMAC_KEY"}
        or settings["MEDINOTE_LIVE_ENABLED"] not in {"true", "false"}
        or not re.fullmatch(r"sk-[A-Za-z0-9_-]{20,}", settings["MEDINOTE_OPENAI_API_KEY"])
        or not re.fullmatch(r"[a-fA-F0-9]{64}", settings["MEDINOTE_QUOTA_HMAC_KEY"])
    ):
        raise ValueError("Configuration non reconnue ; aucune modification.")
    return settings


def rotated_config(existing: str, api_key: str) -> str:
    settings = rotation_settings(existing)
    if not re.fullmatch(r"sk-[A-Za-z0-9_-]{20,}", api_key):
        raise ValueError("Format de clé incorrect ; aucune modification.")
    if secrets.compare_digest(settings["MEDINOTE_OPENAI_API_KEY"], api_key):
        raise ValueError("La nouvelle clé doit être différente de la précédente.")
    settings["MEDINOTE_OPENAI_API_KEY"] = api_key
    return "".join(f"{name}={value}\n" for name, value in settings.items())


def configure(rotate: bool = False) -> None:
    if os.geteuid() != 0:
        raise ValueError("Cette initialisation doit être exécutée par l’administrateur root.")
    if not sys.stdin.isatty():
        raise ValueError("Un terminal interactif est requis ; ne pas passer la clé en argument.")
    directory = SECRET_FILE.parent.lstat()
    if not stat.S_ISDIR(directory.st_mode) or directory.st_uid != 0 or directory.st_mode & 0o022:
        raise ValueError("Répertoire central invalide ; aucune permission globale modifiée.")
    fd = os.open(SECRET_FILE, os.O_RDONLY | os.O_NOFOLLOW)
    temporary = None
    try:
        with os.fdopen(fd, encoding="utf-8") as current:
            fcntl.flock(current.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            info = os.fstat(current.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != 0
                or info.st_gid != 10001
                or stat.S_IMODE(info.st_mode) != 0o440
                or info.st_nlink != 1
                or info.st_size > 8192
            ):
                raise ValueError("Fichier central invalide ; bootstrap administrateur requis.")
            existing = current.read()
            # Vérifier avant de demander la clé, sans produire ni conserver de secret provisoire.
            settings = [
                s.strip()
                for s in existing.splitlines()
                if s.strip() and not s.lstrip().startswith("#")
            ]
            if rotate:
                rotation_settings(existing)
            elif settings != ["MEDINOTE_LIVE_ENABLED=false"]:
                raise ValueError("Configuration déjà renseignée ; aucun écrasement.")
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                key = getpass.getpass("Clé API du projet OpenAI MediNote (saisie masquée) : ")
            content = rotated_config(existing, key) if rotate else initial_config(existing, key)
            temp_fd, temporary = tempfile.mkstemp(prefix=".medinote-", dir=SECRET_FILE.parent)
            with os.fdopen(temp_fd, "w", encoding="utf-8") as target:
                os.fchown(target.fileno(), 0, 10001)
                os.fchmod(target.fileno(), 0o440)
                target.write(content)
                target.flush()
                os.fsync(target.fileno())
            latest = SECRET_FILE.lstat()
            identity = ("st_dev", "st_ino", "st_mtime_ns", "st_ctime_ns", "st_size")
            if any(getattr(latest, field) != getattr(info, field) for field in identity):
                raise ValueError("Configuration modifiée pendant la saisie ; aucune substitution.")
            os.replace(temporary, SECRET_FILE)
            temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    print("Clés enregistrées dans le fichier central, sans affichage ni appel payant.")
    print("L’API doit être recréée depuis la release active pour lire le nouveau fichier.")


def main(argv=()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="Remplacer uniquement la clé API, en conservant la clé HMAC et le mode live.",
    )
    args = parser.parse_args(argv)
    try:
        configure(rotate=args.rotate)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (OSError, EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        print(
            "Initialisation interrompue ou accès impossible ; vérifier le fichier central.",
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

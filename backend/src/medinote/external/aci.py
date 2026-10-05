"""Lecture de la copie figée d'ACI-Bench (CC BY 4.0)."""

import csv
import re
from pathlib import Path

from medinote.external.schemas import ExternalCase, ExternalSegment
from medinote.serialization import sha256_file

SOURCE = "https://github.com/wyim/aci-bench"
SOURCE_COMMIT = "b909b2bb9cf1d19de08df15cddde7bd0179665e4"
DATA_DIR = Path("data/external/aci-bench")
SPLITS = {
    "dev": ("valid.csv", "6629e89e3fb409d2b3eceab60dc7b32fe1d3fb8d4e07795039284965522aa4d0"),
    "test": (
        "clinicalnlp_taskB_test1.csv",
        "5cc4008e68545f84913744a8e493a58bdf17ba7e1b7a0be46d6943d6bfca9471",
    ),
}
SPEAKERS = {"doctor": "clinician", "patient": "patient", "patient_guest": "other"}
TAG = re.compile(r"^\[([a-z_]+)\]\s*(.*)$")


def parse_dialogue(text):
    turns = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = TAG.match(line)
        if match:
            tag, content = match.groups()
            if tag not in SPEAKERS:
                raise ValueError(f"Locuteur inconnu : {tag}")
            turns.append([SPEAKERS[tag], tag, content])
        elif turns:
            # Trois lignes du corpus prolongent la réplique précédente sans étiquette.
            turns[-1][2] = f"{turns[-1][2]} {line}".strip()
        else:
            raise ValueError("Dialogue sans locuteur initial")
    # Une réplique étiquetée mais vide (D2N072) ne porte aucune information.
    turns = [turn for turn in turns if turn[2]]
    return [
        ExternalSegment(segment_id=f"s{i:03}", speaker=speaker, speaker_tag=tag, text=content)
        for i, (speaker, tag, content) in enumerate(turns, 1)
    ]


def split_path(root, split):
    name, expected = SPLITS[split]
    path = Path(root) / DATA_DIR / name
    if sha256_file(path) != expected:
        raise ValueError(f"Copie ACI-Bench altérée : {name}")
    return path


def load_split(root, split):
    with split_path(root, split).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cases = [
        ExternalCase(
            case_id=row["encounter_id"].lower(),
            split=split,
            subset=row["dataset"],
            segments=parse_dialogue(row["dialogue"]),
            reference_note=row["note"].strip(),
        )
        for row in rows
    ]
    if len({c.case_id for c in cases}) != len(cases):
        raise ValueError("Identifiants ACI-Bench dupliqués")
    return sorted(cases, key=lambda c: c.case_id)

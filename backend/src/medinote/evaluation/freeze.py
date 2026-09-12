import os
import subprocess
from pathlib import Path

from medinote.corpus import CorpusRepository
from medinote.evaluation.schemas import FrozenManifest
from medinote.schemas import Method
from medinote.serialization import canonical_json, sha256_file, utc_now

FROZEN_PATHS = [
    "data/cases.v1.jsonl",
    "data/stress.v1.jsonl",
    "data/gold.v1.jsonl",
    "data/provenance.v1.json",
    "data/demo_ids.v1.json",
    "backend/src/medinote/schemas.py",
    "backend/src/medinote/rendering.py",
    "backend/src/medinote/sources.py",
    "backend/src/medinote/llm.py",
    "backend/src/medinote/pipelines.py",
    "backend/src/medinote/generation.py",
    "eval/protocol.v1.json",
    "eval/annotation-guide.v1.md",
    "eval/pricing.v1.json",
    "uv.lock",
    "frontend/package-lock.json",
]


def freeze_manifest(root: Path, output: Path):
    repo = CorpusRepository(root).load()
    repo.validate_corpus()
    paths = FROZEN_PATHS + [
        str(p.relative_to(root))
        for p in sorted((root / "backend/src/medinote/prompts").glob("*"))
        if p.is_file()
    ]
    paths += [
        str(p.relative_to(root))
        for p in sorted((root / "backend/src/medinote/evaluation").glob("*.py"))
    ]
    code_sha = os.environ.get("MEDINOTE_BUILD_SHA", "")
    if not code_sha or code_sha == "development":
        code_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        if subprocess.check_output(
            ["git", "diff", "HEAD", "--", *paths], cwd=root, text=True
        ).strip():
            raise ValueError("Les entrées du gel doivent correspondre au commit")
    files = {p: sha256_file(root / p) for p in paths}
    reference_hashes = {
        p: files[p] for p in ["data/cases.v1.jsonl", "data/stress.v1.jsonl", "data/gold.v1.jsonl"]
    }
    reviewed = {
        e.artifact_sha256
        for e in repo.review_events
        if e.kind == "human" and e.outcome == "accepted"
    }
    review = "human" if set(reference_hashes.values()) <= reviewed else "none"
    suites = {}
    for name, ids in [
        ("main-test", sorted(c.case_id for c in repo.cases.values() if c.split == "test")),
        ("stress", sorted(c.case_id for c in repo.cases.values() if c.split == "stress")),
        ("demo", sorted(c.case_id for c in repo.list_public_cases())),
    ]:
        suites[name] = [
            (cid, m)
            for i, cid in enumerate(ids)
            for m in (list(Method) if i % 2 == 0 else list(reversed(Method)))
        ]
    manifest = FrozenManifest(
        schema_version="1.0",
        created_at=utc_now(),
        code_sha=code_sha,
        files=files,
        parameters={
            "model": "gpt-4.1-mini-2025-04-14",
            "temperature": 0,
            "max_output_tokens": 4000,
            "store": False,
            "max_retries": 0,
            "attempt_timeout_seconds": 25,
            "other_parameters": "provider_defaults",
        },
        suites=suites,
        reference_review=review,
        reference_hashes=reference_hashes,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as f:
        f.write(canonical_json(manifest) + "\n")
    return manifest


def verify_manifest(root: Path, path: Path):
    manifest = FrozenManifest.model_validate_json(path.read_text())
    for name, expected in manifest.files.items():
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not (root / relative).is_file()
            or sha256_file(root / relative) != expected
        ):
            raise ValueError(f"Entrée figée altérée : {name}")
    return manifest

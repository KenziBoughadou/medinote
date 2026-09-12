import pytest
from medinote.evaluation.freeze import verify_manifest
from medinote.evaluation.schemas import FrozenManifest
from medinote.serialization import sha256_file, write_json


def test_changed_hash_refused(tmp_path):
    source = tmp_path / "input.txt"
    source.write_text("original")
    manifest = FrozenManifest(
        schema_version="1.0",
        created_at="2026-09-11T00:00:00Z",
        code_sha="1" * 40,
        files={"input.txt": sha256_file(source)},
        parameters={},
        suites={},
        reference_review="none",
        reference_hashes={},
    )
    path = tmp_path / "manifest.json"
    write_json(path, manifest)
    verify_manifest(tmp_path, path)
    source.write_text("changed")
    with pytest.raises(ValueError, match="altérée"):
        verify_manifest(tmp_path, path)

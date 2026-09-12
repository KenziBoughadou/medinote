from types import SimpleNamespace

import pytest
from medinote.errors import ServiceError
from medinote.evaluation.runner import run_batch
from medinote.evaluation.schemas import FrozenManifest
from medinote.serialization import write_json


async def test_missing_dependency_does_not_create_fake_runs(tmp_path):
    manifest = FrozenManifest(
        schema_version="1.0",
        created_at="2026-09-11T00:00:00Z",
        code_sha="1" * 40,
        files={},
        parameters={},
        suites={"demo": []},
        reference_review="none",
        reference_hashes={},
    )
    path = tmp_path / "manifest.json"
    write_json(path, manifest)

    def disabled():
        raise ServiceError("LIVE_DISABLED", "Absent")

    with pytest.raises(ServiceError):
        await run_batch(
            tmp_path, path, "demo", tmp_path / "output", SimpleNamespace(_check_live=disabled)
        )
    assert not (tmp_path / "output").exists()

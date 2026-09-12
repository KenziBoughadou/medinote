"""Campagne complète simulée dans tmp_path ; jamais un résultat scientifique publié."""

import json
from types import SimpleNamespace

import pytest
from medinote.cli import _publish
from medinote.config import MODEL_ID, Settings
from medinote.corpus import CorpusRepository
from medinote.evaluation.blinding import export_blind_bundle, import_annotations
from medinote.evaluation.freeze import freeze_manifest
from medinote.evaluation.report import build_report
from medinote.evaluation.runner import collect_runs, run_batch
from medinote.generation import GenerationService
from medinote.llm import ProviderResult
from medinote.schemas import SectionKey
from medinote.serialization import canonical_json
from medinote.usage import UsageStore


async def test_complete_simulated_evaluation_flow(root, tmp_path, monkeypatch):
    monkeypatch.setenv("MEDINOTE_BUILD_SHA", "1" * 40)
    manifest_path = tmp_path / "manifest.json"
    manifest = freeze_manifest(root, manifest_path)
    assert len(manifest.suites["main-test"]) == 80
    assert len(manifest.suites["stress"]) == 40
    with pytest.raises(FileExistsError):
        freeze_manifest(root, manifest_path)

    class EmptyProvider:
        calls = 0

        async def generate(self, request):
            self.calls += 1
            payload = (
                {key: [] for key in SectionKey} if request.method == "direct" else {"facts": []}
            )
            return ProviderResult(
                status="ok",
                raw_json={"model": MODEL_ID, "fixture": True},
                output_text=canonical_json(payload),
                model_returned=MODEL_ID,
                input_tokens=100,
                output_tokens=50,
            )

    settings = Settings(
        root=root,
        state_dir=tmp_path / "state",
        env="test",
        live_enabled=True,
        openai_api_key="simulated-only",
    )
    store = UsageStore(settings.db_path)
    store.initialize()
    provider = EmptyProvider()
    service = GenerationService(settings, CorpusRepository(root).load(), store, provider)
    study = tmp_path / "study"
    for suite in ["main-test", "stress"]:
        await run_batch(root, manifest_path, suite, study / suite, service)
    assert provider.calls == 120
    runs = collect_runs(study)
    assert len(runs) == 120
    blind = tmp_path / "blind"
    export_blind_bundle(root, study, blind)
    assert not (blind / "blind-mapping.json").exists()
    forms = [
        json.loads(line) for line in (blind / "annotations-template.jsonl").read_text().splitlines()
    ]
    for form in forms:
        document = json.loads((blind / f"{form['blind_output_id']}.json").read_text())
        assert "method" not in document and "metadata" not in document
        form.update(
            status="complete",
            segmentation_review_complete=True,
            annotator={
                "kind": "ai",
                "id": "test-fixture",
                "model_snapshot": "simulated-only",
                "prompt_sha256": "0" * 64,
            },
        )
        form["gold_assessments"] = [
            dict(
                gold_id=g["fact_id"],
                status="omitted" if g["expected_in_note"] else "not_required",
                claim_ids=[],
                justification="Note vide dans une fixture simulée.",
            )
            for g in document["gold"]
        ]
    annotations = tmp_path / "annotations.jsonl"
    annotations.write_text("".join(canonical_json(f) + "\n" for f in forms))
    imported = import_annotations(root, study, annotations)
    report = build_report(root, study, imported, tmp_path / "report")
    assert report.status == "ai_annotated"
    assert report.metrics.by_method["direct"]["omission"].value == 1
    assert report.metrics.by_method["structured"]["citation_precision"].value is None
    assert report.metrics.comparisons["coverage"].difference == 0
    assert report.metrics.stress["direct"].denominator == 10
    assert report.metrics.stress["direct"].value == 0
    assert (tmp_path / "report/bootstrap-indices.json.gz").is_file()
    assert len(list((tmp_path / "report/figures").glob("*.svg"))) == 3
    await run_batch(root, manifest_path, "demo", tmp_path / "demo", service)
    _publish(
        settings,
        SimpleNamespace(
            demo_batch=tmp_path / "demo", report=tmp_path / "report", output=tmp_path / "public"
        ),
    )
    published = json.loads((tmp_path / "public/bundle.v1.json").read_text())
    assert len(published["results"]) == 6
    assert all(
        result["origin"] == "llm_recorded"
        for methods in published["results"].values()
        for result in methods.values()
    )
    assert provider.calls == 132
    with pytest.raises(FileExistsError):
        import_annotations(root, study, annotations)
    frozen_path = study / "main-test/frozen-manifest.json"
    original_manifest = frozen_path.read_text()
    frozen_path.write_text(original_manifest + "\n")
    with pytest.raises(ValueError, match="Hash du gel"):
        collect_runs(study, root)
    frozen_path.write_text(original_manifest)
    (study / runs[0].note_path).write_text("{}")
    with pytest.raises(ValueError, match="Hash"):
        collect_runs(study)

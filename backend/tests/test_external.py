import json
import shutil

import pytest
from medinote.config import RESERVATION
from medinote.errors import ServiceError
from medinote.evaluation.freeze import verify_manifest
from medinote.external import aci
from medinote.external.agreement import cohen_kappa, gwet_ac1
from medinote.external.campaign import (
    freeze_external,
    require_production,
    run_generation,
    run_judging,
    verify_external_manifest,
)
from medinote.external.llm import (
    MAX_INPUT_TOKENS,
    PRICES,
    coverage_request,
    generation_request,
    reference_facts_request,
)
from medinote.external.rendering import render_extracted_fact, render_output
from medinote.external.report import build_report, rouge
from medinote.external.schemas import ExtractionOutput, ReferenceFact
from medinote.llm import ProviderResult
from medinote.usage import UsageStore


class FakeProvider:
    def __init__(self, failures=(), coverage_labels=("covered", "omitted", "contradicted")):
        self.failures = list(failures)
        self.coverage_labels = list(coverage_labels)
        self.calls = []
        self.payloads = []

    async def generate(self, request):
        name = request.payload["text"]["format"]["name"]
        self.calls.append(name)
        self.payloads.append(request.payload)
        if self.failures and self.failures[0] == len(self.calls):
            self.failures.pop(0)
            return ProviderResult(status="timeout", error_code="PROVIDER_TIMEOUT", duration_ms=5)
        source = json.loads(request.payload["input"][0]["content"])
        if name == "DirectOutput":
            empty = {
                k: []
                for k in [
                    "history",
                    "background",
                    "medications_allergies",
                    "observations",
                    "assessment",
                    "plan",
                ]
            }
            output = {"reason": [{"text": "Cough for a week.", "source_ids": ["s002"]}], **empty}
            output["plan"] = [{"text": "Chest X-ray.", "source_ids": ["s999"]}]
        elif name == "ExtractionOutput":
            output = {
                "facts": [
                    {
                        "section": "reason",
                        "label": "cough",
                        "value": "one week",
                        "unit": None,
                        "subject": {"kind": "patient", "label": None},
                        "polarity": "affirmed",
                        "temporality": "present",
                        "certainty": "reported",
                        "source_ids": ["s002"],
                    }
                ]
            }
        elif name == "ReferenceFactsOutput":
            output = {
                "facts": [
                    {"section": "reason", "text": "The patient has a cough."},
                    {"section": "history", "text": "The cough started one week ago."},
                    {"section": "plan", "text": "A chest X-ray is ordered."},
                ]
            }
        elif name == "CoverageOutput":
            labels = self.coverage_labels
            output = {
                "judgments": [
                    {"index": f["index"], "label": labels[(f["index"] - 1) % len(labels)]}
                    for f in source["reference_facts"]
                ]
            }
        else:
            output = {
                "judgments": [
                    {
                        "index": a["index"],
                        "label": "supported",
                        "citations_support": a["index"] == 1,
                    }
                    for a in source["assertions"]
                ]
            }
        return ProviderResult(
            status="ok",
            raw_json={"id": f"resp-{len(self.calls)}", "model": request.model},
            output_text=json.dumps(output),
            model_returned=request.model,
            input_tokens=1000,
            output_tokens=200,
            duration_ms=100 + len(self.calls),
        )


@pytest.fixture
def usage(tmp_path):
    store = UsageStore(tmp_path / "usage.sqlite3")
    store.initialize()
    return store


@pytest.fixture
def manifest(root, tmp_path, monkeypatch):
    monkeypatch.setenv("MEDINOTE_BUILD_SHA", "0" * 40)
    path = tmp_path / "external-manifest.json"
    freeze_external(root, path)
    return path


def test_v1_freeze_is_untouched(root):
    verify_manifest(root, root / "eval/frozen-manifest.v1.json")


def test_aci_copy_is_pinned_and_parsed(root, tmp_path):
    dev, test = aci.load_split(root, "dev"), aci.load_split(root, "test")
    assert (len(dev), len(test)) == (20, 40)
    assert {c.subset for c in test} == {"aci", "virtassist", "virtscribe"}
    d2n068 = next(c for c in dev if c.case_id == "d2n068")
    assert any(
        "order an echocardiogram . lastly , for your high blood pressure" in s.text
        for s in d2n068.segments
    )
    assert all(s.text for c in dev for s in c.segments)
    copy = tmp_path / aci.DATA_DIR
    copy.mkdir(parents=True)
    for name, _ in aci.SPLITS.values():
        shutil.copy(root / aci.DATA_DIR / name, copy / name)
    with (copy / "valid.csv").open("a") as f:
        f.write("\n")
    with pytest.raises(ValueError, match="altérée"):
        aci.load_split(tmp_path, "dev")


def test_unknown_speaker_is_rejected():
    with pytest.raises(ValueError, match="Locuteur inconnu"):
        aci.parse_dialogue("[doctor] hello\n[nurse] hi")


def test_requests_fit_limits_and_prices_are_archived(root):
    archived = json.loads((root / "eval/external/pricing.v2.json").read_text())["models"]
    assert PRICES == {
        model: (p["input_usd_per_million"], p["output_usd_per_million"])
        for model, p in archived.items()
    }
    for split in ["dev", "test"]:
        for case in aci.load_split(root, split):
            for method in ["direct", "structured"]:
                request = generation_request(case, method)
                assert request.input_tokens <= MAX_INPUT_TOKENS
                assert request.payload["store"] is False
            assert reference_facts_request(case).reservation_micro_usd < 100_000


def test_structured_rendering_is_english_and_flags_unknown_sources(root):
    case = aci.load_split(root, "dev")[0]
    output = ExtractionOutput.model_validate(
        {
            "facts": [
                {
                    "section": "history",
                    "label": "fever",
                    "value": None,
                    "unit": None,
                    "subject": {"kind": "relative", "label": "mother"},
                    "polarity": "negated",
                    "temporality": "past",
                    "certainty": "reported",
                    "source_ids": ["s001", "s999"],
                }
            ]
        }
    )
    assert render_extracted_fact(output.facts[0]) == (
        "fever — negated; relative: mother; past; reported."
    )
    note = render_output(case, "structured", output)
    assert note.assertions[0].unresolved_ids == ["s999"]
    assert note.text.startswith("Chief complaint")


def test_usage_reserves_the_requested_amount_and_prices_by_model(usage):
    job = usage.acquire_lease("experiment", "d2n001", "judge-coverage")
    attempt = usage.reserve_attempt(job, amount=60_000)
    assert usage.settle_attempt(attempt, 1000, 1000, pricing=lambda i, o: 10_000) == 10_000
    usage.release_lease(job)
    job = usage.acquire_lease("experiment", "d2n001", "direct")
    with pytest.raises(ValueError):
        usage.reserve_attempt(job, amount=0)
    default = usage.reserve_attempt(job)
    with usage.connection() as db:
        reserved = db.execute(
            "SELECT reserved_micro_usd FROM attempts WHERE attempt_id=?", (default,)
        ).fetchone()[0]
    assert reserved == RESERVATION


def test_paid_campaigns_require_production(settings):
    with pytest.raises(ServiceError) as error:
        require_production(settings)
    assert error.value.code == "SHARED_BUDGET_REQUIRED"


def test_manifest_detects_altered_inputs(root, manifest, tmp_path):
    data = json.loads(manifest.read_text())
    assert data["source"]["commit"] == aci.SOURCE_COMMIT
    assert "data/external/aci-bench/clinicalnlp_taskB_test1.csv" in data["files"]
    assert "backend/src/medinote/external/prompts/judge-support.v2.txt" in data["files"]
    data["files"]["uv.lock"] = "0" * 64
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="altérée"):
        verify_external_manifest(root, altered)
    with pytest.raises(ValueError, match="jamais remplacé"):
        freeze_external(root, manifest)


async def test_dev_campaign_end_to_end(root, manifest, usage, tmp_path):
    # Appel 3 : génération en échec ; appel 4 : premier jugement relancé.
    generations = FakeProvider(failures=[3])
    batch = await run_generation(root, manifest, "dev", tmp_path / "dev", usage, generations)
    runs = [json.loads(line) for line in (batch / "runs.jsonl").read_text().splitlines()]
    assert len(runs) == 40
    assert [r["status"] for r in runs].count("timeout") == 1
    assert runs[0]["method"] == "direct" and runs[2]["method"] == "structured"
    with pytest.raises(FileExistsError):
        await run_generation(root, manifest, "dev", batch, usage, FakeProvider())

    judge = FakeProvider(failures=[2])
    judgments = await run_judging(root, manifest, batch, tmp_path / "judge", usage, judge)
    records = (judgments / "judgments.jsonl").read_text().splitlines()
    assert sum(json.loads(r)["status"] == "timeout" for r in records) == 1
    calls = len(judge.calls)
    # Une reprise ne repaie aucun jugement déjà obtenu.
    await run_judging(root, manifest, batch, judgments, usage, judge)
    assert len(judge.calls) == calls

    second = await run_judging(
        root, manifest, batch, tmp_path / "second", usage, FakeProvider(), "secondary", judgments
    )
    report = build_report(root, batch, judgments, second, tmp_path / "report")
    assert report["judge_agreement"]["coverage"]["cohen_kappa"] == pytest.approx(1.0)
    assert report["judge_agreement"]["reliable"] is True
    counts = report["counts"]
    assert counts["direct"]["planned"] == counts["structured"]["planned"] == 20
    assert counts["direct"]["valid"] + counts["structured"]["valid"] == 39
    assert counts["direct"]["unresolved_citations"] == counts["direct"]["valid"]
    coverage = report["comparisons"]["coverage"]
    assert coverage["ci95_low"] <= coverage["difference"] <= coverage["ci95_high"]
    assert (tmp_path / "report" / "report.md").read_text().startswith("# Étude externe")
    with usage.connection() as db:
        charged = db.execute(
            "SELECT COUNT(*) FROM attempts WHERE charged_micro_usd > reserved_micro_usd"
        ).fetchone()[0]
    assert charged == 0


async def test_second_judge_reuses_reference_facts_and_measures_agreement(
    root, manifest, usage, tmp_path
):
    batch = await run_generation(root, manifest, "test", tmp_path / "test", usage, FakeProvider())
    with pytest.raises(ValueError, match="premier"):
        await run_judging(
            root, manifest, batch, tmp_path / "early", usage, FakeProvider(), "secondary"
        )
    primary = await run_judging(root, manifest, batch, tmp_path / "judge", usage, FakeProvider())
    judge = FakeProvider(coverage_labels=["covered", "omitted", "omitted"])
    second = await run_judging(
        root, manifest, batch, tmp_path / "second", usage, judge, "secondary", primary
    )
    assert "ReferenceFactsOutput" not in judge.calls
    assert {p["model"] for p in judge.payloads} == {"gpt-5-mini-2025-08-07"}
    assert all(
        "temperature" not in p and p["reasoning"] == {"effort": "low"} for p in judge.payloads
    )
    with pytest.raises(ValueError, match="rôle"):
        build_report(root, batch, primary, primary, tmp_path / "wrong")
    report = build_report(root, batch, primary, second, tmp_path / "report")
    agreement = report["judge_agreement"]
    # Un fait sur trois change d'étiquette (contredit → omis) chez le second juge.
    assert agreement["coverage"]["agreement"] == pytest.approx(2 / 3)
    assert agreement["coverage"]["confusion_primary_by_secondary"]["contradicted"]["omitted"] == 80
    assert agreement["support"]["cohen_kappa"] is None
    assert agreement["support"]["gwet_ac1"] == 1.0
    assert report["second_judge"]["comparisons"]["coverage"]["a"] == pytest.approx(1 / 3)
    markdown = (tmp_path / "report" / "report.md").read_text()
    assert "Aucune validation humaine" in markdown and "Accord entre les deux juges" in markdown


def test_rouge_and_kappa_reference_values():
    assert rouge("a b c", "a b c") == {"rouge1": 1.0, "rouge2": 1.0, "rougeL": 1.0}
    assert rouge("x y", "a b")["rougeL"] == 0.0
    assert rouge("a c b", "a b c")["rougeL"] == pytest.approx(2 / 3)
    pairs = [("a", "a"), ("a", "b"), ("b", "b"), ("b", "b")]
    assert cohen_kappa(pairs, ["a", "b"]) == pytest.approx(0.5)
    assert gwet_ac1(pairs, ["a", "b"]) == pytest.approx((0.75 - 0.46875) / 0.53125)
    # Accord parfait sur une seule étiquette : kappa indéfini, AC1 égal à 1.
    unanimous = [("a", "a")] * 10
    assert cohen_kappa(unanimous, ["a", "b"]) is None
    assert gwet_ac1(unanimous, ["a", "b"]) == 1.0


def test_coverage_request_numbers_reference_facts(root):
    case = aci.load_split(root, "dev")[0]
    note = render_output(case, "structured", ExtractionOutput(facts=[]))
    request = coverage_request(note, [ReferenceFact(section="plan", text="X-ray ordered.")])
    source = json.loads(request.payload["input"][0]["content"])
    assert source["reference_facts"] == [{"index": 1, "section": "plan", "text": "X-ray ordered."}]

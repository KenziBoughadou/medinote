import json
from pathlib import Path

from medinote.corpus import DEMO_IDS, CorpusRepository
from medinote.schemas import GenerationResult, Method, PublicBundle, PublishedReport
from medinote.serialization import sha256_file, sha256_json, utc_now, write_json
from medinote.sources import finalize_note, resolve_citations, technical_checks


def validate_published_result(result, case):
    result = GenerationResult.model_validate(result)
    if case.case_id not in DEMO_IDS or case.split != "dev" or result.case_id != case.case_id:
        raise ValueError("Seuls les six cas dev autorisés sont publiables")
    if result.origin == "llm_live":
        raise ValueError("Une réponse live ne constitue pas une archive publiable")
    rebuilt = finalize_note(case.case_id, result.note.sections)
    if rebuilt != result.note:
        raise ValueError("Hash ou texte canonique discordant")
    for section in result.note.sections:
        for i, assertion in enumerate(section.assertions, 1):
            if assertion.assertion_id != f"{section.key}.{i:03}":
                raise ValueError("Identifiant serveur discordant")
            expected = resolve_citations(
                case, [c.segment_id for c in assertion.citations], assertion.assertion_id
            )
            if expected != assertion.citations:
                raise ValueError("Citation discordante avec la source")
    if technical_checks(result.note) != result.checks:
        raise ValueError("Contrôles techniques discordants")
    return result


def validate_bundle(bundle):
    bundle = PublicBundle.model_validate(bundle)
    payload = bundle.model_dump(mode="json", exclude={"content_sha256"})
    if sha256_json(payload) != bundle.content_sha256:
        raise ValueError("Hash du bundle discordant")
    if [c.case_id for c in bundle.consultations] != DEMO_IDS or set(bundle.results) != set(
        DEMO_IDS
    ):
        raise ValueError("Sélection publique discordante")
    for case in bundle.consultations:
        if set(bundle.results[case.case_id]) != set(Method):
            raise ValueError("Deux méthodes requises")
        for result in bundle.results[case.case_id].values():
            validate_published_result(result, case)
    return bundle


def load_public(root):
    bundle = validate_bundle(json.loads((root / "public-data/bundle.v1.json").read_text()))
    report = PublishedReport.model_validate_json((root / "public-data/report.v1.json").read_text())
    if report.hashes.get("bundle") != bundle.content_sha256:
        raise ValueError("Rapport et bundle discordants")
    validate_report_review(root, report)
    return bundle, report


def validate_report_review(root, report):
    if report.status != "human_reviewed":
        return
    repo = CorpusRepository(root).load()
    required = {
        sha256_file(root / name)
        for name in ["data/cases.v1.jsonl", "data/stress.v1.jsonl", "data/gold.v1.jsonl"]
    }
    reviewed = {
        event.artifact_sha256
        for event in repo.review_events
        if event.kind == "human" and event.outcome == "accepted"
    }
    if not required <= reviewed or report.metrics is None or not report.hashes.get("annotations"):
        raise ValueError("Revue humaine complète non établie")
    if (
        report.review_status.get("outputs") != "human"
        or report.review_status.get("cohorts") != "complete"
    ):
        raise ValueError("Annotations humaines ou cohortes incomplètes")


def build_public_bundle(root: Path, results=None, report=None, output=None):
    repo = CorpusRepository(root).load()
    if results is None:
        results = json.loads((root / "data/illustrative-notes.v1.json").read_text())
    payload = dict(
        schema_version="1.0",
        consultations=[c.model_dump(mode="json") for c in repo.list_public_cases()],
        results={
            cid: {
                str(m): validate_published_result(r, repo.get_case(cid)).model_dump(mode="json")
                for m, r in results[cid].items()
            }
            for cid in DEMO_IDS
        },
        built_at=utc_now(),
    )
    bundle = validate_bundle(dict(**payload, content_sha256=sha256_json(payload)))
    report = report or PublishedReport(
        schema_version="1.0",
        status="awaiting_runs",
        cohort_sizes={
            "main": 60,
            "dev": 20,
            "test": 40,
            "stress_pairs": 10,
            "planned_main_outputs": 80,
            "planned_stress_outputs": 40,
            "recorded_outputs": 0,
        },
        review_status={"references": "ai_prepared_not_human_reviewed", "outputs": "not_annotated"},
        metrics=None,
        limitations=[
            "Corpus synthétique préparé par IA, sans revue humaine.",
            "Exemples éditoriaux illustratifs ; aucune performance de modèle mesurée.",
            "La comparaison porte sur les pipelines complets, avec deux modes de rédaction.",
        ],
        artifact_links={
            "protocol": "https://github.com/KenziBoughadou/medinote/blob/main/eval/protocol.v1.json"
        },
        hashes={"corpus": repo.corpus_sha256},
    )
    recorded = sum(
        result.origin == "llm_recorded"
        for methods in bundle.results.values()
        for result in methods.values()
    )
    if recorded == 12 and report.status == "awaiting_runs" and report.metrics is None:
        report = report.model_copy(
            update={
                "status": "awaiting_annotation",
                "cohort_sizes": {**report.cohort_sizes, "demo_recorded_outputs": recorded},
                "limitations": [
                    item
                    for item in report.limitations
                    if not item.startswith("Exemples éditoriaux illustratifs")
                ],
            }
        )
    validate_report_review(root, report)
    report = report.model_copy(
        update={"hashes": {**report.hashes, "bundle": bundle.content_sha256}}
    )
    output = output or root / "public-data"
    write_json(output / "bundle.v1.json", bundle)
    write_json(output / "report.v1.json", report)
    return bundle, report

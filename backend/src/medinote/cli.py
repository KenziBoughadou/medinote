import argparse
import asyncio
import json
from pathlib import Path

from medinote.config import Settings
from medinote.corpus import CorpusRepository
from medinote.errors import ServiceError
from medinote.serialization import canonical_json


def study_status(root):
    from medinote.publication import load_public

    bundle, report = load_public(root)
    return {
        "data": CorpusRepository(root).load().validate_corpus(),
        "real_demo_outputs": sum(
            r.origin == "llm_recorded"
            for methods in bundle.results.values()
            for r in methods.values()
        ),
        "ai_annotations": report.status == "ai_annotated",
        "human_review": report.status == "human_reviewed",
        "study_status": report.status,
        "publication": "external_verification_required",
    }


def parser():
    p = argparse.ArgumentParser(
        prog="medinote", description="Consultations synthétiques uniquement"
    )
    sub = p.add_subparsers(dest="command", required=True)
    corpus = sub.add_parser("corpus").add_subparsers(dest="action", required=True)
    corpus.add_parser("validate").add_argument("--root", type=Path, required=True)
    status = sub.add_parser("study-status")
    status.add_argument("--root", type=Path, required=True)
    ev = sub.add_parser("eval").add_subparsers(dest="action", required=True)
    freeze = ev.add_parser("freeze")
    freeze.add_argument("--root", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    run = ev.add_parser("run")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--suite", choices=["main-test", "stress", "demo"], required=True)
    run.add_argument("--output", type=Path, required=True)
    for name in ["export-blind", "import-annotations", "report"]:
        command = ev.add_parser(name)
        command.add_argument("--batch", type=Path, required=True)
        if name != "export-blind":
            command.add_argument("--annotations", type=Path, required=True)
        if name != "import-annotations":
            command.add_argument("--output", type=Path, required=True)
    publish = sub.add_parser("publish")
    publish.add_argument("--demo-batch", type=Path, required=True)
    publish.add_argument("--report", type=Path, required=True)
    publish.add_argument("--output", type=Path, required=True)
    ext = sub.add_parser("external").add_subparsers(dest="action", required=True)
    commands = {
        "freeze": ["--root", "--output"],
        "run": ["--manifest", "--output"],
        "judge": ["--manifest", "--batch", "--output"],
        "report": ["--batch", "--judgments", "--second", "--output"],
    }
    for name, options in commands.items():
        command = ext.add_parser(name)
        for option in options:
            command.add_argument(option, type=Path, required=True)
        if name == "run":
            command.add_argument("--split", choices=["dev", "test"], required=True)
        if name == "judge":
            command.add_argument("--role", choices=["primary", "secondary"], default="primary")
            command.add_argument("--primary", type=Path)
    return p


async def _run(settings, args):
    from medinote.evaluation.runner import run_batch
    from medinote.generation import GenerationService
    from medinote.usage import UsageStore

    if not settings.live_enabled:
        raise ServiceError("LIVE_DISABLED", "Clé et live autorisé requis.", 503)
    usage = UsageStore(settings.db_path)
    usage.initialize()
    service = GenerationService(settings, CorpusRepository(settings.root).load(), usage)
    try:
        return str(await run_batch(settings.root, args.manifest, args.suite, args.output, service))
    finally:
        await service.close()


async def _external_paid(settings, root, args):
    from medinote.external.campaign import require_production, run_generation, run_judging
    from medinote.external.llm import ExternalProvider
    from medinote.usage import UsageStore

    if not settings.live_enabled:
        raise ServiceError("LIVE_DISABLED", "Clé et live autorisé requis.", 503)
    require_production(settings)
    usage = UsageStore(settings.db_path)
    usage.initialize()
    provider = ExternalProvider(settings.openai_api_key.get_secret_value())
    try:
        if args.action == "run":
            output = await run_generation(
                root, args.manifest, args.split, args.output, usage, provider
            )
        else:
            output = await run_judging(
                root,
                args.manifest,
                args.batch,
                args.output,
                usage,
                provider,
                role=args.role,
                primary=args.primary,
            )
        return str(output)
    finally:
        await provider.close()


def _external(settings, root, args):
    from medinote.external import campaign, report

    if args.action == "freeze":
        return campaign.freeze_external(root, args.output).model_dump(mode="json")
    if args.action in {"run", "judge"}:
        return asyncio.run(_external_paid(settings, root, args))
    built = report.build_report(root, args.batch, args.judgments, args.second, args.output)
    return {key: built[key] for key in ["split", "consultations", "comparisons", "judge_agreement"]}


def _publish(settings, args):
    from medinote.corpus import DEMO_IDS
    from medinote.evaluation.blinding import safe_artifact
    from medinote.evaluation.runner import collect_runs
    from medinote.publication import build_public_bundle
    from medinote.schemas import GenerationResult, Method, PublishedReport

    runs = collect_runs(args.demo_batch, settings.root)
    if len(runs) != 12 or {(r.case_id, r.method) for r in runs} != {
        (cid, m) for cid in DEMO_IDS for m in Method
    }:
        raise ValueError("Douze vraies sorties dev exigées")
    results = {cid: {} for cid in DEMO_IDS}
    for run in runs:
        if run.status != "ok" or run.note_path is None or run.raw_response_path is None:
            raise ValueError("Sortie réelle complète requise")
        raw = json.loads(safe_artifact(args.demo_batch, run.raw_response_path).read_text())
        result = GenerationResult.model_validate_json(
            safe_artifact(args.demo_batch, run.note_path).read_text()
        )
        if (
            result.origin != "llm_recorded"
            or result.run_id != run.run_id
            or raw.get("model") != result.metadata.model_returned
        ):
            raise ValueError("Provenance de génération discordante")
        results[run.case_id][run.method] = result
    report = PublishedReport.model_validate_json((args.report / "report.v1.json").read_text())
    build_public_bundle(settings.root, results, report, args.output)
    return str(args.output)


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        settings = Settings.load()
        root = getattr(args, "root", settings.root).resolve()
        if args.command == "corpus":
            repo = CorpusRepository(root).load()
            result = repo.validate_corpus()
            from medinote.llm import build_generation_request
            from medinote.schemas import Method

            for case in repo.cases.values():
                for method in Method:
                    build_generation_request(case, method)
        elif args.command == "study-status":
            result = study_status(root)
        elif args.command == "publish":
            result = _publish(settings, args)
        elif args.command == "external":
            result = _external(settings, root, args)
        elif args.action == "freeze":
            from medinote.evaluation.freeze import freeze_manifest

            result = freeze_manifest(root, args.output).model_dump(mode="json")
        elif args.action == "run":
            result = asyncio.run(_run(settings, args))
        elif args.action == "export-blind":
            from medinote.evaluation.blinding import export_blind_bundle

            mapping = export_blind_bundle(root, args.batch, args.output)
            result = {"outputs": len(mapping), "output": str(args.output)}
        elif args.action == "import-annotations":
            from medinote.evaluation.blinding import import_annotations

            result = str(import_annotations(root, args.batch, args.annotations))
        else:
            from medinote.evaluation.report import build_report

            result = build_report(root, args.batch, args.annotations, args.output).model_dump(
                mode="json"
            )
        print(canonical_json(result))
        return 0
    except ServiceError as exc:
        print(canonical_json({"error": exc.code, "message": exc.message}))
        interrupted = (
            args.command in {"eval", "external"}
            and args.action in {"run", "judge"}
            and args.output.exists()
        )
        return 4 if interrupted else 3
    except (ValueError, AssertionError, KeyError, OSError) as exc:
        print(canonical_json({"error": "INVALID_INPUT", "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Gel, générations et jugements de l'étude externe ACI-Bench."""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import ValidationError

from medinote.errors import ServiceError
from medinote.external.aci import SOURCE, SOURCE_COMMIT, SPLITS, load_split
from medinote.external.llm import (
    ATTEMPT_TIMEOUT_SECONDS,
    GENERATOR_MODEL,
    JUDGE_MODEL,
    JUDGE_TYPES,
    JUDGES,
    MAX_OUTPUT_TOKENS,
    OUTPUT_TYPES,
    SECOND_JUDGE_MODEL,
    cost_micro_usd,
    coverage_request,
    generation_request,
    pricing,
    reference_facts_request,
    support_request,
)
from medinote.external.rendering import render_output
from medinote.external.schemas import ExternalNote, ExternalRun, JudgeRecord, Model
from medinote.schemas import Method
from medinote.serialization import canonical_json, sha256_file, utc_now, write_json

FROZEN_GLOBS = [
    "backend/src/medinote/external/*.py",
    "backend/src/medinote/external/prompts/*",
    "eval/external/*.json",
    "eval/external/*.md",
]
FROZEN_FILES = [
    "backend/src/medinote/usage.py",
    "uv.lock",
    *[f"data/external/aci-bench/{name}" for name, _ in SPLITS.values()],
]
JUDGE_ATTEMPTS = 3
LEASE_WAITS = 60


class ExternalManifest(Model):
    schema_version: Literal["2.0"]
    created_at: str
    code_sha: str
    source: dict[str, str]
    files: dict[str, str]
    parameters: dict
    suites: dict[str, list[tuple[str, Method]]]


def frozen_paths(root):
    paths = [p for pattern in FROZEN_GLOBS for p in sorted(root.glob(pattern)) if p.is_file()]
    return sorted({str(p.relative_to(root)) for p in paths} | set(FROZEN_FILES))


def freeze_external(root, output):
    root = Path(root)
    paths = frozen_paths(root)
    code_sha = os.environ.get("MEDINOTE_BUILD_SHA", "")
    if not code_sha or code_sha == "development":
        code_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        if subprocess.check_output(
            ["git", "status", "--porcelain", "--", *paths], cwd=root, text=True
        ).strip():
            raise ValueError("Les entrées du gel doivent correspondre au commit")
    suites = {}
    for split in SPLITS:
        ids = [c.case_id for c in load_split(root, split)]
        # Même alternance que la v1 : A puis B, puis B puis A.
        suites[split] = [
            (cid, m)
            for i, cid in enumerate(ids)
            for m in (list(Method) if i % 2 == 0 else list(reversed(Method)))
        ]
    manifest = ExternalManifest(
        schema_version="2.0",
        created_at=utc_now(),
        code_sha=code_sha,
        source={"url": SOURCE, "commit": SOURCE_COMMIT},
        files={p: sha256_file(root / p) for p in paths},
        parameters={
            "generator_model": GENERATOR_MODEL,
            "judge_model": JUDGE_MODEL,
            "second_judge_model": SECOND_JUDGE_MODEL,
            "temperature": {"generator": 0, "judge": 0, "second_judge": "non supportée"},
            "second_judge_reasoning_effort": "low",
            "store": False,
            "max_output_tokens": {k: v for k, v in MAX_OUTPUT_TOKENS.items()},
            "attempt_timeout_seconds": ATTEMPT_TIMEOUT_SECONDS,
            "generation_attempts": 1,
            "judge_attempts": JUDGE_ATTEMPTS,
        },
        suites=suites,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError("Un gel existant n'est jamais remplacé")
    write_json(output, manifest)
    return manifest


def verify_external_manifest(root, path):
    manifest = ExternalManifest.model_validate_json(Path(path).read_text())
    for name, expected in manifest.files.items():
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not (root / relative).is_file()
            or sha256_file(root / relative) != expected
        ):
            raise ValueError(f"Entrée figée altérée : {name}")
    if set(manifest.files) != set(frozen_paths(Path(root))):
        raise ValueError("Fichiers de l'étude externe ajoutés ou retirés depuis le gel")
    return manifest


def append_jsonl(path, value):
    with path.open("a", encoding="utf-8") as f:
        f.write(canonical_json(value) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_jsonl(path, model):
    if not path.exists():
        return []
    return [model.model_validate_json(line) for line in path.read_text().splitlines() if line]


async def call(usage, provider, request, case_id, label):
    for _ in range(LEASE_WAITS):
        try:
            job_id = usage.acquire_lease("experiment", case_id, label)
            break
        except ServiceError as exc:
            # La démo publique partage le bail : on attend sans rien réserver.
            if exc.code != "SERVER_BUSY":
                raise
            await asyncio.sleep(5)
    else:
        raise ServiceError("SERVER_BUSY", "Bail de génération indisponible.", 429)
    status = "failed"
    try:
        attempt_id = usage.reserve_attempt(job_id, amount=request.reservation_micro_usd)
        try:
            result = await provider.generate(request)
        except BaseException:
            usage.mark_unknown(attempt_id, "INTERRUPTED")
            raise
        usage.settle_attempt(
            attempt_id,
            result.input_tokens,
            result.output_tokens,
            result.error_code,
            pricing=pricing(request.model),
        )
        status = result.status
        return result
    finally:
        usage.release_lease(job_id, status)


def usd(model, result):
    cost = cost_micro_usd(model, result.input_tokens, result.output_tokens)
    return cost / 1e6 if cost is not None else None


async def run_generation(root, manifest_path, split, output, usage, provider):
    root = Path(root)
    manifest = verify_external_manifest(root, manifest_path)
    manifest_hash = sha256_file(manifest_path)
    cases = {c.case_id: c for c in load_split(root, split)}
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "frozen-manifest.json", manifest)
    write_json(
        output / "run-manifest.json",
        {"split": split, "manifest_sha256": manifest_hash, "started_at": utc_now()},
    )
    for case_id, method in manifest.suites[split]:
        verify_external_manifest(root, manifest_path)
        case = cases[case_id]
        request = generation_request(case, method)
        run_id = uuid4().hex
        started = utc_now()
        result = await call(usage, provider, request, case_id, f"external-{method}")
        status, error_code, note = result.status, result.error_code, None
        if status == "ok":
            try:
                output_model = OUTPUT_TYPES[method].model_validate_json(result.output_text or "")
                note = render_output(case, method, output_model)
            except (ValidationError, ValueError):
                status, error_code = "schema_error", "INVALID_OUTPUT"
        raw_path = f"raw/{run_id}.json" if result.raw_json is not None else None
        note_path = f"notes/{run_id}.json" if note else None
        if raw_path:
            write_json(output / raw_path, result.raw_json)
        if note_path:
            write_json(output / note_path, note)
        append_jsonl(
            output / "runs.jsonl",
            ExternalRun(
                run_id=run_id,
                manifest_sha256=manifest_hash,
                split=split,
                case_id=case_id,
                method=method,
                status=status,
                error_code=error_code,
                model_requested=request.model,
                model_returned=result.model_returned,
                started_at=started,
                duration_ms=result.duration_ms,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                estimated_cost_usd=usd(request.model, result),
                raw_response_path=raw_path,
                note_path=note_path,
                note_sha256=note.note_sha256 if note else None,
            ),
        )
    write_json(output / "completed.json", {"finished_at": utc_now()})
    return output


def load_batch(batch):
    runs = read_jsonl(batch / "runs.jsonl", ExternalRun)
    if not runs or not (batch / "completed.json").exists():
        raise ValueError("Campagne de génération incomplète")
    if len({(r.case_id, r.method) for r in runs}) != len(runs):
        raise ValueError("Plusieurs générations pour un même cas et une même méthode")
    if {r.manifest_sha256 for r in runs} != {sha256_file(batch / "frozen-manifest.json")}:
        raise ValueError("Générations issues d'un autre gel")
    notes = {}
    for run in runs:
        if run.note_path:
            note = ExternalNote.model_validate_json((batch / run.note_path).read_text())
            if note.note_sha256 != run.note_sha256:
                raise ValueError("Note archivée altérée")
            notes[(run.case_id, run.method)] = note
    return runs, notes


def _valid_judgment(task, output, expected):
    if task == "reference_facts":
        return bool(output.facts)
    return sorted(j.index for j in output.judgments) == list(range(1, expected + 1))


async def judge(
    usage, provider, records_path, done, task, case_id, method, note, request, expected
):
    key = (task, case_id, method)
    if key in done:
        return done[key]
    for attempt in range(1, JUDGE_ATTEMPTS + 1):
        result = await call(usage, provider, request, case_id, f"judge-{task}")
        status, error_code, parsed = result.status, result.error_code, None
        if status == "ok":
            try:
                parsed = JUDGE_TYPES[task].model_validate_json(result.output_text or "")
                if not _valid_judgment(task, parsed, expected):
                    raise ValueError("Jugements incomplets ou dupliqués")
            except (ValidationError, ValueError):
                status, error_code, parsed = "schema_error", "INVALID_OUTPUT", None
        record = JudgeRecord(
            task=task,
            case_id=case_id,
            method=method,
            note_sha256=note.note_sha256 if note else None,
            attempt=attempt,
            status=status,
            error_code=error_code,
            model_returned=result.model_returned,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            estimated_cost_usd=usd(request.model, result),
            output=parsed.model_dump(mode="json") if parsed else None,
        )
        append_jsonl(records_path, record)
        if parsed:
            done[key] = record
            return record
    raise ValueError(f"Jugement impossible après {JUDGE_ATTEMPTS} tentatives : {key}")


def final_judgments(path):
    final = {}
    for record in read_jsonl(path, JudgeRecord):
        if record.output is not None:
            final[(record.task, record.case_id, record.method)] = record
    return final


async def run_judging(
    root, manifest_path, batch, output, usage, provider, role="primary", primary=None
):
    root = Path(root)
    model = JUDGES[role]
    manifest = verify_external_manifest(root, manifest_path)
    if sha256_file(batch / "frozen-manifest.json") != sha256_file(manifest_path):
        raise ValueError("Le juge doit utiliser le gel des générations")
    runs, notes = load_batch(batch)
    split = runs[0].split
    cases = {c.case_id: c for c in load_split(root, split)}
    if role == "secondary":
        # Le second juge note exactement les faits de référence découpés par le premier.
        if primary is None or not (primary / "completed.json").exists():
            raise ValueError("Le second juge exige les jugements terminés du premier")
        primary_records = final_judgments(primary / "judgments.jsonl")
    output.mkdir(parents=True, exist_ok=True)
    records_path = output / "judgments.jsonl"
    # Une reprise réutilise les jugements terminés et ne paie que ceux qui manquent.
    done = final_judgments(records_path)
    for case_id in sorted({cid for cid, _ in manifest.suites[split]}):
        if role == "secondary":
            facts_record = primary_records[("reference_facts", case_id, None)]
        else:
            facts_record = await judge(
                usage,
                provider,
                records_path,
                done,
                "reference_facts",
                case_id,
                None,
                None,
                reference_facts_request(cases[case_id]),
                None,
            )
        facts = JUDGE_TYPES["reference_facts"].model_validate(facts_record.output).facts
        for method in Method:
            note = notes.get((case_id, method))
            if note is None:
                continue
            verify_external_manifest(root, manifest_path)
            await judge(
                usage,
                provider,
                records_path,
                done,
                "coverage",
                case_id,
                method,
                note,
                coverage_request(note, facts, model),
                len(facts),
            )
            if note.assertions:
                await judge(
                    usage,
                    provider,
                    records_path,
                    done,
                    "support",
                    case_id,
                    method,
                    note,
                    support_request(cases[case_id], note, model),
                    len(note.assertions),
                )
    write_json(
        output / "completed.json",
        {
            "finished_at": utc_now(),
            "batch_manifest_sha256": sha256_file(manifest_path),
            "role": role,
            "model": model,
        },
    )
    return output


def require_production(settings):
    if settings.env != "production" or settings.db_path != Path("/var/lib/medinote/usage.sqlite3"):
        raise ServiceError(
            "SHARED_BUDGET_REQUIRED",
            "Les campagnes réelles utilisent la comptabilité de production.",
            503,
        )

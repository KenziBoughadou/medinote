import json
import os
from uuid import uuid4

from medinote.errors import ServiceError
from medinote.evaluation.freeze import verify_manifest
from medinote.evaluation.schemas import ExperimentRun
from medinote.llm import estimated_micro_usd
from medinote.serialization import canonical_json, sha256_file, utc_now, write_json


def append_jsonl(path, value):
    with path.open("a", encoding="utf-8") as f:
        f.write(canonical_json(value) + "\n")
        f.flush()
        os.fsync(f.fileno())


def persist_run(output, run, raw, result):
    if raw is not None:
        write_json(output / run.raw_response_path, raw)
    if result is not None:
        write_json(output / run.note_path, result)
    append_jsonl(output / "raw-responses.jsonl", {"run_id": run.run_id, "response": raw})
    append_jsonl(
        output / "notes.jsonl",
        {"run_id": run.run_id, "result": result.model_dump(mode="json") if result else None},
    )
    artifact_hashes = dict(run.hashes)
    if run.raw_response_path:
        artifact_hashes["raw_response_file"] = sha256_file(output / run.raw_response_path)
    if run.note_path:
        artifact_hashes["note_file"] = sha256_file(output / run.note_path)
        artifact_hashes["note_text"] = result.note.note_sha256
    run = run.model_copy(update={"hashes": artifact_hashes})
    append_jsonl(output / "runs.jsonl", run)


async def run_batch(root, manifest_path, suite, output, service):
    manifest = verify_manifest(root, manifest_path)
    service._check_live()
    output.mkdir(parents=True, exist_ok=False)
    batch_id = uuid4().hex
    manifest_hash = sha256_file(manifest_path)
    write_json(output / "frozen-manifest.json", manifest)
    write_json(
        output / "run-manifest.json",
        {
            "schema_version": "1.0",
            "batch_id": batch_id,
            "suite": suite,
            "manifest_sha256": manifest_hash,
            "planned": len(manifest.suites[suite]),
            "started_at": utc_now(),
            "order": manifest.suites[suite],
            "status": "running",
        },
    )
    for cid, method in manifest.suites[suite]:
        verify_manifest(root, manifest_path)
        run_id = uuid4().hex
        started = utc_now()
        try:
            execution = await service.generate_experiment(cid, method)
        except ServiceError as exc:
            # Budget/lease failures are campaign interruptions, not paid observations.
            write_json(
                output / "interrupted.json",
                {"case_id": cid, "method": method, "code": exc.code, "at": utc_now()},
            )
            raise
        outcome = execution.outcomes[0]
        p = outcome.provider
        cost = estimated_micro_usd(p.input_tokens, p.output_tokens)
        run = ExperimentRun(
            batch_id=batch_id,
            run_id=execution.result.run_id if execution.result else run_id,
            case_id=cid,
            method=method,
            manifest_sha256=manifest_hash,
            hashes=manifest.files,
            model_requested=manifest.parameters["model"],
            model_returned=p.model_returned,
            parameters=manifest.parameters,
            started_at=started,
            duration_ms=execution.duration_ms,
            input_tokens=p.input_tokens,
            output_tokens=p.output_tokens,
            estimated_cost_usd=cost / 1e6 if cost is not None else None,
            status=outcome.status,
            error_code=outcome.error_code,
            raw_response_path=f"raw/{run_id}.json" if p.raw_json is not None else None,
            note_path=f"notes/{run_id}.json" if execution.result else None,
        )
        persist_run(output, run, p.raw_json, execution.result)
    write_json(
        output / "completed.json",
        {"finished_at": utc_now(), "planned": len(manifest.suites[suite])},
    )
    run_manifest = json.loads((output / "run-manifest.json").read_text())
    run_manifest["status"] = "completed"
    write_json(output / "run-manifest.json", run_manifest)
    return output


def collect_runs(batch, root=None):
    from medinote.corpus import read_jsonl

    paths = (
        [batch / "runs.jsonl"]
        if (batch / "runs.jsonl").exists()
        else sorted(batch.glob("*/runs.jsonl"))
    )
    if not paths:
        raise ValueError("Aucune campagne enregistrée")
    runs = []
    for path in paths:
        frozen_path = path.parent / "frozen-manifest.json"
        if root is not None:
            verify_manifest(root, frozen_path)
        frozen_hash = sha256_file(frozen_path)
        prefix = path.parent.relative_to(batch)
        for run in read_jsonl(path, ExperimentRun):
            if run.manifest_sha256 != frozen_hash:
                raise ValueError("Hash du gel archivé discordant")
            for attribute, hash_key in [
                ("note_path", "note_file"),
                ("raw_response_path", "raw_response_file"),
            ]:
                artifact = getattr(run, attribute)
                if artifact is not None:
                    from medinote.evaluation.blinding import safe_artifact

                    if sha256_file(safe_artifact(path.parent, artifact)) != run.hashes.get(
                        hash_key
                    ):
                        raise ValueError("Hash de sortie archivée discordant")
            updates = {
                key: str(prefix / getattr(run, key)) if getattr(run, key) else None
                for key in ["note_path", "raw_response_path"]
            }
            runs.append(run.model_copy(update=updates))
    if len({r.run_id for r in runs}) != len(runs):
        raise ValueError("Exécution dupliquée")
    if len({r.manifest_sha256 for r in runs}) != 1:
        raise ValueError("Campagnes issues de gels différents")
    if len({(r.case_id, r.method) for r in runs}) != len(runs):
        raise ValueError("Plusieurs observations du même cas/méthode")
    return runs

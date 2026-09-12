import json
import random
from pathlib import Path
from uuid import uuid4

from medinote.corpus import CorpusRepository, read_jsonl
from medinote.evaluation.alignment import validate_alignment, validate_annotation_completeness
from medinote.evaluation.schemas import Annotation
from medinote.schemas import GenerationResult
from medinote.serialization import canonical_json, sha256_file, sha256_json, write_json


def safe_artifact(batch, name):
    p = Path(name)
    if p.is_absolute() or ".." in p.parts or (batch / p).is_symlink():
        raise ValueError("Chemin d’artefact invalide")
    return batch / p


def export_blind_bundle(root, batch, output):
    repo = CorpusRepository(root).load()
    from medinote.evaluation.runner import collect_runs

    runs = collect_runs(batch, root)
    random.Random(20260911).shuffle(runs)
    output.mkdir(parents=True, exist_ok=False)
    mapping = {}
    forms = []
    for i, run in enumerate(runs, 1):
        blind = f"blind-{i:04}"
        mapping[blind] = {
            "run_id": run.run_id,
            "case_id": run.case_id,
            "method": run.method,
            "note_path": run.note_path,
        }
        if run.status != "ok":
            continue
        result = GenerationResult.model_validate_json(
            safe_artifact(batch, run.note_path).read_text()
        )
        gold = [f for f in repo.gold if f.case_id == run.case_id]
        note = result.note.model_dump(mode="json")
        write_json(
            output / f"{blind}.json",
            {
                "blind_output_id": blind,
                "note": note,
                "source": repo.get_case(run.case_id).model_dump(mode="json"),
                "gold": [f.model_dump(mode="json") for f in gold],
            },
        )
        forms.append(
            dict(
                annotation_id=uuid4().hex,
                blind_output_id=blind,
                note_sha256=result.note.note_sha256,
                gold_sha256=sha256_json([f.model_dump(mode="json") for f in gold]),
                guide_sha256=sha256_file(root / "eval/annotation-guide.v1.md"),
                annotator={
                    "kind": "human",
                    "id": "À RENSEIGNER PAR LE RELECTEUR",
                    "model_snapshot": None,
                    "prompt_sha256": None,
                },
                status="draft",
                claims=[],
                gold_assessments=[],
                segmentation_review_complete=False,
                comments="Formulaire vierge : aucune revue effectuée.",
            )
        )
    (output / "annotations-template.jsonl").write_text(
        "".join(canonical_json(a) + "\n" for a in forms)
    )
    private = batch / "private"
    private.mkdir(mode=0o700, exist_ok=True)
    map_path = private / "blind-mapping.json"
    with map_path.open("x") as f:
        f.write(canonical_json(mapping) + "\n")
    map_path.chmod(0o600)
    return mapping


def load_validated_annotations(root, batch, path):
    from medinote.evaluation.runner import collect_runs

    collect_runs(batch, root)
    repo = CorpusRepository(root).load()
    mapping = json.loads((batch / "private/blind-mapping.json").read_text())
    annotations = read_jsonl(path, Annotation)
    seen = set()
    ids = set()
    result = {}
    for annotation in annotations:
        if annotation.blind_output_id in seen or annotation.annotation_id in ids:
            raise ValueError("Annotation dupliquée")
        seen.add(annotation.blind_output_id)
        ids.add(annotation.annotation_id)
        if annotation.blind_output_id not in mapping:
            raise ValueError("Sortie aveugle inconnue")
        mapped = mapping[annotation.blind_output_id]
        if not mapped["note_path"]:
            raise ValueError("Pas de note à annoter pour un échec")
        note = GenerationResult.model_validate_json(
            safe_artifact(batch, mapped["note_path"]).read_text()
        ).note
        gold = [f for f in repo.gold if f.case_id == mapped["case_id"]]
        validate_annotation_completeness(annotation)
        validate_alignment(
            annotation,
            note,
            gold,
            repo.get_case(mapped["case_id"]),
            sha256_file(root / "eval/annotation-guide.v1.md"),
        )
        result[mapped["run_id"]] = annotation
    required = {k for k, v in mapping.items() if v["note_path"]}
    if seen != required:
        raise ValueError("Toutes les notes finales doivent être annotées")
    return result


def import_annotations(root, batch, path):
    annotations = load_validated_annotations(root, batch, path)
    directory = batch / "annotations"
    directory.mkdir(exist_ok=True)
    incoming = {a.annotation_id: a for a in annotations.values()}
    for previous in directory.glob("*.jsonl"):
        for annotation in read_jsonl(previous, Annotation):
            if (
                annotation.annotation_id in incoming
                and annotation.annotator != incoming[annotation.annotation_id].annotator
            ):
                raise ValueError("Provenance d’une annotation existante non modifiable")
    target = directory / f"{sha256_file(path)}.jsonl"
    with target.open("x") as f:
        f.write("".join(canonical_json(a) + "\n" for a in annotations.values()))
    return target

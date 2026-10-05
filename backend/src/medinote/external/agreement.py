"""Accord entre les deux juges automatiques, élément par élément."""

from medinote.external.schemas import CoverageOutput, SupportOutput

COVERAGE_LABELS = ["covered", "contradicted", "omitted"]
SUPPORT_LABELS = ["supported", "contradicted", "unsupported"]
CITATION_LABELS = ["true", "false"]
RELIABLE_AC1 = 0.6


def cohen_kappa(pairs, labels):
    n = len(pairs)
    if n == 0:
        return None
    observed = sum(a == b for a, b in pairs) / n
    first = {label: sum(a == label for a, _ in pairs) for label in labels}
    second = {label: sum(b == label for _, b in pairs) for label in labels}
    expected = sum(first[label] * second[label] for label in labels) / n**2
    return None if expected == 1 else (observed - expected) / (1 - expected)


def gwet_ac1(pairs, labels):
    # Contrairement au kappa, l'AC1 reste stable quand une étiquette domine largement.
    n = len(pairs)
    if n == 0 or len(labels) < 2:
        return None
    observed = sum(a == b for a, b in pairs) / n
    prevalence = [sum((a == label) + (b == label) for a, b in pairs) / (2 * n) for label in labels]
    expected = sum(p * (1 - p) for p in prevalence) / (len(labels) - 1)
    return (observed - expected) / (1 - expected)


def agreement(pairs, labels):
    return {
        "items": len(pairs),
        "agreement": sum(a == b for a, b in pairs) / len(pairs) if pairs else None,
        "gwet_ac1": gwet_ac1(pairs, labels),
        "cohen_kappa": cohen_kappa(pairs, labels),
        "confusion_primary_by_secondary": {
            first: {second: sum((a, b) == (first, second) for a, b in pairs) for second in labels}
            for first in labels
        },
    }


def _judgments(record, note, output_type):
    if record.note_sha256 != note.note_sha256:
        raise ValueError("Jugement d'une autre note")
    return {j.index: j for j in output_type.model_validate(record.output).judgments}


def judge_agreement(primary, secondary, notes):
    pairs = {"coverage": [], "support": [], "citations": []}
    for (case_id, method), note in sorted(notes.items()):
        tasks = [("coverage", CoverageOutput)]
        if note.assertions:
            tasks.append(("support", SupportOutput))
        for task, output_type in tasks:
            first = _judgments(primary[(task, case_id, method)], note, output_type)
            second = _judgments(secondary[(task, case_id, method)], note, output_type)
            for index in sorted(first):
                pairs[task].append((first[index].label, second[index].label))
                if task == "support":
                    pairs["citations"].append(
                        (
                            str(first[index].citations_support).lower(),
                            str(second[index].citations_support).lower(),
                        )
                    )
    result = {
        "coverage": agreement(pairs["coverage"], COVERAGE_LABELS),
        "support": agreement(pairs["support"], SUPPORT_LABELS),
        "citations": agreement(pairs["citations"], CITATION_LABELS),
    }
    scores = [result[task]["gwet_ac1"] for task in ["coverage", "support"]]
    result["reliable"] = all(score is not None and score >= RELIABLE_AC1 for score in scores)
    result["rule"] = (
        f"AC1 de Gwet >= {RELIABLE_AC1} entre les deux juges pour la couverture et l'appui"
    )
    return result

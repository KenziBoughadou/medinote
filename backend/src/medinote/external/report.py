"""Métriques de l'étude externe, calculées sans nouvel appel au modèle."""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

from medinote.external.aci import load_split
from medinote.external.agreement import judge_agreement
from medinote.external.campaign import final_judgments, load_batch
from medinote.external.schemas import CoverageOutput, ReferenceFactsOutput, SupportOutput
from medinote.schemas import Method
from medinote.serialization import utc_now, write_json

RATIOS = {
    "coverage": ("covered", "expected"),
    "omission": ("omitted", "expected"),
    "expected_contradiction": ("contradicted_expected", "expected"),
    "unsupported": ("unsupported", "assertions"),
    "contradiction": ("contradicted_assertions", "assertions"),
    "citation_support": ("citations_ok", "assertions"),
    "technical_reliability": ("valid", "planned"),
}
SEED = 20261005
REPLICATIONS = 10_000


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def rouge_n(candidate, reference, n):
    def grams(words):
        return Counter(tuple(words[i : i + n]) for i in range(len(words) - n + 1))

    c, r = grams(candidate), grams(reference)
    overlap = sum((c & r).values())
    if not overlap:
        return 0.0
    precision, recall = overlap / sum(c.values()), overlap / sum(r.values())
    return 2 * precision * recall / (precision + recall)


def rouge_l(candidate, reference):
    if not candidate or not reference:
        return 0.0
    previous = [0] * (len(reference) + 1)
    for word in candidate:
        current = [0]
        for j, ref_word in enumerate(reference, 1):
            current.append(
                previous[j - 1] + 1 if word == ref_word else max(previous[j], current[j - 1])
            )
        previous = current
    lcs = previous[-1]
    if not lcs:
        return 0.0
    precision, recall = lcs / len(candidate), lcs / len(reference)
    return 2 * precision * recall / (precision + recall)


def rouge(candidate_text, reference_text):
    candidate, reference = tokens(candidate_text), tokens(reference_text)
    return {
        "rouge1": rouge_n(candidate, reference, 1),
        "rouge2": rouge_n(candidate, reference, 2),
        "rougeL": rouge_l(candidate, reference),
    }


def note_counts(facts, run, note, coverage, support):
    counts = Counter(expected=len(facts), planned=1)
    if note is None:
        # Une génération échouée n'a repris aucun fait : même règle que la v1.
        counts["omitted"] = len(facts)
        return dict(counts)
    counts["valid"] = 1
    for judgment in coverage.judgments:
        counts[
            {"covered": "covered", "contradicted": "contradicted_expected", "omitted": "omitted"}[
                judgment.label
            ]
        ] += 1
    counts["assertions"] = len(note.assertions)
    if support is not None:
        for judgment in support.judgments:
            counts[
                {
                    "supported": "supported",
                    "contradicted": "contradicted_assertions",
                    "unsupported": "unsupported",
                }[judgment.label]
            ] += 1
            counts["citations_ok"] += judgment.citations_support
    counts["unresolved_citations"] = sum(len(a.unresolved_ids) for a in note.assertions)
    return dict(counts)


def ratio(counts, name):
    numerator, denominator = RATIOS[name]
    return counts.get(numerator, 0) / counts[denominator] if counts.get(denominator) else None


def paired_bootstrap(rows_a, rows_b):
    n = len(rows_a)
    rng = np.random.Generator(np.random.PCG64(SEED))
    indices = rng.integers(0, n, size=(REPLICATIONS, n))
    comparisons = {}
    for name, (num, den) in RATIOS.items():
        a = np.array([[r.get(num, 0), r.get(den, 0)] for r in rows_a], dtype=float)
        b = np.array([[r.get(num, 0), r.get(den, 0)] for r in rows_b], dtype=float)
        sa, sb = a[indices].sum(axis=1), b[indices].sum(axis=1)
        valid = (sa[:, 1] > 0) & (sb[:, 1] > 0)
        diff = sb[valid, 0] / sb[valid, 1] - sa[valid, 0] / sa[valid, 1]
        total_a, total_b = a.sum(axis=0), b.sum(axis=0)
        value_a = total_a[0] / total_a[1] if total_a[1] else None
        value_b = total_b[0] / total_b[1] if total_b[1] else None
        defined = valid.mean() >= 0.95
        low, high = np.percentile(diff, [2.5, 97.5]).tolist() if defined else (None, None)
        comparisons[name] = {
            "a": value_a,
            "b": value_b,
            "difference": value_b - value_a if None not in (value_a, value_b) else None,
            "ci95_low": low,
            "ci95_high": high,
        }
    return comparisons, indices


def paired_mean_bootstrap(values_a, values_b, indices, statistic=np.mean):
    a, b = np.array(values_a, dtype=float), np.array(values_b, dtype=float)
    diffs = [statistic(b[i]) - statistic(a[i]) for i in indices]
    low, high = np.percentile(diffs, [2.5, 97.5]).tolist()
    return {
        "a": float(statistic(a)),
        "b": float(statistic(b)),
        "difference": float(statistic(b) - statistic(a)),
        "ci95_low": low,
        "ci95_high": high,
    }


def judged_rows(cases, runs, notes, facts_records, judge_records):
    by_key = {(r.case_id, r.method): r for r in runs}
    rows = {m: [] for m in Method}
    per_note = []
    for case_id in sorted({r.case_id for r in runs}):
        facts = ReferenceFactsOutput.model_validate(
            facts_records[("reference_facts", case_id, None)].output
        ).facts
        for method in Method:
            run, note = by_key[(case_id, method)], notes.get((case_id, method))
            coverage = support = None
            if note is not None:
                record = judge_records[("coverage", case_id, method)]
                if record.note_sha256 != note.note_sha256:
                    raise ValueError("Jugement d'une autre note")
                coverage = CoverageOutput.model_validate(record.output)
                if note.assertions:
                    support = SupportOutput.model_validate(
                        judge_records[("support", case_id, method)].output
                    )
            counts = note_counts(facts, run, note, coverage, support)
            rows[method].append(counts)
            per_note.append(
                {
                    "case_id": case_id,
                    "subset": cases[case_id].subset,
                    "method": method,
                    "status": run.status,
                    "counts": counts,
                    "rouge": rouge(note.text if note else "", cases[case_id].reference_note),
                    "cost_usd": run.estimated_cost_usd,
                    "duration_ms": run.duration_ms,
                }
            )
    return rows, per_note


def totals(rows):
    result = {}
    for method in Method:
        total = Counter()
        for row in rows[method]:
            total.update(row)
        result[method] = dict(total)
    return result


def completed_judgments(directory, role):
    directory = Path(directory)
    completed = directory / "completed.json"
    if not completed.exists() or json.loads(completed.read_text()).get("role") != role:
        raise ValueError(f"Jugements incomplets ou d'un autre rôle : {role}")
    return final_judgments(directory / "judgments.jsonl")


def build_report(root, batch, judgments_dir, second_dir, output):
    runs, notes = load_batch(Path(batch))
    split = runs[0].split
    cases = {c.case_id: c for c in load_split(root, split)}
    final = completed_judgments(judgments_dir, "primary")
    second = completed_judgments(second_dir, "secondary")
    rows, per_note = judged_rows(cases, runs, notes, final, final)
    second_rows, second_per_note = judged_rows(cases, runs, notes, final, second)
    for note, other in zip(per_note, second_per_note, strict=True):
        note["counts_second_judge"] = other["counts"]
    comparisons, indices = paired_bootstrap(rows[Method.direct], rows[Method.structured])
    second_comparisons, _ = paired_bootstrap(
        second_rows[Method.direct], second_rows[Method.structured]
    )

    def series(method, getter):
        return [getter(n) for n in per_note if n["method"] == method]

    for name in ["rouge1", "rouge2", "rougeL"]:
        comparisons[name] = paired_mean_bootstrap(
            series(Method.direct, lambda n: n["rouge"][name]),
            series(Method.structured, lambda n: n["rouge"][name]),
            indices,
        )
    if all(n["cost_usd"] is not None for n in per_note):
        comparisons["cost_usd_mean"] = paired_mean_bootstrap(
            series(Method.direct, lambda n: n["cost_usd"]),
            series(Method.structured, lambda n: n["cost_usd"]),
            indices,
        )
    comparisons["latency_s_median"] = paired_mean_bootstrap(
        series(Method.direct, lambda n: n["duration_ms"] / 1000),
        series(Method.structured, lambda n: n["duration_ms"] / 1000),
        indices,
        statistic=np.median,
    )
    report = {
        "schema_version": "2.0",
        "created_at": utc_now(),
        "split": split,
        "consultations": len({r.case_id for r in runs}),
        "counts": totals(rows),
        "comparisons": comparisons,
        "second_judge": {"counts": totals(second_rows), "comparisons": second_comparisons},
        "judge_agreement": judge_agreement(final, second, notes),
        "per_note": per_note,
        "generation_cost_usd": sum(r.estimated_cost_usd or 0 for r in runs),
        "judge_cost_usd_final_records": sum(
            r.estimated_cost_usd or 0 for r in [*final.values(), *second.values()]
        ),
        "bootstrap": {"replications": REPLICATIONS, "seed": SEED, "generator": "PCG64"},
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "report.json", report)
    (output / "report.md").write_text(markdown(report), encoding="utf-8")
    return report


LABELS = {
    "coverage": "Faits de référence repris",
    "omission": "Faits de référence omis",
    "expected_contradiction": "Faits de référence contredits",
    "unsupported": "Assertions sans appui dans le dialogue",
    "contradiction": "Assertions contredisant le dialogue",
    "citation_support": "Assertions dont les citations suffisent",
    "technical_reliability": "Générations valides",
}


def _pct(value):
    return "—" if value is None else f"{100 * value:.2f} %"


def markdown(report):
    c = report["comparisons"]
    lines = [
        f"# Étude externe ACI-Bench : partition {report['split']}",
        "",
        f"{report['consultations']} consultations, une note par méthode. Jugement automatique "
        "par un modèle distinct du générateur, contrôlé par un second juge ; intervalles par "
        "bootstrap apparié "
        f"({report['bootstrap']['replications']} tirages).",
        "",
        "| Mesure | A, direct | B, structuré | Écart B−A [IC 95 %] |",
        "|---|---:|---:|---|",
    ]
    for name, label in LABELS.items():
        m = c[name]
        interval = (
            "non défini"
            if m["ci95_low"] is None
            else f"[{100 * m['ci95_low']:+.2f} ; {100 * m['ci95_high']:+.2f}] points"
        )
        difference = "—" if m["difference"] is None else f"{100 * m['difference']:+.2f} points"
        lines.append(f"| {label} | {_pct(m['a'])} | {_pct(m['b'])} | {difference} {interval} |")
    for name, label in [("rouge1", "ROUGE-1"), ("rouge2", "ROUGE-2"), ("rougeL", "ROUGE-L")]:
        m = c[name]
        lines.append(
            f"| {label} F1 "
            f"| {m['a']:.4f} | {m['b']:.4f} | {m['difference']:+.4f} "
            f"[{m['ci95_low']:+.4f} ; {m['ci95_high']:+.4f}] |"
        )
    if "cost_usd_mean" in c:
        m = c["cost_usd_mean"]
        lines.append(
            f"| Coût moyen par note | {m['a']:.5f} $ | {m['b']:.5f} $ | {m['difference']:+.5f} $ "
            f"[{m['ci95_low']:+.5f} ; {m['ci95_high']:+.5f}] |"
        )
    m = c["latency_s_median"]
    lines.append(
        f"| Latence médiane | {m['a']:.2f} s | {m['b']:.2f} s | {m['difference']:+.2f} s "
        f"[{m['ci95_low']:+.2f} ; {m['ci95_high']:+.2f}] |"
    )
    lines += [
        "",
        f"Coût des générations : {report['generation_cost_usd']:.4f} $. "
        f"Coût des jugements retenus : {report['judge_cost_usd_final_records']:.4f} $.",
        "",
    ]
    agreement = report["judge_agreement"]
    lines += [
        "## Accord entre les deux juges",
        "",
        "| Tâche | Éléments | Accord brut | AC1 de Gwet | Kappa de Cohen |",
        "|---|---:|---:|---:|---:|",
    ]
    for task, label in [
        ("coverage", "Couverture des faits de référence"),
        ("support", "Appui des assertions"),
        ("citations", "Suffisance des citations"),
    ]:
        a = agreement[task]
        kappa = "—" if a["cohen_kappa"] is None else f"{a['cohen_kappa']:.3f}"
        ac1 = "—" if a["gwet_ac1"] is None else f"{a['gwet_ac1']:.3f}"
        lines.append(f"| {label} | {a['items']} | {_pct(a['agreement'])} | {ac1} | {kappa} |")
    verdict = (
        "atteinte : les scores du juge principal sont présentés comme indicatifs."
        if agreement["reliable"]
        else "non atteinte : les scores sont exploratoires, sans conclusion sur l'écart B−A."
    )
    lines += ["", f"Règle fixée à l'avance ({agreement['rule']}) : {verdict}", ""]
    lines += [
        "## Mêmes mesures selon le second juge",
        "",
        "| Mesure | A, direct | B, structuré | Écart B−A [IC 95 %] |",
        "|---|---:|---:|---|",
    ]
    for name in ["coverage", "omission", "unsupported", "contradiction"]:
        m = report["second_judge"]["comparisons"][name]
        interval = (
            "non défini"
            if m["ci95_low"] is None
            else f"[{100 * m['ci95_low']:+.2f} ; {100 * m['ci95_high']:+.2f}] points"
        )
        difference = "—" if m["difference"] is None else f"{100 * m['difference']:+.2f} points"
        lines.append(
            f"| {LABELS[name]} | {_pct(m['a'])} | {_pct(m['b'])} | {difference} {interval} |"
        )
    lines += [
        "",
        "Aucune validation humaine n'a été réalisée : l'accord entre deux juges automatiques "
        "mesure la sensibilité au choix du juge, pas l'exactitude des jugements.",
        "",
    ]
    return "\n".join(lines)

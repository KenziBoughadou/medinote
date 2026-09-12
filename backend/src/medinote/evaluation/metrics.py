from collections import Counter

import numpy as np

from medinote.schemas import MetricValue, PairedComparison

RATIOS = {
    "omission": ("O", "E"),
    "coverage": ("C", "E"),
    "expected_contradiction": ("K", "E"),
    "unsupported": ("U", "P"),
    "contradiction": ("D", "P"),
    "negation_error": ("polarity_errors", "explicit_repeated"),
    "negative_coverage": ("negative_covered", "negative_expected"),
    "resolvable_references": ("resolved", "emitted"),
    "citation_precision": ("supported_citations", "claim_citations"),
    "citation_coverage": ("cited_claims", "P"),
    "technical_reliability": ("valid", "planned"),
    "notes_with_additions": ("notes_with_U", "valid"),
    "additions_per_consultation": ("U", "planned"),
}


def ratio(numerator, denominator):
    return MetricValue(
        numerator=numerator,
        denominator=denominator,
        value=numerator / denominator if denominator else None,
    )


def score_consultation(gold, annotation=None, note=None, status="ok"):
    expected = {g.fact_id: g for g in gold if g.expected_in_note}
    counts = Counter(
        E=len(expected),
        planned=1,
        negative_expected=sum(g.polarity == "negated" for g in expected.values()),
    )
    if status != "ok":
        counts["O"] = len(expected)
        return dict(counts)
    if annotation is None or note is None:
        raise ValueError("Note valide sans annotation complète")
    counts["valid"] = 1
    assessments = {a.gold_id: a for a in annotation.gold_assessments}
    for gid, g in expected.items():
        state = assessments[gid].status
        counts[{"covered": "C", "contradicted": "K", "omitted": "O"}[state]] += 1
        if state in {"covered", "contradicted"} and g.polarity in {"affirmed", "negated"}:
            counts["explicit_repeated"] += 1
            counts["polarity_errors"] += int(
                any(
                    gid in c.gold_ids and "polarity" in c.contradiction_types
                    for c in annotation.claims
                )
            )
        counts["negative_covered"] += int(g.polarity == "negated" and state == "covered")
    counts["P"] = len(annotation.claims)
    for claim in annotation.claims:
        counts["U"] += claim.label == "unsupported"
        counts["D"] += claim.label == "contradiction"
        counts["claim_citations"] += len(claim.citation_assessments)
        counts["supported_citations"] += sum(a.supports_claim for a in claim.citation_assessments)
        counts["cited_claims"] += any(a.supports_claim for a in claim.citation_assessments)
    citations = [c for s in note.sections for a in s.assertions for c in a.citations]
    counts["emitted"] = len(citations)
    counts["resolved"] = sum(c.resolvable for c in citations)
    counts["notes_with_U"] = int(counts["U"] > 0)
    assert counts["E"] == counts["C"] + counts["K"] + counts["O"]
    return dict(counts)


def aggregate_counts(rows):
    total = Counter()
    for row in rows:
        total.update(row)
    return {
        "counts": dict(total),
        "metrics": {
            name: ratio(total[n], total[d]).model_dump() for name, (n, d) in RATIOS.items()
        },
    }


def paired_bootstrap(a, b, case_ids, replications=10000):
    if len(a) != len(b) or len(a) != len(case_ids) or list(case_ids) != sorted(set(case_ids)):
        raise ValueError("Paires uniques triées requises")
    n = len(a)
    if n == 0:
        raise ValueError("Cohorte vide")
    rng = np.random.Generator(np.random.PCG64(20260911))
    indices = rng.integers(0, n, size=(replications, n))
    comparisons = {}
    for name, (num, den) in RATIOS.items():
        ar = np.array([[r.get(num, 0), r.get(den, 0)] for r in a], dtype=float)
        br = np.array([[r.get(num, 0), r.get(den, 0)] for r in b], dtype=float)
        ac = ar[indices].sum(axis=1)
        bc = br[indices].sum(axis=1)
        valid = (ac[:, 1] > 0) & (bc[:, 1] > 0)
        values = bc[valid, 0] / bc[valid, 1] - ac[valid, 0] / ac[valid, 1]
        aa = ratio(int(ar[:, 0].sum()), int(ar[:, 1].sum())).value
        bb = ratio(int(br[:, 0].sum()), int(br[:, 1].sum())).value
        bounds = (
            np.percentile(values, [2.5, 97.5]).tolist() if valid.mean() >= 0.95 else [None, None]
        )
        comparisons[name] = PairedComparison(
            a=aa,
            b=bb,
            difference=bb - aa if aa is not None and bb is not None else None,
            ci95_low=bounds[0],
            ci95_high=bounds[1],
            n=n,
            unit="consultation",
            warnings=[]
            if valid.mean() >= 0.95
            else ["Ratio non défini dans au moins 95 % des tirages."],
        ).model_dump()
    return comparisons, indices


def score_stress_pairs(cases, annotations):
    pairs = {}
    for case in cases:
        meta = case.stress_pair
        pairs.setdefault(meta.pair_id, []).append(case)
    successes = 0
    for pair in pairs.values():
        if len(pair) != 2:
            raise ValueError("Paire incomplète")
        valid = True
        for case in pair:
            annotation = annotations.get(case.case_id)
            if annotation is None:
                valid = False
                continue
            assessments = {
                a.gold_id.rsplit(".", 1)[-1]: a.status for a in annotation.gold_assessments
            }
            required = [case.stress_pair.target_fact_key, *case.stress_pair.invariant_fact_keys]
            # Les invariants facultatifs sont vérifiés par les claims, même s'ils ne sont pas exigés dans la note principale.
            for key in required:
                if assessments.get(key) == "not_required":
                    valid &= any(
                        any(gid.endswith("." + key) for gid in c.gold_ids)
                        and c.label == "supported_optional"
                        for c in annotation.claims
                    )
                else:
                    valid &= assessments.get(key) == "covered"
        successes += bool(valid)
    return ratio(successes, len(pairs))

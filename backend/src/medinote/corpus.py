import json
from collections import Counter, defaultdict
from pathlib import Path

from medinote.schemas import ConsultationCase, GoldFact, ProvenanceRecord, ReviewEvent
from medinote.serialization import sha256_json
from medinote.sources import validate_source_span

DEMO_IDS = [
    "main-digestif-01",
    "main-respiratoire-01",
    "main-cardiovasculaire-01",
    "main-neurologique-01",
    "main-musculosquelettique-01",
    "main-prevention-01",
]
FAMILIES = [
    "respiratoire",
    "cardiovasculaire",
    "digestif",
    "urinaire",
    "musculosquelettique",
    "neurologique",
    "dermatologique",
    "suivi-chronique",
    "sante-psychique",
    "prevention",
]


def read_jsonl(path, model):
    return [
        model.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class CorpusRepository:
    def __init__(self, root: Path):
        self.root = root
        self.cases = {}
        self.gold = []
        self.provenance = []
        self.review_events = []

    def load(self):
        cases = read_jsonl(self.root / "data/cases.v1.jsonl", ConsultationCase)
        cases += read_jsonl(self.root / "data/stress.v1.jsonl", ConsultationCase)
        self.cases = {c.case_id: c for c in cases}
        if len(self.cases) != len(cases):
            raise ValueError("Identifiants dupliqués")
        self.gold = read_jsonl(self.root / "data/gold.v1.jsonl", GoldFact)
        self.provenance = [
            ProvenanceRecord.model_validate(p)
            for p in json.loads((self.root / "data/provenance.v1.json").read_text())
        ]
        self.review_events = read_jsonl(self.root / "data/review-events.jsonl", ReviewEvent)
        if json.loads((self.root / "data/demo_ids.v1.json").read_text()) != DEMO_IDS:
            raise ValueError("Sélection publique différente du plan")
        return self

    def get_case(self, case_id):
        return self.cases[case_id]

    def list_public_cases(self):
        return [self.get_case(cid) for cid in DEMO_IDS]

    def generation_source(self, case_id):
        case = self.get_case(case_id)
        return dict(
            case_id=case.case_id,
            locale=case.locale,
            segments=[s.model_dump() for s in case.segments],
        )

    @property
    def corpus_sha256(self):
        return sha256_json([c.model_dump(mode="json") for c in self.cases.values()])

    def validate_splits(self):
        main = [c for c in self.cases.values() if c.suite == "main"]
        assert len(main) == 60, "60 cas principaux requis"
        assert Counter(c.split for c in main) == {"dev": 20, "test": 40}
        assert len({c.group_id for c in main}) == 60
        for family in FAMILIES:
            family_cases = [c for c in main if c.family_id == family]
            assert {c.case_id for c in family_cases} == {
                f"main-{family}-{i:02}" for i in range(1, 7)
            }
            assert all(
                c.split == ("dev" if c.case_id[-2:] in ["01", "02"] else "test")
                for c in family_cases
            )
        stress = [c for c in self.cases.values() if c.suite == "stress"]
        assert len(stress) == 20 and len({c.group_id for c in stress}) == 10
        assert not {c.group_id for c in main} & {c.group_id for c in stress}
        assert all(c.split == "dev" for c in self.list_public_cases())

    def validate_gold_evidence(self):
        ids = set()
        keys = set()
        for fact in self.gold:
            assert fact.fact_id not in ids, "Gold dupliqué"
            assert (fact.case_id, fact.fact_key) not in keys, "Clé sémantique dupliquée"
            ids.add(fact.fact_id)
            keys.add((fact.case_id, fact.fact_key))
            for span in fact.evidence:
                validate_source_span(self.get_case(fact.case_id), span)
        for case in self.cases.values():
            facts = [f for f in self.gold if f.case_id == case.case_id]
            assert 8 <= sum(f.expected_in_note for f in facts) <= 18
            assert any(not f.expected_in_note for f in facts), "Fait facultatif requis"

    def validate_stress_pairs(self):
        pairs = defaultdict(list)
        for case in self.cases.values():
            if case.stress_pair:
                pairs[case.stress_pair.pair_id].append(case)
        assert len(pairs) == 10
        for pair in pairs.values():
            assert len(pair) == 2
            variants = {c.stress_pair.variant: c for c in pair}
            assert set(variants) == {"positive", "negative"}
            pos, neg = variants["positive"], variants["negative"]
            assert pos.group_id == neg.group_id
            diffs = [
                (a.text, b.text)
                for a, b in zip(pos.segments, neg.segments, strict=True)
                if a.text != b.text
            ]
            assert len(diffs) == 1
            # Règle éditoriale v1 : insertion exacte de « ne » et « pas ».
            assert diffs[0][1].replace(" ne ", " ").replace(" pas ", " ") == diffs[0][0]
            pg = {f.fact_key: f for f in self.gold if f.case_id == pos.case_id}
            ng = {f.fact_key: f for f in self.gold if f.case_id == neg.case_id}
            target = pos.stress_pair.target_fact_key
            assert target == neg.stress_pair.target_fact_key
            assert pg[target].polarity == "affirmed" and ng[target].polarity == "negated"
            invariants = set(pg) - {target}
            assert set(pos.stress_pair.invariant_fact_keys) == invariants
            assert set(neg.stress_pair.invariant_fact_keys) == invariants
            for key in pg:
                exclude = {"fact_id", "case_id", "evidence"} | (
                    {"polarity"} if key == target else set()
                )
                assert pg[key].model_dump(exclude=exclude) == ng[key].model_dump(exclude=exclude)

    def validate_corpus(self):
        self.validate_splits()
        self.validate_gold_evidence()
        self.validate_stress_pairs()
        provenance = {p.provenance_id for p in self.provenance}
        for case in self.cases.values():
            assert case.provenance_id in provenance
            words = sum(len(s.text.split()) for s in case.segments)
            assert 150 <= words <= 700, f"{case.case_id}: {words} mots"
        return {
            "valid": True,
            "main": 60,
            "dev": 20,
            "test": 40,
            "stress": 20,
            "stress_pairs": 10,
            "public": 6,
            "gold_facts": len(self.gold),
            "corpus_sha256": self.corpus_sha256,
            "human_review_events": sum(r.kind == "human" for r in self.review_events),
        }

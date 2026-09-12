from medinote.corpus import CorpusRepository
from medinote.llm import build_generation_request
from medinote.schemas import Method


def test_corpus(root):
    repo = CorpusRepository(root).load()
    report = repo.validate_corpus()
    assert report["main"] == 60 and report["human_review_events"] == 0
    for case in repo.cases.values():
        for method in Method:
            req = build_generation_request(case, method)
            assert "expected_in_note" not in str(req.payload)
            assert "focus_tags" not in str(req.payload)

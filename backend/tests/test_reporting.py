from types import SimpleNamespace

import pytest
from medinote.cli import main
from medinote.evaluation.report import assert_report_eligible


def test_report_refuses_missing_annotations():
    with pytest.raises(ValueError):
        assert_report_eligible([SimpleNamespace(run_id="r", status="ok")], {})


def test_cli_corpus_and_status(root, capsys):
    assert main(["corpus", "validate", "--root", str(root)]) == 0
    assert main(["plan-status", "--root", str(root)]) == 0
    assert "awaiting_annotation" in capsys.readouterr().out

import pytest
from evaluation_helpers import annotated_example
from medinote.evaluation.blinding import safe_artifact
from medinote.evaluation.schemas import Annotator


def test_ai_provenance_not_relabelled(root):
    _, _, _, a = annotated_example(root)
    changed = a.annotator.model_dump()
    changed["kind"] = "human"
    with pytest.raises(ValueError):
        Annotator(**changed)


def test_artifact_traversal(tmp_path):
    for name in ["../secret", "/etc/passwd"]:
        with pytest.raises(ValueError):
            safe_artifact(tmp_path, name)

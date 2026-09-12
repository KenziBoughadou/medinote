import numpy as np
from medinote.evaluation.metrics import paired_bootstrap


def test_seed_and_pairing():
    a = [{"E": 2, "O": 1}, {"E": 4, "O": 0}]
    b = [{"E": 2, "O": 0}, {"E": 4, "O": 1}]
    c, indices = paired_bootstrap(a, b, ["a", "b"])
    _, again = paired_bootstrap(a, b, ["a", "b"])
    assert np.array_equal(indices, again) and indices.shape == (10000, 2)
    assert c["omission"]["difference"] == 0
    assert c["unsupported"]["ci95_low"] is None
    assert c["unsupported"]["warnings"]

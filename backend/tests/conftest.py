from pathlib import Path

import pytest
from medinote.config import Settings


@pytest.fixture
def root():
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def settings(root, tmp_path):
    return Settings(env="test", root=root, state_dir=tmp_path)

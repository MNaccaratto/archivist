import os
import time

import pytest

from archivist.config import load_config


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Keep history/config out of the real home directory."""
    monkeypatch.setenv("ARCHIVIST_HOME", str(tmp_path / "_archivist_home"))


@pytest.fixture
def cfg():
    return load_config()


def make_file(path, content="x", age_minutes=60):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    old = time.time() - age_minutes * 60
    os.utime(path, (old, old))
    return path

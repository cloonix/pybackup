import json
import pytest
from pathlib import Path


@pytest.fixture
def tmp_config(tmp_path):
    def _make(data: dict) -> Path:
        p = tmp_path / "config.json"
        p.write_text(json.dumps(data))
        return p
    return _make

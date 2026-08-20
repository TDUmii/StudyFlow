from pathlib import Path

import pytest

from app.services import AppService


@pytest.fixture
def service(tmp_path: Path):
    value = AppService(tmp_path / "data", tmp_path / "exports")
    value.setup_profile("Minh", 30)
    return value

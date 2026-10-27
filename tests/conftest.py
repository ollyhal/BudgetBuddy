from pathlib import Path

import pytest

from budgetbuddy.db import connect

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def conn(data_dir: Path):
    connection = connect(data_dir)
    yield connection
    connection.close()


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES

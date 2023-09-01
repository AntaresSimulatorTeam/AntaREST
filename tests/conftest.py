from pathlib import Path

import pytest

# noinspection PyUnresolvedReferences
from tests.conftest_db import *

# noinspection PyUnresolvedReferences
from tests.conftest_services import *

HERE = Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))


@pytest.fixture(scope="session")
def project_path() -> Path:
    return PROJECT_DIR

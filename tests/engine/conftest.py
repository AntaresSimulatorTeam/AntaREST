from pathlib import Path

import pytest

PATH_TESTS = Path(__file__).parents[0]


@pytest.fixture
def path_resources() -> Path:
    return PATH_TESTS / "resources"

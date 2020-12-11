from pathlib import Path

import pytest

PATH_TESTS = Path(__file__).parents[0]


@pytest.fixture
def path_ressources() -> Path:
    return PATH_TESTS / "resources"


@pytest.fixture
def path_jsm_with_refs_outside(path_ressources: Path) -> Path:
    return path_ressources / "jsonschema.json"

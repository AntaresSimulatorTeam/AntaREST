import json
from pathlib import Path

import pytest

from api_iso_antares.custom_types import JSON

PATH_TESTS = Path(__file__).parents[0]


@pytest.fixture
def path_ressources() -> Path:
    return PATH_TESTS / "resources"


@pytest.fixture
def jsonschema_with_refs_outside(path_ressources: Path) -> JSON:
    with open(str(path_ressources / "jsonschema.json"), "r") as inputfile:
        data = json.load(inputfile)
    return data

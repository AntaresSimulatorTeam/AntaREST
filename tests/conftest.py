# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest

project_dir: Path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from api_iso_antares.custom_types import JSON


@pytest.fixture
def test_json_data() -> JSON:
    json_data = {
        "part1": {"key_int": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }
    return json_data

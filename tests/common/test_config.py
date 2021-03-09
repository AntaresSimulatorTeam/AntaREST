import os
from pathlib import Path

import pytest

from antarest.common.config import ConfigYaml


@pytest.mark.unit_test
def test_get_yaml(project_path: Path):
    config = ConfigYaml(file=project_path / "tests/common/test.yaml")

    assert config["main"] == {
        "bonjour": ["le", "monde"],
        "hello": "World",
    }
    assert config["main.hello"] == "World"
    assert config["not_existing"] is None


@pytest.mark.unit_test
def test_env_yaml(project_path: Path):
    config = ConfigYaml(file=project_path / "tests/common/test.yaml")

    assert config["main.hello"] == "World"
    os.environ["MAIN_HELLO"] = "antarest"
    assert config["main.hello"] == "antarest"

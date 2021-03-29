import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, cast

import pytest
from dataclasses_json.api import dataclass_json

from antarest.common.config import ConfigYaml, register_config, Config


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


@dataclass
class Bar:
    arg: Dict[str, str]


@dataclass_json
@dataclass
class Foo:
    bar: Bar
    baz: str = "hello"


def test_custom_typed_conf():
    get_config = register_config("managed", Foo)
    json_config = {
        "managed": {"bar": {"arg": {"hello": "world"}}},
        "unmanaged": {"hello": "world"},
    }
    config = Config(json_config)
    assert config is not None

    custom_config = get_config(config)
    assert custom_config.bar.arg == {"hello": "world"}
    assert custom_config.baz == "hello"
    assert config["unmanaged"] == {"hello": "world"}

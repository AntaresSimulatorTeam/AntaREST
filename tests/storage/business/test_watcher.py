from pathlib import Path
from unittest.mock import Mock, call

import pytest

from antarest.common.config import Config
from antarest.login.model import Group
from antarest.storage.business.watcher import Watcher


def build_config(root: Path) -> Config:
    return Config(
        {
            "storage": {
                "workspaces": {
                    "default": {
                        "path": str(root / "default"),
                        "groups": ["toto"],
                    },
                    "diese": {"path": str(root / "diese"), "groups": ["tata"]},
                }
            }
        }
    )


@pytest.mark.unit_test
def test_init(tmp_path: Path):
    default = tmp_path / "default"
    default.mkdir()
    a = default / "studyA"
    a.mkdir()
    (a / "study.antares").touch()

    diese = tmp_path / "diese"
    diese.mkdir()
    c = diese / "studyC"
    c.mkdir()
    (c / "study.antares").touch()

    service = Mock()
    watcher = Watcher(build_config(tmp_path), service)

    watcher.init()

    service.create_study_from_watcher.assert_has_calls(
        [
            call(a, "default", [Group(id="toto")]),
            call(c, "diese", [Group(id="tata")]),
        ]
    )

from pathlib import Path
from time import sleep
from unittest.mock import Mock, call

import pytest

from antarest.common.config import Config
from antarest.login.model import Group
from antarest.storage.business.watcher import Watcher
from antarest.storage.model import StudyFolder


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
def test_scan(tmp_path: Path):
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

    watcher._scan()

    service.sync_studies_on_disk.assert_called_once_with(
        [
            StudyFolder(a, "default", [Group(id="toto")]),
            StudyFolder(c, "diese", [Group(id="tata")]),
        ]
    )


@pytest.mark.unit_test
def test_get_lock():
    watcher = Watcher(config=Config(), service=Mock())

    assert not watcher._get_lock()

    sleep(Watcher.DELAY + 1)
    assert watcher._get_lock()

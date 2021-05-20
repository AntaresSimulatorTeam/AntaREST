import os
from multiprocessing import Pool
from pathlib import Path
from time import sleep
from unittest.mock import Mock, call

import pytest

from antarest.common.config import Config, StorageConfig, WorkspaceConfig
from antarest.login.model import Group
from antarest.storage.business.watcher import Watcher
from antarest.storage.model import StudyFolder, DEFAULT_WORKSPACE_NAME


def build_config(root: Path) -> Config:
    return Config(
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(
                    path=root / DEFAULT_WORKSPACE_NAME, groups=["toto"]
                ),
                "diese": WorkspaceConfig(path=root / "diese", groups=["tata"]),
            }
        )
    )


def clean_files() -> None:
    if Watcher.LOCK.exists():
        os.remove(Watcher.LOCK)

    lock = f"{Watcher.LOCK.absolute()}.lock"
    if os.path.exists(lock):
        os.remove(lock)


@pytest.mark.unit_test
def test_scan(tmp_path: Path):
    clean_files()

    default = tmp_path / "default"
    default.mkdir()
    a = default / "studyA"
    a.mkdir()
    (a / "study.antares").touch()

    diese = tmp_path / "diese"
    diese.mkdir()
    c = diese / "folder/studyC"
    c.mkdir(parents=True)
    (c / "study.antares").touch()

    d = diese / "folder/trash"
    d.mkdir(parents=True)
    (d / "trash").touch()

    service = Mock()
    watcher = Watcher(build_config(tmp_path), service)

    watcher._scan()

    service.sync_studies_on_disk.assert_called_once_with(
        [
            StudyFolder(c, "diese", [Group(id="tata")]),
        ]
    )


def process(x: int) -> bool:
    return Watcher._get_lock()


@pytest.mark.unit_test
def test_get_lock():
    clean_files()

    pool = Pool()
    res = sum(pool.map(process, range(4)))
    assert res == 1

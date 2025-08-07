# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import logging
import os
import typing as t
from datetime import datetime, timedelta
from multiprocessing import Pool
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import CannotAccessInternalWorkspace, ScanDisabled
from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.core.persistence import Base
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.login.model import GroupDTO
from antarest.login.service import LoginService
from antarest.study.model import DEFAULT_WORKSPACE_NAME, OwnerInfo, Study, StudyMetadataDTO
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import create_study
from tests.storage.conftest import SimpleSyncTaskService


def build_config(root: Path, desktop_mode=False) -> Config:
    return Config(
        desktop_mode=desktop_mode,
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=root / DEFAULT_WORKSPACE_NAME, groups=["toto"]),
                "diese": WorkspaceConfig(
                    path=root / "diese",
                    groups=["tata"],
                    filter_out=["to_skip.*"],
                ),
                "test": WorkspaceConfig(
                    path=root / "test",
                    groups=["toto"],
                    filter_out=["to_skip.*"],
                ),
            }
        ),
    )


def clean_files() -> None:
    if Watcher.LOCK.exists():
        os.remove(Watcher.LOCK)

    lock = f"{Watcher.LOCK.absolute()}.lock"
    if os.path.exists(lock):
        os.remove(lock)


def build_study_service(
    raw_study_service: RawStudyService,
    repository: StudyMetadataRepository,
    config: Config,
    user_service: LoginService = Mock(spec=LoginService),
    cache_service: ICache = Mock(spec=ICache),
    variant_study_service: VariantStudyService = Mock(spec=VariantStudyService),
    task_service: ITaskService = Mock(spec=ITaskService),
) -> StudyService:
    return StudyService(
        raw_study_service=raw_study_service,
        variant_study_service=variant_study_service,
        user_service=user_service,
        command_context=Mock(),
        repository=repository,
        job_result_repository=Mock(),
        event_bus=Mock(),
        task_service=task_service,
        file_transfer_manager=Mock(),
        cache_service=cache_service,
        config=config,
    )


def study_to_dto(study: Study) -> StudyMetadataDTO:
    return StudyMetadataDTO(
        id=study.id,
        name=study.name,
        version=study.version,
        created=str(study.created_at),
        updated=str(study.updated_at),
        workspace=DEFAULT_WORKSPACE_NAME,
        managed=True,
        type=study.type,
        archived=study.archived if study.archived is not None else False,
        owner=(
            OwnerInfo(id=study.owner.id, name=study.owner.name)
            if study.owner is not None
            else OwnerInfo(name="Unknown")
        ),
        groups=[GroupDTO(id=group.id, name=group.name) for group in study.groups],
        public_mode=study.public_mode or PublicMode.NONE,
        horizon=study.additional_data.horizon,
        scenario=None,
        status=None,
        doc=None,
        folder=None,
    )


@pytest.fixture
def study_tree(tmp_path: Path) -> Path:
    """
    Create this hierarchy

    tmp_path
    ├── default
    │   └── studyA
    │       └── study.antares
    └── diese
        └── folder
            ├── studyC
            │   └── study.antares
            ├── trash
            │   └── trash
            ├── another_folder
            │   ├── AW_NO_SCAN
            │   └── study.antares
            └── subfolder
                └── studyG
                    └── study.antares
    """

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

    f = diese / "folder/another_folder"
    f.mkdir(parents=True)
    (f / "AW_NO_SCAN").touch()
    (f / "study.antares").touch()

    return tmp_path


@pytest.mark.unit_test
def test_scan(study_tree: Path):
    clean_files()

    service = Mock()
    watcher = Watcher(build_config(study_tree), service, task_service=SimpleSyncTaskService())

    watcher.scan()

    assert service.sync_studies_on_disk.call_count == 1
    call = service.sync_studies_on_disk.call_args_list[0]
    assert len(call.args[0]) == 1
    assert call.args[0][0].path == study_tree / "diese/folder/studyC"
    assert call.args[0][0].workspace == "diese"
    groups = call.args[0][0].groups
    assert len(groups) == 1
    assert groups[0].id == "tata"
    assert groups[0].name == "tata"
    assert call.args[1] is None


@pytest.mark.unit_test
def test_scan_recursive_false(study_tree: Path, db_session: Session):
    def count_studies():
        return db_session.query(Study).count()

    clean_files()

    g = study_tree / "diese/folder/subfolder/studyG"
    g.mkdir(parents=True)
    (g / "study.antares").touch()

    raw_study_service = Mock(spec=RawStudyService)

    def update_meta(study: Study, fallback_on_default: bool = True) -> Study:
        study.version = "860"
        return study

    raw_study_service.update_from_raw_meta.side_effect = update_meta

    def get_info(path: Path) -> StudyMetadataDTO:
        return study_to_dto(
            create_study(
                id=path.name,
                name=path.name,
                path=str(path),
                version="860",
            )
        )

    raw_study_service.get_study_information.side_effect = get_info
    repository = StudyMetadataRepository(session=db_session, cache_service=Mock(spec=ICache))
    repository.delete = Mock()
    config = build_config(study_tree)
    service = build_study_service(raw_study_service, repository, config)
    watcher = Watcher(config, service, task_service=SimpleSyncTaskService())

    # at the beginning, no study in the database
    assert count_studies() == 0

    # only the studyA should be scanned, as the recursive flag is set to False
    watcher.scan(recursive=False, workspace_name="diese", workspace_directory_path="folder")
    assert count_studies() == 1

    # Now studyC should be scanned, as we scan folder/subfolder which contains studyG
    watcher.scan(recursive=False, workspace_name="diese", workspace_directory_path="folder/subfolder")
    assert count_studies() == 2

    # Even if we deleted stydu G, the scan shoudl not delete, as we are not scanning the folder containing it
    os.remove(g / "study.antares")
    watcher.scan(recursive=False, workspace_name="diese", workspace_directory_path="folder")
    assert count_studies() == 2
    assert repository.delete.call_count == 0

    # Now we scan the folder containing studyG, it should be marked for deletion but not deleted yet
    watcher.scan(recursive=False, workspace_name="diese", workspace_directory_path="folder/subfolder")
    assert repository.delete.call_count == 0

    # We simulate three days went by, now a delete should be triggered
    in_3_days = datetime.utcnow() + timedelta(days=3)
    with mock.patch("antarest.study.service.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = in_3_days
        watcher.scan(recursive=False, workspace_name="diese", workspace_directory_path="folder/subfolder")
        assert repository.delete.call_count == 1


@pytest.mark.unit_test
def test_partial_scan(tmp_path: Path, caplog: t.Any):
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    clean_files()

    # study to be scanned
    default = tmp_path / "test"
    default.mkdir()
    a = default / "studyA"
    a.mkdir()
    (a / "study.antares").touch()

    # create a temporary upgrade folder
    upgrade_folder = default / "folder/~upgrade_folder.study.upgrade.tmp"
    upgrade_folder.mkdir(parents=True)
    (upgrade_folder / "study.antares").touch()

    # create a temporary ts gen folder
    ts_gen_folder = default / "folder/~ts_gen_folder.study.thermal_timeseries_gen.tmp"
    ts_gen_folder.mkdir(parents=True)
    (ts_gen_folder / "study.antares").touch()

    # study to be skipped because we check only the `default directory`
    diese = tmp_path / "diese"
    diese.mkdir()
    c = diese / "folder/studyC"
    c.mkdir(parents=True)
    (c / "study.antares").touch()

    service = Mock()
    watcher = Watcher(build_config(tmp_path), service, task_service=SimpleSyncTaskService())

    with pytest.raises(CannotAccessInternalWorkspace):
        watcher.scan(workspace_name="default", workspace_directory_path=default)

    with caplog.at_level(level=logging.INFO, logger="antarest.study.storage.utils"):
        # scan the `default` directory
        watcher.scan(workspace_name="test", workspace_directory_path=default)

        # verify that only one study has been scanned
        assert service.sync_studies_on_disk.call_count == 1

        # verify that the scan process has been called with the correct arguments
        call = service.sync_studies_on_disk.call_args_list[0]

        # verify that only one study has been scanned
        assert len(call.args[0]) == 1

        # verify that folder `a` has been processed correctly
        assert call.args[0][0].path == a
        assert call.args[0][0].workspace == "test"
        groups = call.args[0][0].groups
        assert len(groups) == 1
        assert groups[0].id == "toto"
        assert groups[0].name == "toto"
        assert call.args[1] == tmp_path / "test"

    # verify that `upgrade_folder` and `ts_gen_folder`  have been skipped
    assert f"Upgrade temporary folder found. Will skip further scan of folder {upgrade_folder}" in caplog.text
    assert f"TS generation temporary folder found. Will skip further scan of folder {ts_gen_folder}" in caplog.text


@pytest.mark.unit_test
def test_scan_disabled_exception(study_tree: Path):
    clean_files()

    # Build a configuration with desktop_mode enabled
    config = build_config(study_tree, desktop_mode=True)
    service = Mock()
    watcher = Watcher(config, service, task_service=SimpleSyncTaskService())

    # Assert that ScanDisabled exception is raised when recursive=True and desktop_mode=True
    with pytest.raises(ScanDisabled, match="Recursive scan disables when desktop mode is on"):
        watcher.scan(recursive=True)

    # Also for one_shot scan
    with pytest.raises(ScanDisabled, match="Recursive scan disables when desktop mode is on"):
        watcher.oneshot_scan(recursive=True)


def process(x: int) -> bool:
    return Watcher._get_lock(2)


@pytest.mark.unit_test
def test_get_lock():
    clean_files()

    pool = Pool()
    res = sum(pool.map(process, range(4)))
    assert res == 1

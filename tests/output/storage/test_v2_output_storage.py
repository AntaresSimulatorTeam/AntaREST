# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import shutil
import uuid
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import Engine

from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.lfs.dir_lfs import DirLargeFileStorage
from antarest.lfs.lfs import ILargeFileStorage
from antarest.output.storage.v2.repository import OutputV2Repository
from antarest.output.storage.v2.v2_output_storage import V2OutputStorage
from antarest.study.model import Study
from antarest.study.repository import StudyMetadataRepository


@pytest.fixture
def init_db(db_engine: Engine) -> None:
    DBSessionMiddleware(None, custom_engine=db_engine)


@pytest.fixture
def study_repo(init_db) -> StudyMetadataRepository:
    return StudyMetadataRepository(cache_service=Mock())


@pytest.fixture
def output_repo(init_db) -> OutputV2Repository:
    return OutputV2Repository()


@pytest.fixture(scope="session")
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture(scope="session")
def output_path(tmp_path_factory: pytest.TempPathFactory, sta_mini_zip_path: Path) -> Path:
    tmp_dir = tmp_path_factory.mktemp(basename=f"unzipped-output-{uuid.uuid4()}")

    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(tmp_dir)
    return tmp_dir / "STA-mini" / "output" / "20201014-1427eco"


@pytest.fixture
def study_id(study_repo: StudyMetadataRepository) -> str:
    with db():
        # The FK constraints enforces us to create a study first.
        study_repo.save(Study(id="my-study", name="name", version="9.2", path=""))
    return "my-study"


@pytest.fixture
def lfs(tmp_path: Path) -> ILargeFileStorage:
    return DirLargeFileStorage(tmp_path / "lfs")


@pytest.fixture
def storage(
    tmp_path: Path, study_repo: StudyMetadataRepository, output_repo: OutputV2Repository, lfs: ILargeFileStorage
) -> V2OutputStorage:
    storage_tmp_dir = tmp_path / "storage" / "tmp"
    storage = V2OutputStorage(archive_storage=lfs, tmp_dir=storage_tmp_dir, repository=output_repo)
    return storage


def test_storage(
    tmp_path: Path,
    storage: V2OutputStorage,
    lfs: ILargeFileStorage,
    study_id: str,
    output_path: Path,
):
    with db():
        # Check there is no output at first for that study
        assert not storage.output_exists(study_id="my-study", output_id="20201014-1427eco")
        assert storage.list_outputs(study_id="my-study") == []

        # Import output
        output_name = storage.import_output("my-study", output_path)
        assert output_name == "20201014-1427eco"

        # Check output exists
        assert storage.output_exists(study_id="my-study", output_id="20201014-1427eco")
        assert not storage.is_output_archived(study_id="my-study", output_id="20201014-1427eco")

        # Check output appears in list of study outputs
        study_outputs = storage.list_outputs(study_id="my-study")
        assert len(study_outputs) == 1
        study_output = study_outputs[0]
        assert study_output.id == "20201014-1427eco"
        assert not study_output.archived
        assert len(lfs.list_files()) == 1

        # Check output export works
        export_path = tmp_path / "exported.zip"
        storage.export_output(study_id="my-study", output_id="20201014-1427eco", target=export_path)
        assert export_path.exists()
        assert zipfile.is_zipfile(export_path)

        # Archive output
        storage.archive_study_output(study_id="my-study", output_id="20201014-1427eco")
        assert storage.is_output_archived(study_id="my-study", output_id="20201014-1427eco")

        # Check we can still download it
        export_path = tmp_path / "exported-2.zip"
        storage.export_output(study_id="my-study", output_id="20201014-1427eco", target=export_path)
        assert export_path.exists()
        assert zipfile.is_zipfile(export_path)

        # Delete output
        storage.delete_output(study_id="my-study", output_id="20201014-1427eco")
        assert not storage.output_exists(study_id="my-study", output_id="20201014-1427eco")
        assert storage.list_outputs(study_id="my-study") == []
        assert lfs.list_files() == []


def create_archive(archive_format: ArchiveFormat, nested: bool, output_path: Path, tmp_path: Path) -> Path:
    """
    Creates an archive containing the output files, possibly with an additional directory level if nested is True
    """
    if nested:
        nested_output_path = tmp_path / "output"
        shutil.copytree(output_path, nested_output_path / "nested")
        output_path = nested_output_path
    archive_path = tmp_path / f"archive{archive_format}"
    archive_dir(output_path, archive_path, remove_source_dir=False, archive_format=archive_format)
    return archive_path


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("archive_format", [ArchiveFormat.ZIP, ArchiveFormat.SEVEN_ZIP])
def test_import_archive(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    archive_format: ArchiveFormat,
    nested: bool,
    tmp_path: Path,
):
    archive_path = create_archive(archive_format, nested, output_path, tmp_path)
    with db():
        output_name = storage.import_output(study_id, archive_path)

    assert output_name == "20201014-1427eco"
    with db():
        assert storage.output_exists(study_id=study_id, output_id="20201014-1427eco")
        assert not storage.is_output_archived(study_id=study_id, output_id="20201014-1427eco")


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("archive_format", [ArchiveFormat.ZIP, ArchiveFormat.SEVEN_ZIP])
def test_import_archive_stream(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    archive_format: ArchiveFormat,
    nested: bool,
    tmp_path: Path,
):
    archive_path = create_archive(archive_format, nested, output_path, tmp_path)
    with db():
        with open(archive_path, "rb") as archive_io:
            output_name = storage.import_output(study_id, archive_io)

    assert output_name == "20201014-1427eco"
    with db():
        assert storage.output_exists(study_id=study_id, output_id="20201014-1427eco")
        assert not storage.is_output_archived(study_id=study_id, output_id="20201014-1427eco")


def test_import_output_with_existing_logs(storage: V2OutputStorage, study_id: str, output_path: Path) -> None:
    with db():
        output_name = storage.import_output(study_id, output_path)
        assert output_name == "20201014-1427eco"

        assert storage.output_exists(study_id, "20201014-1427eco")

        out_logs = storage.get_logs(study_id, "20201014-1427eco", LogType.STDOUT)
        assert len(out_logs.splitlines()) == 239
        assert storage.get_logs(study_id, "20201014-1427eco", LogType.STDERR) == ""


def test_import_output_override_logs(
    storage: V2OutputStorage, study_id: str, output_path: Path, tmp_path: Path
) -> None:
    out_path = tmp_path / "out.log"
    err_path = tmp_path / "err.log"
    out_path.write_text("out log")
    err_path.write_text("err log")
    with db():
        output_name = storage.import_output(study_id, output_path, logs=SimulationLogs(out_path, err_path))
        assert output_name == "20201014-1427eco"

        assert storage.output_exists(study_id, "20201014-1427eco")

        assert storage.get_logs(study_id, "20201014-1427eco", LogType.STDOUT) == "out log"
        assert storage.get_logs(study_id, "20201014-1427eco", LogType.STDERR) == "err log"

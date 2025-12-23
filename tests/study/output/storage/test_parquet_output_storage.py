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
import uuid
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import Engine

from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.study.model import Study
from antarest.study.output.lfs.flat_dir_large_file_storage import FlatDirLargeFileStorage
from antarest.study.output.storage.parquet_output_storage import ParquetOutputStorage
from antarest.study.output.storage.repository import OutputMetadataRepository
from antarest.study.repository import StudyMetadataRepository


@pytest.fixture
def init_db(db_engine: Engine) -> None:
    DBSessionMiddleware(None, custom_engine=db_engine)


@pytest.fixture
def study_repo(init_db) -> StudyMetadataRepository:
    return StudyMetadataRepository(cache_service=Mock())


@pytest.fixture
def output_repo(init_db) -> OutputMetadataRepository:
    return OutputMetadataRepository()


@pytest.fixture(scope="session")
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture(scope="session")
def output_path(tmp_path_factory: pytest.TempPathFactory, sta_mini_zip_path: Path) -> Path:
    tmp_dir = tmp_path_factory.mktemp(basename=f"unzipped-output-{uuid.uuid4()}")

    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(tmp_dir)
    return tmp_dir / "STA-mini" / "output" / "20201014-1427eco"


def test_storage(
    tmp_path: Path, study_repo: StudyMetadataRepository, output_repo: OutputMetadataRepository, output_path: Path
):
    lfs = FlatDirLargeFileStorage(tmp_path / "lfs")

    storage_tmp_dir = tmp_path / "storage" / "tmp"
    storage = ParquetOutputStorage(archive_storage=lfs, tmp_dir=storage_tmp_dir, metadata_repository=output_repo)

    with db():
        # The FK constraints enforces us to create a study first.
        study_repo.save(Study(id="my-study", name="name", version="9.2", path=""))

        # Check there is no output at first for that study
        assert not storage.output_exists(study_id="my-study", output_id="20201014-1427eco")
        assert storage.get_study_sim_result(study_id="my-study") == []

        # Import output
        output_name = storage.import_output("my-study", output_path)
        assert output_name == "20201014-1427eco"

        # Check output exists
        assert storage.output_exists(study_id="my-study", output_id="20201014-1427eco")
        assert not storage.is_output_archived(study_id="my-study", output_id="20201014-1427eco")

        # Check output appears in list of study outputs
        study_outputs = storage.get_study_sim_result(study_id="my-study")
        assert len(study_outputs) == 1
        study_output = study_outputs[0]
        assert study_output.name == "20201014-1427eco"
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
        assert storage.get_study_sim_result(study_id="my-study") == []
        assert lfs.list_files() == []

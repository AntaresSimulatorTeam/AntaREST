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
import uuid
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.fastapi_sqlalchemy.middleware import init_db_singleton
from antarest.lfs.dir_lfs import DirLargeFileStorage
from antarest.lfs.lfs import ILargeFileStorage
from antarest.output.filestudy.model import FileOutput
from antarest.output.storage.v2.dbmodel import DbOutputMetadataV2
from antarest.output.storage.v2.metadata import IParquetOutputMetadata, ParquetOutputMetadata
from antarest.output.storage.v2.repository import OutputV2Repository
from antarest.output.storage.v2.storage import V2OutputStorage
from antarest.output.storage.v2.variables_parsing import extract_output_variables_to_database
from antarest.output.storage.v2.variables_storage import create_parquet_files
from antarest.study.model import Study
from antarest.study.repository import StudyMetadataRepository


@pytest.fixture
def output_dir(data_dir: Path) -> Path:
    return data_dir / "20260810-1420eco-thermal_groups"


@pytest.fixture
def parquet_dir(tmp_path: Path) -> Path:
    dir = tmp_path / "output"
    dir.mkdir()
    return dir


@pytest.fixture
def parquet_metadata(output_dir: Path, parquet_dir: Path, db_session: Session) -> IParquetOutputMetadata:
    """
    Imports 20260810-1420eco-thermal_groups to parquet and return the associated metadata
    """

    db_output = DbOutputMetadataV2(
        study_id="test",
        output_name="test",
        mc_years=[1, 2],
        metadata_version=1,
        archived=False,
        mode="Economy",
        synthesis=True,
        by_year=True,
        nb_years=2,
        start_month=1,
        january_first_weekday=1,
        leap_year=False,
        start_day=1,
        end_day=365,
        first_weekday=1,
    )
    db_session.add(db_output)
    db_session.flush()

    file_output = FileOutput(output_dir)
    extract_output_variables_to_database(db_session, db_output.id, file_output)
    db_session.flush()

    output_metadata = ParquetOutputMetadata(db_session, db_output.id)
    create_parquet_files(output_metadata, file_output, parquet_dir)

    assert len(list(parquet_dir.iterdir())) == 3
    monthly_file = parquet_dir / "mc-ind_areas_monthly.parquet"
    assert monthly_file.is_file()

    return output_metadata


@pytest.fixture
def init_db(db_engine: Engine) -> None:
    init_db_singleton(custom_engine=db_engine)


@pytest.fixture
def study_repo(init_db) -> StudyMetadataRepository:
    return StudyMetadataRepository()


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
    variables_dir = tmp_path / "variables"
    storage = V2OutputStorage(
        archive_storage=lfs, tmp_dir=storage_tmp_dir, repository=output_repo, variables_dir=variables_dir
    )
    return storage

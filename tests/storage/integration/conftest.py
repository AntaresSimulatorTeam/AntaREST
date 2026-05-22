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

import datetime
import shutil
import zipfile
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import py7zr
import pytest

from antarest.blobstore.repository import BlobContentRepository
from antarest.blobstore.service import BlobService
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import (
    CacheConfig,
    Config,
    InternalMatrixFormat,
    SecurityConfig,
    StorageConfig,
    WorkspaceConfig,
)
from antarest.core.tasks.service import ITaskService
from antarest.login.model import User
from antarest.matrixstore.repository import MatrixContentRepository
from antarest.matrixstore.service import SimpleMatrixService
from antarest.output.service import OutputService
from antarest.service_creator import build_output_service
from antarest.study.main import build_study_service
from antarest.study.model import DEFAULT_WORKSPACE_NAME, StorageMode
from antarest.study.service import StudyService
from tests.helpers import create_raw_study

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(scope="session")
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def sta_mini_seven_zip_path(project_path: Path, sta_mini_zip_path: Path) -> Path:
    target = project_path / "examples/studies/STA-mini.7z"
    if target.is_file():
        return target
    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(sta_mini_zip_path.parent)
    extracted_dir_path = sta_mini_zip_path.parent / "STA-mini"
    with py7zr.SevenZipFile(target, "w") as szf:
        szf.writeall(extracted_dir_path, arcname="")
    shutil.rmtree(extracted_dir_path)
    return target


@pytest.fixture
def services(tmp_path: Path, project_path: Path, sta_mini_zip_path: Path) -> tuple[StudyService, OutputService, Config]:
    path_studies = tmp_path / "studies"

    path_resources = project_path / "resources"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    (path_studies / "STA-mini").rename(path_studies / UUID)

    # noinspection PyArgumentList
    md = create_raw_study(
        id=UUID,
        name="STA-mini",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / UUID),
        created_at=datetime.datetime.fromtimestamp(1480683452),
        updated_at=datetime.datetime.fromtimestamp(1602678639),
        version="700",
        author="Andrea SGATTONI",
        horizon=2030,
    )
    repo = Mock()
    # noinspection PyArgumentList
    repo.get.side_effect = lambda name: create_raw_study(
        id=name,
        name=name,
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / name),
        created_at=datetime.datetime.fromtimestamp(1480683452),
        updated_at=datetime.datetime.fromtimestamp(1602678639),
        version="700",
        storage_mode=StorageMode.FILESYSTEM,
    )
    repo.get_all.return_value = [md]

    variant_repo = Mock()
    variant_repo.get_children.return_value = []

    config = Config(
        resources_path=path_resources,
        security=SecurityConfig(disabled=True),
        cache=CacheConfig(),
        storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=path_studies)}),
    )

    task_service_mock = Mock(spec=ITaskService)
    user_service = Mock()
    # noinspection PyArgumentList
    user_service.get_user.return_value = User(id=0, name="test")

    job_result_repository = Mock()
    job_result_repository.find_by_study.return_value = []

    # Matrices
    matrix_path = tmp_path / "matrices"
    matrix_path.mkdir()
    matrix_content_repository = MatrixContentRepository(bucket_dir=matrix_path, format=InternalMatrixFormat.TSV)
    matrix_service = SimpleMatrixService(matrix_content_repository=matrix_content_repository)

    # Blob
    blob_path = tmp_path / "blob"
    blob_path.mkdir()
    blob_content_repository = BlobContentRepository(bucket_dir=blob_path)
    blob_service = BlobService(blob_content_repository=blob_content_repository)

    cache = LocalCache(config=config.cache)

    # Final object
    study_service, _ = build_study_service(
        config=config,
        cache=cache,
        file_transfer_manager=Mock(),
        task_service=task_service_mock,
        user_service=user_service,
        matrix_service=matrix_service,
        blob_service=blob_service,
        metadata_repository=repo,
        variant_repository=variant_repo,
        job_result_repository=job_result_repository,
    )

    output_service = build_output_service(
        study_service=study_service,
        config=config,
        cache=cache,
        event_bus=study_service.event_bus,
        task_service=task_service_mock,
        filetransfer_service=Mock(),
        matrix_service=matrix_service,
    )

    return study_service, output_service, config


@pytest.fixture
def storage_service(services: tuple[StudyService, OutputService, Config]) -> StudyService:
    return services[0]

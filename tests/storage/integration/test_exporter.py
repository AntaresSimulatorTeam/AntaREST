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

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import Mock

import py7zr
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.blobstore.service import BlobService
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import Config, SecurityConfig, StorageConfig, WorkspaceConfig
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.interfaces.eventbus import DummyEventBusService
from antarest.dependencies import AppState
from antarest.main import add_exception_handlers
from antarest.matrixstore.service import MatrixService
from antarest.output.output_blueprint import create_output_routes
from antarest.service_creator import build_output_service
from antarest.study.main import build_study_service
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.web.studies_blueprint import create_study_routes
from tests.helpers import create_raw_study, with_admin_user
from tests.storage.conftest import SimpleFileTransferManager, SimpleSyncTaskService
from tests.storage.integration.conftest import UUID


def assert_url_content(url: str, tmp_dir: Path, sta_mini_archive_path: Path) -> bytes:
    path_studies = tmp_dir / "studies"

    if sta_mini_archive_path.suffix == ".zip":
        with zipfile.ZipFile(sta_mini_archive_path) as zip_output:
            zip_output.extractall(path=path_studies)
    elif sta_mini_archive_path.suffix == ".7z":
        with py7zr.SevenZipFile(sta_mini_archive_path, "r") as szf:
            szf.extractall(path=path_studies / "STA-mini")
    else:
        raise ValueError(f"Unsupported archive format {sta_mini_archive_path.suffix}")

    cache = LocalCache()

    config = Config(
        resources_path=Path(),
        security=SecurityConfig(disabled=True),
        storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=path_studies)}),
    )

    md = create_raw_study(
        id=UUID,
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / "STA-mini"),
    )
    repo = Mock()
    repo.get.return_value = md

    ftm = SimpleFileTransferManager(Config(storage=StorageConfig(tmp_dir=tmp_dir)))
    task_service = SimpleSyncTaskService()
    matrix_service = Mock(spec=MatrixService)
    blob_service = Mock(spec=BlobService)
    study_service, _ = build_study_service(
        config,
        cache=cache,
        user_service=Mock(),
        task_service=task_service,
        file_transfer_manager=ftm,
        matrix_service=matrix_service,
        blob_service=blob_service,
        generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
        metadata_repository=repo,
    )

    output_service = build_output_service(
        study_service=study_service,
        cache=cache,
        task_service=task_service,
        matrix_service=matrix_service,
        event_bus=DummyEventBusService(),
        filetransfer_service=ftm,
        config=config,
    )

    services = Mock()
    services.study = study_service
    services.output_service = output_service
    services.file_transfer_manager = ftm
    services.task_service = task_service
    app = FastAPI(title=__name__)
    add_exception_handlers(app)
    app.state.app_state = AppState(config=config, services=services, ws_manager=Mock())
    app.include_router(create_study_routes())
    app.include_router(create_output_routes())

    # Simulate the download of data using a streamed request
    client = TestClient(app)
    if client.stream is False:
        # `TestClient` is based on `Requests` (old way before AntaREST-v2.15)
        # noinspection PyArgumentList
        res = client.get(url, stream=True)
        res.raise_for_status()
        result = res.json()
    else:
        # `TestClient` is based on `httpx` (new way since AntaREST-v2.15)
        data = io.BytesIO()
        # noinspection PyCallingNonCallable
        with client.stream("GET", url) as res:
            for chunk in res.iter_bytes():
                data.write(chunk)
        res.raise_for_status()
        result = json.loads(data.getvalue())

    download_task = FileDownloadTaskDTO(**result)
    download_filepath = ftm.fetch_download(download_task.file.id).path
    with open(download_filepath, "rb") as fh:
        return fh.read()


@with_admin_user
def test_exporter_file(tmp_path: Path, sta_mini_zip_path: Path, sta_mini_seven_zip_path: Path) -> None:
    # test with zip file
    data = assert_url_content(
        url=f"/v1/studies/{UUID}/export", tmp_dir=tmp_path, sta_mini_archive_path=sta_mini_zip_path
    )
    assert data and b"<!DOCTYPE HTML PUBLIC" not in data

    # test with 7zip file
    data = assert_url_content(
        url=f"/v1/studies/{UUID}/export", tmp_dir=tmp_path, sta_mini_archive_path=sta_mini_seven_zip_path
    )
    assert data and b"<!DOCTYPE HTML PUBLIC" not in data


@with_admin_user
def test_exporter_file_no_output(tmp_path: Path, sta_mini_zip_path: Path, sta_mini_seven_zip_path: Path) -> None:
    # test with zip file
    data = assert_url_content(
        url=f"/v1/studies/{UUID}/export?no-output", tmp_dir=tmp_path, sta_mini_archive_path=sta_mini_zip_path
    )
    assert data and b"<!DOCTYPE HTML PUBLIC" not in data

    # test with 7zip file
    data = assert_url_content(
        url=f"/v1/studies/{UUID}/export?no-output", tmp_dir=tmp_path, sta_mini_archive_path=sta_mini_seven_zip_path
    )
    assert data and b"<!DOCTYPE HTML PUBLIC" not in data

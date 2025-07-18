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

import io
import json
import zipfile
from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock

import py7zr
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.application import create_app_ctxt
from antarest.core.config import Config, SecurityConfig, StorageConfig, WorkspaceConfig
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.matrixstore.service import MatrixService
from antarest.study.main import build_study_service
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.storage.utils import export_study_flat
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
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

    build_ctxt = create_app_ctxt(FastAPI(title=__name__))
    ftm = SimpleFileTransferManager(Config(storage=StorageConfig(tmp_dir=tmp_dir)))
    build_study_service(
        build_ctxt,
        cache=Mock(),
        user_service=Mock(),
        task_service=SimpleSyncTaskService(),
        file_transfer_manager=ftm,
        matrix_service=Mock(spec=MatrixService),
        generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
        metadata_repository=repo,
        config=config,
    )

    # Simulate the download of data using a streamed request
    client = TestClient(build_ctxt.build())
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


@pytest.mark.parametrize("outputs", [True, False, "prout"])
@pytest.mark.parametrize("output_list", [None, [], ["20201014-1427eco"], ["20201014-1430adq-2"]])
@pytest.mark.parametrize("denormalize", [True, False])
def test_export_flat(
    tmp_path: Path,
    sta_mini_zip_path: Path,
    outputs: bool,
    output_list: Optional[List[str]],
    denormalize: bool,
) -> None:
    path_studies = tmp_path / "studies"
    path_studies.mkdir(exist_ok=True)

    export_path = tmp_path / "exports"
    export_path.mkdir()

    with zipfile.ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    export_study_flat(
        path_studies / "STA-mini",
        export_path / "STA-mini-export",
        Mock(),
        outputs,
        output_list,
        denormalize=denormalize,
    )

    export_output_path = export_path / "STA-mini-export" / "output"
    if outputs:
        assert export_output_path.exists()
        files = set(export_output_path.iterdir())
        if output_list is None:
            assert len(files) == 6
        elif len(output_list) == 0:
            assert not files
        else:
            expected = {export_output_path / item for item in output_list}
            assert files == expected
    else:
        assert not export_output_path.exists()

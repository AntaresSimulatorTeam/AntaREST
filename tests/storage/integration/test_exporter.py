import os
from pathlib import Path
from typing import Optional, List
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.config import (
    Config,
    SecurityConfig,
    StorageConfig,
    WorkspaceConfig,
)
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.matrixstore.service import MatrixService
from antarest.study.main import build_study_service
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.service import StudyService
from antarest.study.storage.utils import export_study_flat
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from tests.storage.conftest import (
    SimpleSyncTaskService,
    SimpleFileTransferManager,
)


def assert_url_content(
    url: str, tmp_dir: Path, sta_mini_zip_path: Path
) -> bytes:
    path_studies = tmp_dir / "studies"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    config = Config(
        resources_path=Path(),
        security=SecurityConfig(disabled=True),
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=path_studies)
            }
        ),
    )

    md = RawStudy(
        id="STA-mini",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(path_studies / "STA-mini"),
    )
    repo = Mock()
    repo.get.return_value = md

    app = FastAPI(title=__name__)
    ftm = SimpleFileTransferManager(
        Config(storage=StorageConfig(tmp_dir=tmp_dir))
    )
    build_study_service(
        app,
        cache=Mock(),
        user_service=Mock(),
        task_service=SimpleSyncTaskService(),
        file_transfer_manager=ftm,
        matrix_service=Mock(spec=MatrixService),
        generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
        metadata_repository=repo,
        config=config,
    )
    client = TestClient(app)
    res = client.get(url, stream=True)
    download_filepath = ftm.fetch_download(
        FileDownloadTaskDTO.parse_obj(res.json()).file.id,
        RequestParameters(user=DEFAULT_ADMIN_USER),
    ).path
    with open(download_filepath, "rb") as fh:
        return fh.read()


def assert_data(data: bytes):
    assert len(data) > 0 and b"<!DOCTYPE HTML PUBLIC" not in data


def test_exporter_file(tmp_path: Path, sta_mini_zip_path: Path):

    data = assert_url_content(
        url="/v1/studies/STA-mini/export",
        tmp_dir=tmp_path,
        sta_mini_zip_path=sta_mini_zip_path,
    )
    assert_data(data)


def test_exporter_file_no_output(tmp_path: Path, sta_mini_zip_path: Path):

    data = assert_url_content(
        url="/v1/studies/STA-mini/export?no-output",
        tmp_dir=tmp_path,
        sta_mini_zip_path=sta_mini_zip_path,
    )
    assert_data(data)


@pytest.mark.parametrize(
    "outputs,outputlist,denormalize",
    [
        (True, None, True),
        (True, [], False),
        (True, ["20201014-1427eco"], False),
        (False, ["20201014-1427eco"], False),
    ],
)
def test_export_flat(
    tmp_path: Path,
    sta_mini_zip_path: Path,
    outputs: bool,
    outputlist: Optional[List[str]],
    denormalize: bool,
):
    path_studies = tmp_path / "studies"
    path_studies.mkdir(exist_ok=True)

    export_path = tmp_path / "exports"
    export_path.mkdir()

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    export_study_flat(
        path_studies / "STA-mini",
        export_path / "STA-mini-export",
        Mock(),
        outputs,
        outputlist,
        denormalize=denormalize,
    )

    export_output_path = export_path / "STA-mini-export" / "output"
    if outputs:
        assert export_output_path.exists()
        if outputlist is not None:
            if len(outputlist) == 0:
                assert len(os.listdir(export_output_path)) == 0
            else:
                for item in outputlist:
                    assert (export_output_path / item).exists()
        else:
            assert len(os.listdir(export_output_path)) == 5
    else:
        assert not export_output_path.exists()

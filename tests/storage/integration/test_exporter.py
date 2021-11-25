from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

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

from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.common.config import (
    Config,
    SecurityConfig,
    StorageConfig,
    WorkspaceConfig,
)
from antarest.storage.model import Study, DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.storage.main import build_storage
from antarest.storage.service import StorageService


def assert_url_content(storage_service: StorageService, url: str) -> bytes:
    app = FastAPI(title=__name__)
    build_storage(
        app,
        user_service=Mock(),
        storage_service=storage_service,
        matrix_service=Mock(),
        config=storage_service.study_service.config,
    )
    client = TestClient(app)
    res = client.get(url, stream=True)
    return res.raw.data


def assert_data(data: bytes):
    assert len(data) > 0 and b"<!DOCTYPE HTML PUBLIC" not in data


def test_exporter_file(tmp_path: Path, sta_mini_zip_path: Path):

    path_studies = tmp_path / "studies"

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

    service = build_storage(
        application=Mock(),
        config=config,
        user_service=Mock(),
        matrix_service=Mock(),
        metadata_repository=repo,
    )

    data = assert_url_content(service, url="/studies/STA-mini/export")
    assert_data(data)


def test_exporter_file_no_output(tmp_path: Path, sta_mini_zip_path: Path):

    path_studies = tmp_path / "studies"

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

    service = build_storage(
        application=Mock(),
        config=config,
        user_service=Mock(),
        matrix_service=Mock(),
        metadata_repository=repo,
    )

    data = assert_url_content(
        service, url="/studies/STA-mini/export?no-output"
    )
    assert_data(data)

import json
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest import __version__
from antarest.common.config import (
    Config,
    SecurityConfig,
    StorageConfig,
    WorkspaceConfig,
)
from antarest.storage.main import build_storage
from antarest.storage.model import DEFAULT_WORKSPACE_NAME


CONFIG = Config(
    resources_path=Path(),
    security=SecurityConfig(disabled=True),
    storage=StorageConfig(
        workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=Path())}
    ),
)


@pytest.mark.unit_test
def test_version() -> None:

    mock_storage_service = Mock()
    mock_storage_service.study_service.path_resources = Path("/")

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=Config(),
        user_service=Mock(),
    )
    client = TestClient(app)

    path = "/version"
    result = client.get(path)

    assert result.status_code == HTTPStatus.OK.value
    assert result.json()["version"] == __version__


@pytest.mark.unit_test
def test_get_matrix() -> None:

    mock_storage_service = Mock()
    mock_storage_service.get_matrix.return_value = BytesIO(b"Hello World")

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
    )
    client = TestClient(app)

    path = "/v1/file/my-study/matrix.txt"
    result = client.get(path, stream=True)

    assert result.status_code == HTTPStatus.OK.value
    assert result.raw.data == b"Hello World"

import json
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock

import pytest
from flask import Flask

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

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(),
        user_service=Mock(),
    )
    client = app.test_client()

    path = "/version"
    result = client.get(path)

    assert result.status_code == HTTPStatus.OK.value
    assert json.loads(result.data)["version"] == __version__


@pytest.mark.unit_test
def test_get_matrix() -> None:

    mock_storage_service = Mock()
    mock_storage_service.get_matrix.return_value = b"Hello World"

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()

    path = "/file/my-study/matrix.txt"
    result = client.get(path)

    assert result.status_code == HTTPStatus.OK.value
    assert result.data == b"Hello World"
